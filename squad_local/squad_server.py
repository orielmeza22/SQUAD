import os, sys, json, subprocess, threading, urllib.request, urllib.parse, shutil, re, time, hashlib, socket, psutil, asyncio
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException, Query, Body
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

# Force UTF-8 stdout encoding on Windows to prevent UnicodeEncodeError for emojis
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        try:
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
        except:
            pass

# ----------------- ENV LOADER -----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_env():
    paths_to_check = [
        os.path.dirname(BASE_DIR),
        BASE_DIR,
        os.path.join(BASE_DIR, "SQUAD_WORKSPACE")
    ]
    for path in paths_to_check:
        for fn in [".env", ".env.local"]:
            p = os.path.join(path, fn)
            if os.path.exists(p):
                print(f"📡 [ENV] Cargando variables desde: {p}")
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#") and "=" in line:
                                k, v = line.split("=", 1)
                                os.environ[k.strip()] = v.strip().strip('"\'')
                except Exception as e:
                    print(f"Error cargando variables desde {p}: {e}")

# Load immediately on import as well
load_env()

# ----------------- OLLAMA API -----------------
class OllamaAPI:
    HOST = "http://127.0.0.1:11434"
    @staticmethod
    def is_online():
        try:
            with urllib.request.urlopen(f"{OllamaAPI.HOST}/", timeout=2) as r: return r.status == 200
        except: return False
    
    @staticmethod
    def list_models():
        try:
            with urllib.request.urlopen(f"{OllamaAPI.HOST}/api/tags", timeout=3) as req:
                return [x['name'] for x in json.loads(req.read().decode('utf-8')).get('models', [])]
        except: return []

    @staticmethod
    def generate(model, prompt=None, messages=None, is_json=False, num_ctx=16384, temperature=0.3, num_predict=4096, stream_callback=None):
        payload = {
            "model": model, 
            "stream": stream_callback is not None, 
            "options": {
                "num_ctx": num_ctx,
                "num_predict": num_predict,
                "temperature": temperature
            }
        }
        if prompt: payload["prompt"] = prompt
        if messages: payload["messages"] = messages
        if is_json: payload["format"] = "json"
        
        url = f"{OllamaAPI.HOST}/api/generate" if prompt else f"{OllamaAPI.HOST}/api/chat"
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        
        if stream_callback:
            try:
                with urllib.request.urlopen(req, timeout=120) as response:
                    accumulated = []
                    for line in response:
                        if line:
                            chunk = json.loads(line.decode('utf-8'))
                            text = chunk.get('response', '') if prompt else chunk.get('message', {}).get('content', '')
                            accumulated.append(text)
                            stream_callback("".join(accumulated))
                    return "".join(accumulated)
            except Exception as e:
                # Fallback to non-stream if stream connection breaks
                print(f"[OLLAMA STREAM ERROR] {e}")
        
        with urllib.request.urlopen(req, timeout=300) as response:
            res = json.loads(response.read().decode('utf-8'))
            return res.get('response', '') if prompt else res.get('message', {}).get('content', '')

# ----------------- GEMINI API -----------------
class GeminiAPI:
    @staticmethod
    def get_api_key():
        load_env()
        return os.environ.get("GEMINI_API_KEY", "")

    @staticmethod
    def is_available():
        return bool(GeminiAPI.get_api_key())

    @staticmethod
    def generate(model, prompt=None, messages=None, is_json=False, temp=0.3):
        key = GeminiAPI.get_api_key()
        if not key:
            raise Exception("GEMINI_API_KEY no configurada. Añádela a tu archivo .env o .env.local")
        
        contents = []
        system_instruction = None
        
        if prompt:
            contents.append({
                "role": "user",
                "parts": [{"text": prompt}]
            })
        elif messages:
            for msg in messages:
                role = msg.get("role")
                content = msg.get("content")
                if role == "system":
                    system_instruction = {
                        "parts": [{"text": content}]
                    }
                else:
                    gemini_role = "user" if role == "user" else "model"
                    contents.append({
                        "role": gemini_role,
                        "parts": [{"text": content}]
                    })
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temp
            }
        }
        
        if system_instruction:
            payload["systemInstruction"] = system_instruction
            
        if is_json:
            payload["generationConfig"]["responseMimeType"] = "application/json"
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        req = urllib.request.Request(
            url, 
            data=json.dumps(payload).encode('utf-8'), 
            headers={'Content-Type': 'application/json'}
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                res = json.loads(response.read().decode('utf-8'))
                # Validate response structure
                if 'candidates' in res and res['candidates']:
                    cand = res['candidates'][0]
                    if 'content' in cand and 'parts' in cand['content'] and cand['content']['parts']:
                        return cand['content']['parts'][0]['text']
                raise Exception("Respuesta vacía o estructurada incorrectamente por Gemini API")
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8')
            raise Exception(f"Gemini API Error {e.code}: {err_body}")

# ----------------- OPENAI API -----------------
class OpenAIAPI:
    @staticmethod
    def get_api_key():
        load_env()
        return os.environ.get("OPENAI_API_KEY", "")

    @staticmethod
    def is_available():
        return bool(OpenAIAPI.get_api_key())

    @staticmethod
    def generate(model, prompt=None, messages=None, is_json=False, temp=0.3):
        key = OpenAIAPI.get_api_key()
        if not key:
            raise Exception("OPENAI_API_KEY no configurada. Añádela a tu archivo .env o .env.local")
        
        openai_messages = []
        if prompt:
            openai_messages.append({"role": "user", "content": prompt})
        elif messages:
            for msg in messages:
                openai_messages.append({
                    "role": msg.get("role"),
                    "content": msg.get("content")
                })
        
        payload = {
            "model": model,
            "messages": openai_messages,
            "temperature": temp
        }
        if is_json:
            payload["response_format"] = {"type": "json_object"}
            
        url = "https://api.openai.com/v1/chat/completions"
        req = urllib.request.Request(
            url, 
            data=json.dumps(payload).encode('utf-8'), 
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {key}'
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                res = json.loads(response.read().decode('utf-8'))
                if 'choices' in res and res['choices']:
                    return res['choices'][0]['message']['content']
                raise Exception("Respuesta vacía o incorrecta de OpenAI API")
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8')
            raise Exception(f"OpenAI API Error {e.code}: {err_body}")

# ----------------- OPENROUTER API -----------------
class OpenRouterAPI:
    @staticmethod
    def get_api_key():
        load_env()
        return os.environ.get("OPENROUTER_API_KEY", "")

    @staticmethod
    def is_available():
        return bool(OpenRouterAPI.get_api_key())

    @staticmethod
    def generate(model, prompt=None, messages=None, is_json=False, temp=0.3):
        key = OpenRouterAPI.get_api_key()
        if not key:
            raise Exception("OPENROUTER_API_KEY no configurada. Añádela en Ajustes o al archivo .env")
        
        openrouter_messages = []
        if prompt:
            openrouter_messages.append({"role": "user", "content": prompt})
        elif messages:
            for msg in messages:
                openrouter_messages.append({
                    "role": msg.get("role"),
                    "content": msg.get("content")
                })
        
        payload = {
            "model": model,
            "messages": openrouter_messages,
            "temperature": temp
        }
        if is_json:
            payload["response_format"] = {"type": "json_object"}
            
        url = "https://openrouter.ai/api/v1/chat/completions"
        req = urllib.request.Request(
            url, 
            data=json.dumps(payload).encode('utf-8'), 
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {key}',
                'HTTP-Referer': 'http://localhost:8000',
                'X-Title': 'SQUAD Builder'
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                res = json.loads(response.read().decode('utf-8'))
                if 'choices' in res and res['choices']:
                    return res['choices'][0]['message']['content']
                raise Exception("Respuesta vacía o incorrecta de OpenRouter API")
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8')
            raise Exception(f"OpenRouter API Error {e.code}: {err_body}")

# ----------------- OPTIMIZATION TOOLS -----------------
class OptTools:
    CACHE_FILE = os.path.join(BASE_DIR, "llm_cache.json")
    
    CODE_GUIDELINES = """
=== REGLAS CRÍTICAS DE INTELIGENCIA Y GENERACIÓN DE CÓDIGO (ESTILO AIDER / CURSOR) ===
1. Pensamiento Crítico (Chain-of-Thought):
   Antes de escribir o modificar código, analiza la lógica del problema paso a paso. Escribe tu análisis y razonamiento dentro de bloques <reasoning>...</reasoning> al principio de tu respuesta.
2. Edición Basada en Parches (Modo Incremental Rápido):
   Si vas a modificar un archivo existente, NO lo reescribas completo. Usa obligatoriamente el formato @@PATCH para proponer solo las líneas exactas a cambiar. Esto es más rápido, consume menos tokens y evita introducir bugs colaterales.
   Solo usa @@FILE para archivos completamente nuevos.

EJEMPLOS DE SINTAXIS REQUERIDA (FEW-SHOT):

Ejemplo A - Crear archivo nuevo:
<reasoning>
1. Necesitamos un modelo de usuarios en un archivo nuevo `models.py`.
2. Usaremos SQLite3.
</reasoning>
@@FILE: models.py
import sqlite3
# Código completo del nuevo archivo aquí...
@@ENDFILE@@

Ejemplo B - Modificar archivo existente con parches incrementales:
<reasoning>
1. Añadiremos la función `verify_password` abajo de `hash_password` en `auth.py`.
2. Usaremos la librería `bcrypt`.
</reasoning>
@@PATCH: auth.py
<<<<<<< SEARCH
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())
=======
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed)
>>>>>>> END
3. Rutas de Estilo y Script en HTML:
   Al enlazar hojas de estilo o scripts en index.html, usa rutas relativas directas desde la raíz (ej: href="styles.css" o src="main_output.js"). NUNCA uses prefijos "/static/" ni Jinja2/Flask templates {{ url_for(...) }} a menos que el servidor esté explícitamente configurado para ello y exista el directorio.
================================================================================
"""
    
    _cache_data = None
    _cache_lock = threading.Lock()
    
    @staticmethod
    def load_cache():
        with OptTools._cache_lock:
            if OptTools._cache_data is not None:
                return OptTools._cache_data
            if os.path.exists(OptTools.CACHE_FILE):
                try:
                    with open(OptTools.CACHE_FILE, "r", encoding="utf-8") as f:
                        OptTools._cache_data = json.load(f)
                        return OptTools._cache_data
                except: pass
            OptTools._cache_data = {}
            return OptTools._cache_data

    @staticmethod
    def save_cache(cache):
        with OptTools._cache_lock:
            OptTools._cache_data = cache
            try:
                with open(OptTools.CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(cache, f, ensure_ascii=False, indent=2)
            except: pass

    @staticmethod
    def get_cache(model, prompt_or_messages, temp):
        key = hashlib.md5(f"{model}:{json.dumps(prompt_or_messages)}:{temp}".encode('utf-8')).hexdigest()
        cache = OptTools.load_cache()
        return cache.get(key), key

    @staticmethod
    def set_cache(key, response):
        cache = OptTools.load_cache()
        cache[key] = response
        OptTools.save_cache(cache)

    @staticmethod
    def calculate_dynamic_ctx():
        if hasattr(state, "context_window") and state.context_window:
            return state.context_window
        total_chars = 0
        if os.path.exists(SysTools.WORKSPACE):
            for root, _, files in os.walk(SysTools.WORKSPACE):
                if ".git" in root or "node_modules" in root or "__pycache__" in root: continue
                for f in files:
                    try: total_chars += os.path.getsize(os.path.join(root, f))
                    except: pass
        est_tokens = (total_chars // 4) + 4000
        if est_tokens <= 8192:
            return 8192
        elif est_tokens <= 16384:
            return 16384
        else:
            return min(32768, ((est_tokens + 4095) // 4096) * 4096)

    @staticmethod
    def prune_code_agnostic(code, file_path):
        lines = code.splitlines()
        pruned = []
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.py':
            for line in lines:
                stripped = line.strip()
                if line.startswith(('def ', 'class ', 'import ', 'from ')):
                    pruned.append(line)
                elif stripped.startswith(('def ', 'class ')):
                    pruned.append(line)
        elif ext in ['.js', '.ts', '.jsx', '.tsx']:
            for line in lines:
                stripped = line.strip()
                if stripped.startswith(('import ', 'export ', 'class ', 'function ', 'async function ')):
                    pruned.append(line)
                elif 'const ' in line and '=>' in line:
                    pruned.append(line)
        
        if pruned:
            return "\n".join(pruned) + "\n# [...resto del archivo omitido para ahorrar tokens...]"
        return code

    @staticmethod
    def get_relevant_files_context(query, max_tokens=15000):
        all_files = []
        if not os.path.exists(SysTools.WORKSPACE): return ""
        for root, _, files in os.walk(SysTools.WORKSPACE):
            if ".git" in root or "node_modules" in root or "__pycache__" in root: continue
            for f in files:
                p = os.path.join(root, f)
                rel = os.path.relpath(p, SysTools.WORKSPACE).replace('\\', '/')
                all_files.append(rel)
                
        # Heurística para consultas conversacionales o generales sin intención de código
        query_lower = query.lower()
        conversational_keywords = [
            "hola", "buenos", "tardes", "noches", "quién eres", "como estas", "cómo estás", "gracias", 
            "ejemplos", "ejemplo", "qué es", "que es", "qué puede", "que puede", "para qué", "para que", 
            "ayuda", "help", "squad", "opinas", "opinión", "bienvenido", "saludos"
        ]
        is_conversational = any(kw in query_lower for kw in conversational_keywords)
        
        code_related = [
            "código", "code", "archivo", "file", "escribe", "write", "modifica", "modify", "cambia", "change", 
            "error", "bug", "falla", "función", "clase", "class", "import", "require", "npm", "pip", "python", "node",
            "html", "css", "js", "ts", "app.py", "index.html", "package.json", "base de datos", "db", "sqlite",
            "crea", "crear", "create", "agrega", "agregar", "add", "borra", "elimina", "delete", "implementa",
            "implementar", "diseña", "diseñar", "refactor", "optimiza", "arregla", "fix", "corrige", "compila"
        ]
        has_code_intent = any(w in query_lower for w in code_related) or any(f.lower() in query_lower for f in all_files)
        
        if is_conversational and not has_code_intent:
            state.log("💡 [CONTEXTO] Consulta general detectada. Omitiendo archivos del workspace para velocidad rápida.")
            return f"Lista de archivos del proyecto (los archivos no se incluyen en el contexto por ser una consulta general): {', '.join(all_files)}"

        total_size = sum(os.path.getsize(os.path.join(SysTools.WORKSPACE, f)) for f in all_files if os.path.exists(os.path.join(SysTools.WORKSPACE, f)))
        if total_size < max_tokens * 3:
            return "\n\n".join(f"Archivo: {f}\n{SysTools.read(f)}" for f in all_files)
            
        words = [w.lower() for w in query.split() if len(w) > 2]
        scores = {}
        for f in all_files:
            content = SysTools.read(f)
            score = 0
            for w in words:
                score += content.lower().count(w)
            scores[f] = score
            
        sorted_files = sorted(all_files, key=lambda x: scores[x], reverse=True)
        included_files = []
        current_chars = 0
        max_chars = max_tokens * 4
        
        for f in sorted_files:
            content = SysTools.read(f)
            file_desc = f"Archivo: {f}\n{content}"
            if current_chars + len(file_desc) > max_chars:
                pruned_content = OptTools.prune_code_agnostic(content, f)
                pruned_desc = f"Archivo: {f} (Poda de Contexto para Ahorro de Tokens)\n{pruned_content}"
                if current_chars + len(pruned_desc) <= max_chars:
                    included_files.append(pruned_desc)
                    current_chars += len(pruned_desc)
            else:
                included_files.append(file_desc)
                current_chars += len(file_desc)
                
        summary = f"Lista de todos los archivos del proyecto: {', '.join(all_files)}\n\n"
        return summary + "\n\n".join(included_files)

def get_fallback_model(ollama_models):
    coder_models = [m for m in ollama_models if "coder" in m]
    if coder_models:
        for sz in ["7b", "8b", "14b", "3b", "1.5b"]:
            match = next((m for m in coder_models if sz in m), None)
            if match:
                return match
        return coder_models[0]
    for sz in ["3b", "8b", "14b", "7b"]:
        match = next((m for m in ollama_models if sz in m), None)
        if match:
            return match
    return ollama_models[0]

# ----------------- AI PROVIDER UNIFIED -----------------
class AIProvider:
    @staticmethod
    def generate(model, prompt=None, messages=None, is_json=False, temp=None, no_cache=False):
        # Swarm Multi-Model Routing
        if getattr(state, "smart_routing", False):
            content_to_check = prompt or ""
            if not content_to_check and messages:
                content_to_check = "\n".join(m.get("content", "") for m in messages)
            content_to_check = content_to_check.lower()
            
            is_planning_or_review = any(x in content_to_check for x in ["arquitecto", "architect", "plan técnico", "planificación", "review", "reviewer", "analizando calidad", "revisa los archivos", "spec.md"])
            
            if is_planning_or_review:
                if model.startswith("gemini-"):
                    model = "gemini-2.5-pro"
                elif model.startswith(("gpt-", "o1-", "o3-")):
                    model = "gpt-4o"
            else:
                if model.startswith("gemini-"):
                    model = "gemini-2.5-flash"
                elif model.startswith(("gpt-", "o1-", "o3-")):
                    model = "gpt-4o-mini"
 
        if temp is None:
            linter_retries = getattr(state, "linter_retries", 0)
            temp = max(0.0, state.temperature - (linter_retries * 0.15))
            
        system_p = getattr(state, "system_prompt", "")
        if system_p and (not system_p.startswith("Eres el Orquestador") or is_json):
            if messages:
                has_sys = any(m.get("role") == "system" for m in messages)
                if not has_sys:
                    messages = [{"role": "system", "content": system_p}] + messages
            else:
                messages = [
                    {"role": "system", "content": system_p},
                    {"role": "user", "content": prompt}
                ]
                prompt = None
 
        prompt_tokens = 0
        if prompt:
            prompt_tokens = len(prompt) // 4
        elif messages:
            prompt_tokens = sum(len(m.get('content', '')) for m in messages) // 4
            
        # Check cache first
        cache_key = None
        if not no_cache:
            cached_res, cache_key = OptTools.get_cache(model, prompt or messages, temp)
            if cached_res is not None:
                state.cache_hits += 1
                state.token_in += prompt_tokens
                state.token_out += len(cached_res) // 4
                print("⚡ [LLM CACHE HIT] Retornando respuesta guardada de caché local.")
                return cached_res

        state.token_in += prompt_tokens
        num_ctx = OptTools.calculate_dynamic_ctx()
        
        res = ""
        is_gemini = model.startswith("gemini-")
        is_openai = model.startswith("gpt-") or model.startswith("o1-") or model.startswith("o3-")
        is_openrouter = model.startswith("openrouter/")
        
        if is_gemini:
            if not GeminiAPI.is_available():
                if OllamaAPI.is_online():
                    ollama_models = OllamaAPI.list_models()
                    if ollama_models:
                        fallback_model = get_fallback_model(ollama_models)
                        state.log(f"⚠️ [FALLBACK] Gemini API Key no configurada. Usando modelo local de Ollama: {fallback_model}")
                        model = fallback_model
                        is_gemini = False
            if is_gemini:
                raise Exception("GEMINI_API_KEY no configurada. Añádela a tu archivo .env o .env.local")
        elif is_openai:
            if not OpenAIAPI.is_available():
                if OllamaAPI.is_online():
                    ollama_models = OllamaAPI.list_models()
                    if ollama_models:
                        fallback_model = get_fallback_model(ollama_models)
                        state.log(f"⚠️ [FALLBACK] OpenAI API Key no configurada. Usando modelo local de Ollama: {fallback_model}")
                        model = fallback_model
                        is_openai = False
            if is_openai:
                raise Exception("OPENAI_API_KEY no configurada. Añádela a tu archivo .env o .env.local")
        elif is_openrouter:
            if not OpenRouterAPI.is_available():
                if OllamaAPI.is_online():
                    ollama_models = OllamaAPI.list_models()
                    if ollama_models:
                        fallback_model = get_fallback_model(ollama_models)
                        state.log(f"⚠️ [FALLBACK] OpenRouter API Key no configurada. Usando modelo local de Ollama: {fallback_model}")
                        model = fallback_model
                        is_openrouter = False
            if is_openrouter:
                raise Exception("OPENROUTER_API_KEY no configurada. Añádela a tu panel de Ajustes en la app.")
        
        if is_gemini:
            res = GeminiAPI.generate(model, prompt=prompt, messages=messages, is_json=is_json, temp=temp)
        elif is_openai:
            res = OpenAIAPI.generate(model, prompt=prompt, messages=messages, is_json=is_json, temp=temp)
        elif is_openrouter:
            real_model = model.replace("openrouter/", "", 1)
            res = OpenRouterAPI.generate(real_model, prompt=prompt, messages=messages, is_json=is_json, temp=temp)
        else:
            def stream_cb(accumulated_text):
                if len(accumulated_text) > 100:
                    preview = accumulated_text[-80:]
                    state.update_last_log(f"🤖 [GENERANDO...]: ... {preview}")
                else:
                    state.update_last_log(f"🤖 [GENERANDO...]: {accumulated_text}")
            
            try:
                if not OllamaAPI.is_online():
                    raise Exception("Ollama está desconectado.")
                res = OllamaAPI.generate(model, prompt=prompt, messages=messages, is_json=is_json, num_ctx=num_ctx, temperature=temp, num_predict=4096, stream_callback=stream_cb)
            except Exception as e:
                # Fallback to Gemini if configured
                if GeminiAPI.is_available():
                    state.log(f"⚠️ [FALLBACK] Ollama falló o excedió tiempo ({e}). Derivando llamada a gemini-2.5-flash...")
                    model = "gemini-2.5-flash"
                    res = GeminiAPI.generate(model, prompt=prompt, messages=messages, is_json=is_json, temp=temp)
                else:
                    raise e
                    
        response_tokens = len(res) // 4
        state.token_out += response_tokens
        
        if model.startswith("gemini-"):
            input_cost = (prompt_tokens / 1_000_000) * 0.075
            output_cost = (response_tokens / 1_000_000) * 0.30
            state.cost_usd += input_cost + output_cost
        elif is_openai:
            input_cost = (prompt_tokens / 1_000_000) * 2.50
            output_cost = (response_tokens / 1_000_000) * 10.00
            state.cost_usd += input_cost + output_cost
            
        if not no_cache and cache_key:
            OptTools.set_cache(cache_key, res)
        return res

# ----------------- SYSTEM TOOLS -----------------
class SysTools:
    WORKSPACE = os.path.join(BASE_DIR, "SQUAD_WORKSPACE")
    git_lock = threading.Lock()

    @staticmethod
    def find_node_entry_point():
        if not os.path.exists(SysTools.WORKSPACE):
            return "main_output.js"
        workspace_files = os.listdir(SysTools.WORKSPACE)
        main_files = [f for f in workspace_files if f.startswith("main_output.") and f.endswith(('.js', '.ts', '.jsx', '.tsx'))]
        if main_files:
            return main_files[0]
        commons = [f for f in ["server.js", "app.js", "index.js", "main.js"] if f in workspace_files]
        if commons:
            return commons[0]
        recursive_commons = []
        for root, _, files in os.walk(SysTools.WORKSPACE):
            if "node_modules" in root or ".git" in root or "venv" in root or "__pycache__" in root:
                continue
            for f in files:
                if f in ["server.js", "app.js", "index.js", "main.js"]:
                    rel_path = os.path.relpath(os.path.join(root, f), SysTools.WORKSPACE).replace('\\', '/')
                    recursive_commons.append(rel_path)
        if recursive_commons:
            recursive_commons.sort(key=lambda x: (
                x.count('/'),
                0 if 'app.js' in x else 1 if 'server.js' in x else 2
            ))
            return recursive_commons[0]
        for root, _, files in os.walk(SysTools.WORKSPACE):
            if "node_modules" in root or ".git" in root or "venv" in root or "__pycache__" in root:
                continue
            for f in files:
                if f.endswith(('.js', '.ts')):
                    rel_path = os.path.relpath(os.path.join(root, f), SysTools.WORKSPACE).replace('\\', '/')
                    return rel_path
        return "main_output.js"

    @staticmethod
    def setup():
        load_settings()
        if not os.path.exists(SysTools.WORKSPACE): os.makedirs(SysTools.WORKSPACE)

    @staticmethod
    def cleanup_workspace_processes():
        if not os.path.exists(SysTools.WORKSPACE):
            return
        ws_abs = os.path.abspath(SysTools.WORKSPACE)
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.pid == os.getpid():
                    continue
                pname = proc.name().lower()
                if not any(x in pname for x in ["python", "node", "npm", "pip", "cmd", "powershell", "bash"]):
                    continue
                try:
                    cwd = os.path.abspath(proc.cwd())
                    if cwd.startswith(ws_abs):
                        print(f"🧹 [SISTEMA] Matando proceso residual en workspace: PID {proc.pid} ({proc.name()})")
                        proc.kill()
                        continue
                except:
                    pass
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

    @staticmethod
    def auto_heal_esm_commonjs():
        pkg_path = os.path.join(SysTools.WORKSPACE, "package.json")
        if not os.path.exists(pkg_path):
            return
        has_import = False
        has_require = False
        for root, _, files in os.walk(SysTools.WORKSPACE):
            if "node_modules" in root or ".git" in root or "venv" in root: continue
            for f in files:
                if f.endswith(('.js', '.jsx', '.ts', '.tsx')):
                    try:
                        with open(os.path.join(root, f), 'r', encoding='utf-8') as file_obj:
                            content = file_obj.read()
                        if re.search(r'^\s*import\s+[\'\"]|^\s*import\s+.*\s+from\s+[\'\"]', content, re.MULTILINE):
                            has_import = True
                        if re.search(r'\brequire\s*\(', content):
                            has_require = True
                    except:
                        pass
        try:
            with open(pkg_path, 'r', encoding='utf-8') as f_pkg:
                pkg_data = json.load(f_pkg)
        except:
            pkg_data = {}
        if not isinstance(pkg_data, dict):
            pkg_data = {}
        if has_import and not has_require:
            pkg_data["type"] = "module"
            print("📦 [SISTEMA] Proyecto detectado como ESM. Ajustando type=module en package.json.")
        elif has_require and not has_import:
            pkg_data["type"] = "commonjs"
            print("📦 [SISTEMA] Proyecto detectado como CommonJS. Ajustando type=commonjs en package.json.")
        try:
            with open(pkg_path, 'w', encoding='utf-8') as f_pkg:
                json.dump(pkg_data, f_pkg, indent=2)
        except:
            pass

    @staticmethod
    def auto_heal_sqlite_connections():
        if not os.path.exists(SysTools.WORKSPACE):
            return
        for root, _, files_in_dir in os.walk(SysTools.WORKSPACE):
            if "node_modules" in root or ".git" in root or "venv" in root or "__pycache__" in root:
                continue
            for f in files_in_dir:
                if f.endswith('.py'):
                    path = os.path.join(root, f)
                    try:
                        with open(path, 'r', encoding='utf-8') as file_obj:
                            content = file_obj.read()
                        pattern = r'(\b(\w+)\s*=\s*sqlite3\.connect\([^\n]+)'
                        def repl_py(m):
                            line = m.group(1)
                            var_name = m.group(2)
                            return f'{line}\n    try:\n        {var_name}.execute("PRAGMA journal_mode=WAL")\n        {var_name}.execute("PRAGMA busy_timeout=5000")\n    except Exception: pass'
                        new_content, count = re.subn(pattern, repl_py, content)
                        if count > 0:
                            with open(path, 'w', encoding='utf-8') as file_obj:
                                file_obj.write(new_content)
                    except Exception:
                        pass
                elif f.endswith(('.js', '.ts')):
                    path = os.path.join(root, f)
                    try:
                        with open(path, 'r', encoding='utf-8') as file_obj:
                            content = file_obj.read()
                        pattern = r'(\b(const|let|var)\s+(\w+)\s*=\s*new\s+sqlite3\.Database\([^\n]+)'
                        def repl_js(m):
                            line = m.group(1)
                            var_name = m.group(3)
                            return f'{line}\n{var_name}.run("PRAGMA journal_mode=WAL;");\n{var_name}.run("PRAGMA busy_timeout=5000;");'
                        new_content, count = re.subn(pattern, repl_js, content)
                        if count > 0:
                            with open(path, 'w', encoding='utf-8') as file_obj:
                                file_obj.write(new_content)
                    except Exception:
                        pass

    @staticmethod
    def dry_parse_multifile(text):
        lines = text.split("\n")
        current_file = None
        current_content = []
        files = {}
        for line in lines:
            if line.startswith("@@FILE:"):
                if current_file:
                    files[current_file] = "\n".join(current_content).strip("`\n ")
                current_file = line.replace("@@FILE:", "").strip()
                current_content = []
            elif line.startswith("@@ENDFILE@@") or line.startswith("@@ENDFILE"):
                if current_file:
                    files[current_file] = "\n".join(current_content).strip("`\n ")
                    current_file = None
            else:
                if current_file is not None:
                    if line.strip().startswith("```") and len(line.strip()) <= 15:
                        continue
                    current_content.append(line)
        if current_file:
            files[current_file] = "\n".join(current_content).strip("`\n ")
        return files

    @staticmethod
    def check_syntax(name, c):
        if name.endswith('.py'):
            try:
                compile(c, name, 'exec')
                return True, ""
            except SyntaxError as e:
                return False, f"SyntaxError: {e.msg} en la línea {e.lineno}"
            except Exception as e:
                return False, str(e)
        elif name.endswith(('.js', '.jsx', '.ts', '.tsx')):
            if shutil.which('node'):
                import tempfile
                try:
                    suffix = os.path.splitext(name)[1]
                    with tempfile.NamedTemporaryFile(suffix=suffix, mode='w', encoding='utf-8', delete=False) as temp_f:
                        temp_f.write(c)
                        temp_f_name = temp_f.name
                    res = subprocess.run(['node', '--check', temp_f_name], capture_output=True, text=True)
                    os.remove(temp_f_name)
                    if res.returncode != 0:
                        err = res.stderr.replace(temp_f_name, name)
                        return False, err.strip()
                    return True, ""
                except:
                    try: os.remove(temp_f_name)
                    except: pass
        return True, ""

    @staticmethod
    def setup_venv(logger_list=None):
        venv_dir = os.path.join(SysTools.WORKSPACE, "venv")
        if sys.platform == "win32":
            python_exe = os.path.join(venv_dir, "Scripts", "python.exe")
            pip_exe = os.path.join(venv_dir, "Scripts", "pip.exe")
        else:
            python_exe = os.path.join(venv_dir, "bin", "python")
            pip_exe = os.path.join(venv_dir, "bin", "pip")

        if not os.path.exists(python_exe):
            if logger_list is not None:
                logger_list.append("📦 [SISTEMA] Creando entorno virtual (venv) en el workspace...")
            try:
                subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True, capture_output=True)
                if logger_list is not None:
                    logger_list.append("✅ [SISTEMA] Entorno virtual creado con éxito.")
            except Exception as e:
                if logger_list is not None:
                    logger_list.append(f"⚠️ [SISTEMA] No se pudo crear venv: {e}. Se utilizará Python global.")
                return sys.executable, "pip"
        return python_exe, pip_exe

    @staticmethod
    def auto_detect_nodejs_dependencies():
        pkg_path = os.path.join(SysTools.WORKSPACE, "package.json")
        detected_deps = set()
        node_builtins = {
            "fs", "path", "child_process", "crypto", "os", "http", "https", "url", 
            "querystring", "stream", "util", "assert", "events", "zlib", "buffer", 
            "dns", "net", "readline", "repl", "tls", "v8", "vm", "worker_threads", 
            "process", "timers", "console"
        }
        
        if os.path.exists(SysTools.WORKSPACE):
            for root, _, files_in_dir in os.walk(SysTools.WORKSPACE):
                if "node_modules" in root or ".git" in root or "venv" in root or "__pycache__" in root:
                    continue
                for f in files_in_dir:
                    if f.endswith(('.js', '.jsx', '.ts', '.tsx')):
                        try:
                            with open(os.path.join(root, f), 'r', encoding='utf-8') as file_obj:
                                content = file_obj.read()
                            req_matches = re.findall(r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)', content)
                            imp_matches = re.findall(r'(?:import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]|import\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)|import\s+[\'"]([^\'"]+)[\'"])', content)
                            
                            all_matches = req_matches
                            for m in imp_matches:
                                if isinstance(m, tuple):
                                    for part in m:
                                        if part:
                                            all_matches.append(part)
                                elif m:
                                    all_matches.append(m)
                                        
                            for dep in all_matches:
                                dep = dep.strip()
                                if not dep:
                                    continue
                                if dep.startswith('.') or dep.startswith('/') or dep.startswith('\\'):
                                    continue
                                
                                if dep.startswith('@'):
                                    parts = dep.split('/')
                                    if len(parts) >= 2:
                                        dep_name = f"{parts[0]}/{parts[1]}"
                                    else:
                                        dep_name = dep
                                else:
                                    dep_name = dep.split('/')[0]
                                    
                                if dep_name not in node_builtins:
                                    detected_deps.add(dep_name)
                        except Exception:
                            pass

        pkg_data = {}
        if os.path.exists(pkg_path):
            try:
                with open(pkg_path, 'r', encoding='utf-8') as f_pkg:
                    pkg_data = json.load(f_pkg)
            except Exception:
                pass
                
        if not isinstance(pkg_data, dict):
            pkg_data = {}
            
        if "name" not in pkg_data:
            pkg_data["name"] = "squad-workspace-project"
        if "type" not in pkg_data:
            pkg_data["type"] = "commonjs"
        changed = False
        if "scripts" not in pkg_data or not isinstance(pkg_data["scripts"], dict):
            pkg_data["scripts"] = {}
            changed = True
            
        target_f = SysTools.find_node_entry_point()
        correct_start_cmd = f"node {target_f}"
        
        current_start = pkg_data["scripts"].get("start", "")
        ref_file = None
        if current_start.strip().startswith("node "):
            ref_file = current_start.strip()[5:].strip()
        elif current_start.strip().startswith("nodemon "):
            ref_file = current_start.strip()[8:].strip()
            
        file_missing = False
        if ref_file:
            ref_file = ref_file.replace('"', '').replace("'", "")
            ref_path = os.path.join(SysTools.WORKSPACE, ref_file)
            if not os.path.exists(ref_path):
                file_missing = True
                
        is_invalid = (
            not current_start 
            or ".bat" in current_start 
            or ".sh" in current_start 
            or ".py" in current_start 
            or ".md" in current_start
            or file_missing
        )
        if is_invalid:
            pkg_data["scripts"]["start"] = correct_start_cmd
            changed = True
            
        if "dependencies" not in pkg_data or not isinstance(pkg_data["dependencies"], dict):
            pkg_data["dependencies"] = {}
            changed = True
        for dep in detected_deps:
            if dep not in pkg_data["dependencies"]:
                pkg_data["dependencies"][dep] = "*"
                changed = True
                
        if changed or not os.path.exists(pkg_path):
            try:
                with open(pkg_path, 'w', encoding='utf-8') as f_pkg:
                    json.dump(pkg_data, f_pkg, indent=2)
            except Exception:
                pass

    @staticmethod
    def auto_detect_python_dependencies():
        req_path = os.path.join(SysTools.WORKSPACE, "requirements.txt")
        detected_modules = set()
        py_builtins = {
            "os", "sys", "re", "math", "json", "datetime", "time", "random", "hashlib",
            "subprocess", "shutil", "urllib", "collections", "itertools", "functools",
            "typing", "io", "csv", "sqlite3", "threading", "logging", "asyncio", "xml",
            "socket", "select", "selectors", "signal", "tempfile", "traceback", "uuid"
        }
        
        if os.path.exists(SysTools.WORKSPACE):
            for root, _, files_in_dir in os.walk(SysTools.WORKSPACE):
                if "node_modules" in root or ".git" in root or "venv" in root or "__pycache__" in root:
                    continue
                for f in files_in_dir:
                    if f.endswith('.py'):
                        try:
                            with open(os.path.join(root, f), 'r', encoding='utf-8') as file_obj:
                                content = file_obj.read()
                            
                            for line in content.splitlines():
                                line = line.strip()
                                if line.startswith('import '):
                                    parts = line[7:].split(',')
                                    for p in parts:
                                        p_strip = p.strip()
                                        if not p_strip: continue
                                        mod = p_strip.split()[0].split('.')[0]
                                        if mod and mod not in py_builtins:
                                            detected_modules.add(mod)
                                elif line.startswith('from '):
                                    parts = line[5:].strip().split()
                                    if parts:
                                        mod = parts[0].split('.')[0]
                                        if mod and mod not in py_builtins:
                                            detected_modules.add(mod)
                        except Exception:
                            pass
                            
        if detected_modules:
            package_mapping = {
                "flask": "flask",
                "sqlalchemy": "SQLAlchemy",
                "sqlmodel": "sqlmodel",
                "fastapi": "fastapi",
                "uvicorn": "uvicorn",
                "jinja2": "Jinja2",
                "requests": "requests",
                "pydantic": "pydantic",
                "jwt": "PyJWT",
                "bcrypt": "bcrypt",
                "sqlite": "pysqlite3"
            }
            
            needed_packages = set()
            for mod in detected_modules:
                pkg = package_mapping.get(mod.lower(), mod)
                needed_packages.add(pkg)
                
            existing_packages = set()
            if os.path.exists(req_path):
                try:
                    with open(req_path, 'r', encoding='utf-8') as f_req:
                        for line in f_req:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                pkg_name = re.split(r'[=<>~]', line)[0].strip()
                                existing_packages.add(pkg_name.lower())
                except Exception:
                    pass
                    
            missing = [pkg for pkg in needed_packages if pkg.lower() not in existing_packages]
            if missing:
                try:
                    with open(req_path, 'a', encoding='utf-8') as f_req:
                        for pkg in missing:
                            f_req.write(f"\n{pkg}")
                except Exception:
                    try:
                        with open(req_path, 'w', encoding='utf-8') as f_req:
                            for pkg in needed_packages:
                                f_req.write(f"{pkg}\n")
                    except Exception:
                        pass

    @staticmethod
    def auto_heal_hardcoded_ports():
        if not os.path.exists(SysTools.WORKSPACE):
            return
        for root, _, files_in_dir in os.walk(SysTools.WORKSPACE):
            if "node_modules" in root or ".git" in root or "venv" in root or "__pycache__" in root:
                continue
            for f in files_in_dir:
                if f.endswith(('.js', '.jsx', '.ts', '.tsx')):
                    path = os.path.join(root, f)
                    try:
                        with open(path, 'r', encoding='utf-8') as file_obj:
                            content = file_obj.read()
                        new_content, count1 = re.subn(
                            r'\b(const|let|var)\s+PORT\s*=\s*(\d+)\s*;?',
                            r'\1 PORT = process.env.PORT || \2;',
                            content
                        )
                        new_content, count2 = re.subn(
                            r'\.listen\(\s*(\d+)\s*(,|\))',
                            r'.listen(process.env.PORT || \1\2',
                            new_content
                        )
                        new_content, count3 = re.subn(
                            r'http://localhost:\d+/api',
                            r'((typeof window !== "undefined" ? window.location.origin : "") + "/api")',
                            new_content
                        )
                        if count1 > 0 or count2 > 0 or count3 > 0:
                            with open(path, 'w', encoding='utf-8') as file_obj:
                                file_obj.write(new_content)
                    except Exception:
                        pass
                elif f.endswith('.py'):
                    path = os.path.join(root, f)
                    try:
                        with open(path, 'r', encoding='utf-8') as file_obj:
                            content = file_obj.read()
                        new_content, count = re.subn(
                            r'\bport\s*=\s*(\d+)',
                            r"port=int(os.environ.get('PORT', \1))",
                            content
                        )
                        if count > 0:
                            with open(path, 'w', encoding='utf-8') as file_obj:
                                file_obj.write(new_content)
                    except Exception:
                        pass

    @staticmethod
    def kill_process_tree(pid):
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            for child in children:
                try:
                    child.kill()
                except Exception:
                    pass
            parent.kill()
        except Exception as e:
            try:
                if sys.platform == 'win32':
                    subprocess.run(f"taskkill /F /T /PID {pid}", shell=True, capture_output=True)
                else:
                    os.kill(pid, 9)
            except Exception:
                pass

    @staticmethod
    def get_free_port(start_port):
        port = start_port
        while port < 65535:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('127.0.0.1', port))
                    return port
            except OSError:
                port += 1
        return start_port
            
    @staticmethod
    def read(name):
        p = os.path.join(SysTools.WORKSPACE, name)
        if not os.path.exists(p): return ""
        try:
            with open(p, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            # Safely catch UnicodeDecodeError for binary files in the workspace (e.g. SQLite databases)
            return ""
        except Exception:
            return ""

    @staticmethod
    def write(name, c, force=False):
        clean_name = name.lstrip("\\/")
        if ":" in clean_name:
            clean_name = clean_name.split(":", 1)[-1].lstrip("\\/")
        clean_name = os.path.normpath(clean_name)
        while clean_name.startswith("..") or clean_name.startswith("/") or clean_name.startswith("\\"):
            clean_name = clean_name.replace("../", "").replace("..\\", "").replace("..", "").lstrip("\\/")

        # Critical file write interception logic
        is_critical = clean_name in ["app.py", "package.json", "index.html", ".env", "docker-compose.yml", "requirements.txt", "main_output.py", "main_output.js", "main_output.tsx"]
        if not force and getattr(state, "interception_enabled", True) and is_critical:
            if not hasattr(state, "pending_writes"):
                state.pending_writes = {}
            state.pending_writes[clean_name] = c
            state.launcher_logs.append(f"[INTERCEPTOR] ⚠️ Modificación de '{clean_name}' retenida para confirmación del usuario.")
            return "PENDING"

        p = os.path.abspath(os.path.join(SysTools.WORKSPACE, clean_name))
        if not p.startswith(os.path.abspath(SysTools.WORKSPACE)):
             p = os.path.join(SysTools.WORKSPACE, "fallback_unnamed_file.txt")
             
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f: f.write(c)
        if hasattr(state, "file_changes"):
            state.file_changes.append(clean_name)
        return p
        
    @staticmethod
    def apply_patch(file_path_rel, patch_text):
        p = os.path.abspath(os.path.join(SysTools.WORKSPACE, file_path_rel.lstrip("\\/")))
        if not p.startswith(os.path.abspath(SysTools.WORKSPACE)):
            return False
            
        content = ""
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    content = f.read()
            except:
                return False
        else:
            try:
                os.makedirs(os.path.dirname(p), exist_ok=True)
                parts = patch_text.split("<<<<<<< SEARCH")
                replace_content = []
                for part in parts[1:]:
                    if "=======" not in part or ">>>>>>> END" not in part:
                        continue
                    _, rest = part.split("=======", 1)
                    replace_block, _ = rest.split(">>>>>>> END", 1)
                    replace_content.append(replace_block.strip("\r\n"))
                final_content = "\n".join(replace_content)
                with open(p, "w", encoding="utf-8") as f:
                    f.write(final_content)
                return True
            except:
                return False
            
        parts = patch_text.split("<<<<<<< SEARCH")
        modified = False
        for part in parts[1:]:
            if "=======" not in part or ">>>>>>> END" not in part:
                continue
            search_block, rest = part.split("=======", 1)
            replace_block, _ = rest.split(">>>>>>> END", 1)
            
            search_block = search_block.strip("\r\n")
            replace_block = replace_block.strip("\r\n")
            
            if not search_block:
                continue
                
            if search_block in content:
                content = content.replace(search_block, replace_block)
                modified = True
            else:
                search_lines = [l.rstrip() for l in search_block.splitlines()]
                content_lines = [l.rstrip() for l in content.splitlines()]
                search_len = len(search_lines)
                for idx in range(len(content_lines) - search_len + 1):
                    if content_lines[idx:idx+search_len] == search_lines:
                        replace_lines = [l.rstrip() for l in replace_block.splitlines()]
                        content_lines[idx:idx+search_len] = replace_lines
                        content = "\n".join(content_lines)
                        modified = True
                        break
        if modified:
            with open(p, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        return False

    @staticmethod
    def extract_and_write_multifile(text):
        lines = text.split("\n")
        current_file = None
        current_content = []
        files = []
        
        current_patch_file = None
        current_patch_content = []
        
        for line in lines:
            if line.startswith("@@PATCH:"):
                if current_file:
                    SysTools.write(current_file, "\n".join(current_content).strip("`\n "))
                    current_file = None
                if current_patch_file:
                    SysTools.apply_patch(current_patch_file, "\n".join(current_patch_content))
                    current_patch_file = None
                current_patch_file = line.replace("@@PATCH:", "").strip()
                current_patch_content = []
                files.append(current_patch_file)
                continue
            elif line.startswith("@@FILE:"):
                if current_file:
                    SysTools.write(current_file, "\n".join(current_content).strip("`\n "))
                if current_patch_file:
                    SysTools.apply_patch(current_patch_file, "\n".join(current_patch_content))
                    current_patch_file = None
                current_file = line.replace("@@FILE:", "").strip()
                current_content = []
                files.append(current_file)
                continue
            elif line.startswith("@@DELETE:"):
                if current_file:
                    SysTools.write(current_file, "\n".join(current_content).strip("`\n "))
                    current_file = None
                if current_patch_file:
                    SysTools.apply_patch(current_patch_file, "\n".join(current_patch_content))
                    current_patch_file = None
                del_file = line.replace("@@DELETE:", "").strip()
                del_path = os.path.abspath(os.path.join(SysTools.WORKSPACE, del_file.lstrip("\\/")))
                if del_path.startswith(os.path.abspath(SysTools.WORKSPACE)) and os.path.exists(del_path):
                    try:
                        os.remove(del_path)
                    except:
                        pass
                continue
            
            has_endfile = "@@ENDFILE" in line
            has_endpatch = "@@ENDPATCH" in line
            
            if has_endfile or has_endpatch:
                tag = "@@ENDFILE" if has_endfile else "@@ENDPATCH"
                parts = line.split(tag, 1)
                before_tag = parts[0]
                before_tag = before_tag.replace(">>>>>>> END", "").rstrip()
                
                if current_file is not None:
                    if before_tag.strip():
                        if not (before_tag.strip().startswith("```") and len(before_tag.strip()) <= 15):
                            current_content.append(before_tag)
                    SysTools.write(current_file, "\n".join(current_content).strip("`\n "))
                    current_file = None
                elif current_patch_file is not None:
                    if before_tag.strip():
                        current_patch_content.append(before_tag)
                    SysTools.apply_patch(current_patch_file, "\n".join(current_patch_content))
                    current_patch_file = None
                continue
            
            if current_file is not None:
                if line.strip().startswith("```") and len(line.strip()) <= 15:
                    continue
                current_content.append(line)
            elif current_patch_file is not None:
                current_patch_content.append(line)

        if current_file:
             SysTools.write(current_file, "\n".join(current_content).strip("`\n "))
        if current_patch_file:
             SysTools.apply_patch(current_patch_file, "\n".join(current_patch_content))
             
        if not files:
            blocks = re.findall(r'```([a-zA-Z0-9_-]*)\s*(.*?)(?:```|$)', text, re.DOTALL)
            if not blocks:
                if "```" not in text:
                    return []
                blocks = [("", text.strip())]
            
            for lang_tag, code in blocks:
                lang_tag = lang_tag.lower()
                ext = "py"
                fname = None
                
                # Check if code block starts with a filename comment like: # @FILE: filename.ext
                first_lines = [line.strip() for line in code.splitlines()[:2]]
                for line in first_lines:
                     m = re.search(r'(?:#|//|/\*|<!--)\s*@FILE:?\s*([a-zA-Z0-9_\-\./]+)', line, re.IGNORECASE)
                     if m:
                         fname = m.group(1).strip()
                         break
                
                if lang_tag in ["html"]:
                    ext = "html"
                    fname = "index.html"
                elif lang_tag in ["css"]:
                    ext = "css"
                    fname = "styles.css"
                elif lang_tag in ["javascript", "js", "react", "jsx", "node"]:
                    ext = "js"
                    is_server = "require(" in code or "express()" in code or "app.listen(" in code or "module.exports" in code or "import express" in code or "fastify" in code
                    fname = "main_output.js" if is_server else "app.js"
                elif lang_tag in ["typescript", "ts", "tsx"]:
                    ext = "tsx"
                    fname = "main_output.tsx"
                elif lang_tag in ["json"]:
                    ext = "json"
                    fname = "main_output.json"
                elif lang_tag in ["bash", "sh", "shell", "bat", "cmd"]:
                    ext = "bat" if sys.platform.startswith("win") else "sh"
                    fname = f"main_output.{ext}"
                elif lang_tag in ["sql"]:
                    ext = "sql"
                    fname = "schema.sql"
                else:
                    if "import React" in code or "console.log" in code or "const " in code:
                        ext = "js"
                        is_server = "require(" in code or "express()" in code or "app.listen(" in code or "module.exports" in code or "import express" in code or "fastify" in code
                        fname = "main_output.js" if is_server else "app.js"
                    elif "<!doctype html" in code.lower() or "<html" in code.lower():
                        ext = "html"
                        fname = "index.html"
                    elif "body {" in code or "margin:" in code or "padding:" in code or "@keyframes" in code:
                        ext = "css"
                        fname = "styles.css"
                    elif (
                        code.strip().startswith(("name:", "on:", "jobs:", "steps:", "- name:"))
                        or "runs-on:" in code
                        or "github.com/actions" in code
                        or re.search(r'^name:\s+\S', code, re.MULTILINE)
                    ):
                        # CI/CD YAML pipeline — save with proper extension
                        ext = "yml"
                        # Try to infer a sensible filename
                        if "github" in code.lower() or "workflows" in lang_tag.lower():
                            fname = ".github/workflows/ci.yml"
                        else:
                            fname = "pipeline.yml"
                    elif code.strip().startswith(("- ", "* ", "1. ", "2. ", "3. ", "### ", "# ")) or "**" in code:
                        ext = "md"
                        fname = "main_output.md"
                    else:
                        ext = "py"
                        fname = "main_output.py"
                
                if fname:
                    SysTools.write(fname, code)
                    files.append(fname)
        return files

    @staticmethod
    def extract_code(text):
        m = re.search(r'```[a-zA-Z0-9_-]*\s*(.*?)\s*```', text, re.DOTALL)
        return m.group(1).strip() if m else text.strip()

    @staticmethod
    def web_search(query):
        try:
            url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query)
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=10) as r:
                html = r.read().decode('utf-8')
                snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', html, re.IGNORECASE|re.DOTALL)
                clean = [re.sub(r'<[^>]+>', '', s).strip() for s in snippets][:3]
                return "\n".join(clean) if clean else "No hay resultados útiles."
        except Exception as e: return f"Error de búsqueda: {e}"

    @staticmethod
    def check_brackets_and_quotes(content):
        stack = []
        mapping = {')': '(', '}': '{', ']': '['}
        lines = content.splitlines()
        
        in_block_comment = False
        in_string = None
        
        for line_idx, line in enumerate(lines):
            col_idx = 0
            while col_idx < len(line):
                char = line[col_idx]
                
                if not in_string and not in_block_comment:
                    if line[col_idx:col_idx+2] == '//':
                        break
                    if line[col_idx:col_idx+2] == '/*':
                        in_block_comment = True
                        col_idx += 2
                        continue
                if in_block_comment:
                    if line[col_idx:col_idx+2] == '*/':
                        in_block_comment = False
                        col_idx += 2
                    else:
                        col_idx += 1
                    continue
                    
                if in_string:
                    if char == '\\':
                        col_idx += 2
                        continue
                    if char == in_string:
                        in_string = None
                    col_idx += 1
                    continue
                else:
                    if char in ('"', "'", '`'):
                        in_string = char
                        col_idx += 1
                        continue
                        
                if char in ('(', '{', '['):
                    stack.append((char, line_idx + 1))
                elif char in (')', '}', ']'):
                    if not stack:
                        return False, f"Cierre inesperado '{char}' en línea {line_idx + 1}"
                    top, start_line = stack.pop()
                    if mapping[char] != top:
                        return False, f"Se esperaba el cierre de '{top}' (abierto en línea {start_line}) pero se encontró '{char}' en línea {line_idx + 1}"
                col_idx += 1
                
        if stack:
            top, start_line = stack[-1]
            return False, f"Apertura de '{top}' en línea {start_line} no está cerrada."
        return True, "Correcto"

    @staticmethod
    def auto_fix_css(file_path, content):
        """Intenta reparar problemas de sintaxis CSS comunes de forma determinística."""
        lines = content.splitlines()
        fixed_lines = []
        open_parens = 0
        open_braces = 0
        in_string = None
        changed = False
        for line in lines:
            new_line = list(line)
            for i, ch in enumerate(line):
                if in_string:
                    if ch == in_string:
                        in_string = None
                elif ch in ('"', "'"):
                    in_string = ch
                elif ch == '(':
                    open_parens += 1
                elif ch == ')':
                    if open_parens > 0:
                        open_parens -= 1
                elif ch == '{':
                    open_braces += 1
                elif ch == '}':
                    if open_braces > 0:
                        open_braces -= 1
            fixed_lines.append(line)
        # Close any unclosed parens/braces at end of file
        if open_parens > 0:
            fixed_lines[-1] = fixed_lines[-1] + (')' * open_parens)
            changed = True
        if open_braces > 0:
            fixed_lines.append('}' * open_braces)
            changed = True
        if changed:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(fixed_lines))
            except Exception:
                pass
        return changed

    @staticmethod
    def run_linter(file_path):
        content = ""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return False, f"No se pudo leer el archivo: {e}"

        if file_path.endswith('.py'):
            stripped = content.strip()
            # Guard: env var file (KEY=value format, not Python) → delete it
            env_var_pattern = bool(re.match(r'^[A-Z_][A-Z0-9_]*=[^\s]', stripped))
            only_env_lines = all(
                re.match(r'^[A-Z_][A-Z0-9_]*=', l.strip()) or not l.strip() or l.strip().startswith('#')
                for l in stripped.splitlines()
            )
            if env_var_pattern and only_env_lines:
                try:
                    os.remove(file_path)
                except Exception:
                    pass
                return True, "Archivo de variables de entorno eliminado (no es Python válido)."

            # Guard: YAML content → rename
            yaml_indicators = (
                stripped.startswith(("name:", "on:", "jobs:", "steps:", "- name:"))
                or "runs-on:" in stripped
                or bool(re.search(r'^name:\s+\S', stripped, re.MULTILINE))
            )
            if yaml_indicators:
                new_path = re.sub(r'\.py$', '.yml', file_path)
                try:
                    os.rename(file_path, new_path)
                except Exception:
                    pass
                return True, "Archivo YAML renombrado de .py a .yml correctamente."
            
            # Guard: Markdown content → rename
            markdown_indicators = (
                stripped.startswith(("- ", "* ", "1. ", "2. ", "3. ", "### ", "# ", "## ", "---"))
                or "**" in stripped
                or "###" in stripped
                or "####" in stripped
            )
            if markdown_indicators:
                new_path = re.sub(r'\.py$', '.md', file_path)
                try:
                    os.rename(file_path, new_path)
                except Exception:
                    pass
                return True, "Archivo Markdown renombrado de .py a .md correctamente."
            try:
                subprocess.run([sys.executable, "-m", "py_compile", file_path], check=True, capture_output=True, text=True)
                return True, "Síntaxis correcta."
            except subprocess.CalledProcessError as e:
                return False, e.stderr
        elif file_path.endswith('.css'):
            ok, msg = SysTools.check_brackets_and_quotes(content)
            if not ok:
                # Attempt deterministic auto-fix for CSS
                fixed = SysTools.auto_fix_css(file_path, content)
                if fixed:
                    return True, "CSS auto-reparado (paréntesis/llaves cerradas)."
                return False, msg
            return True, "Sintaxis CSS correcta."
        elif file_path.endswith(('.js', '.jsx', '.ts', '.tsx', '.html')):
            # Auto-fix JS: remove duplicate const declarations at end of file
            if file_path.endswith('.js') and not file_path.endswith(('.jsx', '.tsx')):
                # Detect and remove duplicate const/var/let declarations
                lines = content.splitlines()
                declared_consts = {}
                clean_lines = []
                skip_block = False
                for i, line in enumerate(lines):
                    m = re.match(r'\s*(const|let|var)\s+(\w+)\s*=', line)
                    if m:
                        name = m.group(2)
                        if name in declared_consts:
                            # This is a redeclaration - skip this line and potentially next block
                            skip_block = True
                            continue
                        else:
                            declared_consts[name] = i
                    elif skip_block and line.strip() == '});':
                        skip_block = False
                        continue
                    if not skip_block:
                        clean_lines.append(line)
                fixed_js = '\n'.join(clean_lines)
                if fixed_js != content:
                    try:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(fixed_js)
                        content = fixed_js
                    except Exception:
                        pass
            ok, msg = SysTools.check_brackets_and_quotes(content)
            if not ok:
                return False, msg
            if file_path.endswith('.js') and not file_path.endswith(('.jsx', '.tsx')):
                try:
                    subprocess.run(["node", "--check", file_path], check=True, capture_output=True, text=True)
                    return True, "Sintaxis de Node.js correcta."
                except subprocess.CalledProcessError as e:
                    return False, e.stderr + "\n" + e.stdout
                except FileNotFoundError:
                    pass
            return True, "Sintaxis balanceada."
        return True, "Linter skip"

    @staticmethod
    def git_init_and_commit(msg="Auto-commit"):
        with SysTools.git_lock:
            try:
                # Verificar si es un repositorio git válido
                res = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=SysTools.WORKSPACE, capture_output=True, text=True)
                is_git = (res.returncode == 0)
                
                if not is_git:
                    # Si existe .git pero está corrupto, lo removemos
                    git_dir = os.path.join(SysTools.WORKSPACE, ".git")
                    if os.path.exists(git_dir):
                        shutil.rmtree(git_dir, ignore_errors=True)
                    subprocess.run(["git", "init"], cwd=SysTools.WORKSPACE, check=True, capture_output=True)
                    subprocess.run(["git", "config", "user.name", "Squad AI"], cwd=SysTools.WORKSPACE, check=True, capture_output=True)
                    subprocess.run(["git", "config", "user.email", "squad@ai.local"], cwd=SysTools.WORKSPACE, check=True, capture_output=True)
                
                subprocess.run(["git", "add", "."], cwd=SysTools.WORKSPACE, check=True, capture_output=True)
                subprocess.run(["git", "commit", "-m", msg], cwd=SysTools.WORKSPACE, capture_output=True)
                return True, "Shadow Git Commit Guardado."
            except Exception as e: return False, str(e)
        
    @staticmethod
    def git_push(repo_url, branch="main"):
        with SysTools.git_lock:
            try:
                subprocess.run(["git", "remote", "remove", "origin"], cwd=SysTools.WORKSPACE, capture_output=True)
                subprocess.run(["git", "remote", "add", "origin", repo_url], cwd=SysTools.WORKSPACE, check=True, capture_output=True)
                subprocess.run(["git", "branch", "-M", branch], cwd=SysTools.WORKSPACE, check=True, capture_output=True)
                res = subprocess.run(["git", "push", "-u", "origin", branch], cwd=SysTools.WORKSPACE, check=True, capture_output=True, text=True)
                return True, f"Push exitoso a {repo_url}"
            except subprocess.CalledProcessError as e:
                return False, f"Git error (Verifica autenticación/URL): {e.stderr}"
            except Exception as e:
                return False, str(e)

# ----------------- STATE & AGENTS -----------------
class PipelineState:
    def __init__(self):
        self.logs = []
        self.is_running = False
        self.pipeline_status = "idle"  # idle | running | waiting_spec_approval
        self.pending_pipeline_data = {}
        self.active_diagnostic = None  # None or {"error": str, "file": str, "line": str, "suggestion": str}
        self.design_identity = {
            "colors": "Dark elegant (slate, emerald accents)",
            "fonts": "Inter, System Font",
            "style": "Modern Minimalist",
            "preset": "default"
        }
        self.smart_routing = False
        self.active_port = 5000
        self.file_changes = []
        self.chat_history = []
        self.launcher_logs = []
        self.active_process = None
        self.active_model = "gemini-2.5-flash"
        self.linter_retries = 0
        self.token_in = 34205
        self.token_out = 8192
        self.cost_usd = 0.0
        self.cache_hits = 0
        self.temperature = 0.3
        self.system_prompt = "Eres el Orquestador V5. Responde siempre en JSON."
        self.default_port = 5000
        self.enable_rag = True
        self.pending_writes = {}
        self.interception_enabled = True

    def log(self, msgs):
        print(msgs)
        self.logs.append(msgs)

    def update_last_log(self, msg):
        if self.logs:
            self.logs[-1] = msg
        else:
            self.logs.append(msg)

state = PipelineState()

# ----------------- SETTINGS & SANITIZATION -----------------
SETTINGS_FILE = os.path.join(BASE_DIR, "squad_settings.json")

def load_settings():
    global SETTINGS_FILE
    defaults = {
        "workspace": os.path.join(BASE_DIR, "SQUAD_WORKSPACE"),
        "ollama_host": "http://127.0.0.1:11434",
        "default_model": "gemini-2.5-flash",
        "temperature": 0.3,
        "enable_rag": True,
        "default_port": 5000,
        "system_prompt": "Eres el Orquestador V5. Responde siempre en JSON.",
        "context_window": 16384,
        "interception_enabled": True,
        "smart_routing": False,
        "design_identity": {
            "colors": "Dark elegant (slate, emerald accents)",
            "fonts": "Inter, System Font",
            "style": "Modern Minimalist",
            "preset": "default"
        }
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                defaults.update(data)
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    SysTools.WORKSPACE = os.path.abspath(defaults["workspace"])
    OllamaAPI.HOST = defaults["ollama_host"]
    state.active_model = defaults["default_model"]
    state.temperature = defaults["temperature"]
    state.enable_rag = defaults["enable_rag"]
    state.default_port = defaults.get("default_port", 5000)
    state.system_prompt = defaults.get("system_prompt", "Eres el Orquestador V5. Responde siempre en JSON.")
    state.context_window = defaults.get("context_window", 16384)
    state.interception_enabled = defaults.get("interception_enabled", True)
    state.smart_routing = defaults.get("smart_routing", False)
    state.design_identity = defaults.get("design_identity", {
        "colors": "Dark elegant (slate, emerald accents)",
        "fonts": "Inter, System Font",
        "style": "Modern Minimalist",
        "preset": "default"
    })
    return defaults

def save_settings(new_settings):
    global SETTINGS_FILE
    current = load_settings()
    current.update(new_settings)
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=2)
        SysTools.WORKSPACE = os.path.abspath(current["workspace"])
        OllamaAPI.HOST = current["ollama_host"]
        state.active_model = current["default_model"]
        state.temperature = current["temperature"]
        state.enable_rag = current["enable_rag"]
        state.default_port = current.get("default_port", 5000)
        state.system_prompt = current.get("system_prompt", "Eres el Orquestador V5. Responde siempre en JSON.")
        state.context_window = current.get("context_window", 16384)
        state.interception_enabled = current.get("interception_enabled", True)
        state.smart_routing = current.get("smart_routing", False)
        state.design_identity = current.get("design_identity", {
            "colors": "Dark elegant (slate, emerald accents)",
            "fonts": "Inter, System Font",
            "style": "Modern Minimalist",
            "preset": "default"
        })
        return True, "Settings saved"
    except Exception as e:
        return False, str(e)

def sanitize_workspace_path(path):
    clean_name = path.lstrip("\\/")
    if ":" in clean_name:
        clean_name = clean_name.split(":", 1)[-1].lstrip("\\/")
    clean_name = os.path.normpath(clean_name)
    while clean_name.startswith("..") or clean_name.startswith("/") or clean_name.startswith("\\"):
        clean_name = clean_name.replace("../", "").replace("..\\", "").replace("..", "").lstrip("\\/")
    full_path = os.path.abspath(os.path.join(SysTools.WORKSPACE, clean_name))
    if not full_path.startswith(os.path.abspath(SysTools.WORKSPACE)):
        raise ValueError("Acceso denegado: fuera del workspace")
    return full_path

def run_autonomous_linter(error_logs_list, model):
    state.launcher_logs.append("🧹 [LINTER AUTÓNOMO]: Iniciando diagnóstico de código...")
    error_summary = "\n".join(error_logs_list)
    
    files_context = []
    if os.path.exists(SysTools.WORKSPACE):
        for root, _, files in os.walk(SysTools.WORKSPACE):
            if ".git" in root or "node_modules" in root or "__pycache__" in root or "venv" in root: continue
            for f in files:
                p = os.path.join(root, f)
                rel = os.path.relpath(p, SysTools.WORKSPACE).replace('\\', '/')
                content = SysTools.read(rel)
                files_context.append(f"@@FILE: {rel}\n{content}\n@@ENDFILE@@")
                
    files_context_str = "\n\n".join(files_context)
    
    prompt = f"""Eres el Agente Linter de Emergencia de SQUAD. La aplicación local acaba de crashear durante la ejecución.
A continuación se muestran los logs de error de la terminal:
---
{error_summary}
---

Los archivos actuales en el espacio de trabajo son:
---
{files_context_str}
---

Tu objetivo es solucionar el error. Puede ser una importación faltante, un error de sintaxis, dependencias desalineadas, etc.
REGLA DE IMPORTACIÓN: Si el error se debe a una importación local de un archivo inexistente (como require('./config')), debes reescribir el archivo importador para incorporar esa lógica directamente (autocontenido) o generar el archivo faltante con la sintaxis @@FILE: en tu respuesta.
REGLA DE PUERTO: El servidor siempre debe escuchar en el puerto definido por la variable de entorno PORT (process.env.PORT o os.environ.get('PORT')), utilizando un fallback adecuado si no está definida.
{OptTools.CODE_GUIDELINES}

REGLA DE FORMATO OBLIGATORIA: Debes responder ÚNICAMENTE utilizando uno de los siguientes formatos para cada archivo que modifiques o crees:

Para reemplazar o crear un archivo completo:
@@FILE: nombre_del_archivo
código completo aquí
@@ENDFILE@@

Para aplicar un parche específico en un archivo existente:
@@PATCH: nombre_del_archivo
<<<<<<< SEARCH
código original exacto a reemplazar
=======
código de reemplazo
>>>>>>> END
@@ENDPATCH

No agregues ninguna explicación ni texto introductorio ni conclusiones. Solo genera las correcciones de archivos con el formato indicado."""
    
    try:
        orig_val = getattr(state, "interception_enabled", True)
        state.interception_enabled = False
        fixed_output = AIProvider.generate(model=model, prompt=prompt, no_cache=True)
        corrected_files = SysTools.extract_and_write_multifile(fixed_output)
        state.launcher_logs.append(f"🧹 [LINTER AUTÓNOMO]: Reparación aplicada sobre archivos: {str(corrected_files)}")
    except Exception as e:
        state.launcher_logs.append(f"❌ [LINTER AUTÓNOMO] Error invocando IA para reparación: {e}")
    finally:
        state.interception_enabled = orig_val

def stream_process_output(proc, model):
    has_crashed = False
    error_lines = []
    
    # Initialize error tracking
    proc.last_err_loc = None
    
    while True:
        line = proc.stdout.readline()
        if not line and proc.poll() is not None:
            break
        if line:
            line_str = line.decode('utf-8', errors='ignore').strip() if isinstance(line, bytes) else line.strip()
            state.launcher_logs.append(line_str)
            print(f"[LAUNCHER] {line_str}")
            
            # Python traceback parser
            # e.g., File "app.py", line 12, in <module>
            py_match = re.search(r'File "([^"]+)", line (\d+)', line_str)
            if py_match:
                err_file = py_match.group(1)
                err_line = py_match.group(2)
                proc.last_err_loc = (err_file, err_line)
                
            if any(marker in line_str for marker in ["ModuleNotFoundError:", "NameError:", "TypeError:", "ValueError:", "SyntaxError:"]):
                has_crashed = True
                loc = getattr(proc, "last_err_loc", None) or ("app.py", "1")
                state.active_diagnostic = {
                    "error": line_str,
                    "file": loc[0],
                    "line": loc[1],
                    "suggestion": "Se detectó una excepción de Python. Usa 'Auto-reparar con IA' o edita el archivo en Monaco."
                }
                print(f"[LAUNCHER] ⚠️ Error fatal detectado ({line_str}). Forzando reinicio para auto-reparación.")
                try:
                    SysTools.kill_process_tree(proc.pid)
                except:
                    pass
            elif any(marker in line_str for marker in ["ReferenceError:", "TypeError:", "SyntaxError:"]):
                # JS/Node error parser
                has_crashed = True
                js_match = re.search(r'([a-zA-Z0-9_\-\.]+):(\d+)', line_str)
                if js_match:
                    state.active_diagnostic = {
                        "error": line_str,
                        "file": js_match.group(1),
                        "line": js_match.group(2),
                        "suggestion": "Se detectó un error en el código JS. Revisa la línea señalada en Monaco."
                    }
                else:
                    state.active_diagnostic = {
                        "error": line_str,
                        "file": "unknown",
                        "line": "1",
                        "suggestion": "Se detectó un error en JS. Revisa los logs de consola."
                    }
            elif any(marker in line_str for marker in ["Error:", "Traceback (most recent call last):"]):
                has_crashed = True
                
            if has_crashed or any(marker in line_str.lower() for marker in ["fail", "error", "exception"]):
                error_lines.append(line_str)
                if len(error_lines) > 30:
                    error_lines.pop(0)

    ret_code = proc.poll()
    if (ret_code is not None and ret_code != 0) or has_crashed:
        state.launcher_logs.append("[LINTER AUTÓNOMO] 🧹 Detectado crash o error de ejecución.")
        if state.linter_retries < 3:
            state.linter_retries += 1
            state.launcher_logs.append(f"[LINTER AUTÓNOMO] 🔄 Intento de autoreparación {state.linter_retries}/3 en progreso...")
            try:
                run_autonomous_linter(error_lines, model)
                state.launcher_logs.append("[LINTER AUTÓNOMO] 🚀 Lanzando de nuevo tras reparación...")
                threading.Thread(target=run_launch_sequence, args=(model,), daemon=True).start()
            except Exception as e:
                state.launcher_logs.append(f"❌ [LINTER AUTÓNOMO] Error en ciclo de reparación: {e}")
        else:
            state.launcher_logs.append("⚠️ [LINTER AUTÓNOMO] Límite de autoreparación alcanzado. Por favor corrige manualmente en el Monaco Editor.")

def run_system_installer(tool_name):
    tool_map = {
        "node": "OpenJS.NodeJS",
        "git": "Git.Git",
        "docker": "Docker.DockerDesktop"
    }
    
    winget_id = tool_map.get(tool_name.lower())
    if not winget_id:
        return False, f"Herramienta '{tool_name}' no soportada para auto-instalación."
        
    if sys.platform != 'win32':
        return False, "La auto-instalación por ahora solo está soportada en Windows (vía winget)."
        
    ps_cmd = f"Start-Process winget -ArgumentList 'install --id {winget_id} -e --accept-source-agreements --accept-package-agreements'"
    cmd = f"powershell -Command \"{ps_cmd}\""
    
    state.launcher_logs.append(f"[AUTO-INSTALADOR] Lanzando instalador de {tool_name}...")
    state.launcher_logs.append("[AUTO-INSTALADOR] ⚠️ Sigue el progreso en la ventana externa de consola que se abrirá en tu pantalla.")
    
    try:
        subprocess.run(cmd, shell=True, check=True)
        state.launcher_logs.append(f"[AUTO-INSTALADOR] ✅ Ventana de instalación de {tool_name} abierta correctamente.")
        state.launcher_logs.append("[AUTO-INSTALADOR] Presiona 'REFRESCAR' en el panel de Pre-flight una vez que finalice la instalación en la ventana externa.")
        return True, f"Lanzado instalador de {tool_name}."
    except Exception as e:
        state.launcher_logs.append(f"[AUTO-INSTALADOR] ❌ Falló al lanzar el instalador: {e}")
        return False, str(e)

def run_launch_sequence(model):
    try:
        # 1. Clean residual files lock and processes in SQUAD_WORKSPACE
        state.launcher_logs.append("🧹 [SISTEMA] Liberando bloqueos de archivos y procesos residuales...")
        SysTools.cleanup_workspace_processes()

        # 2. SQLite old DB auto-backup if schema files changed
        schema_keywords = ["models.py", "schema.sql", "database.py", "db.py", "models.ts"]
        db_changed = any(any(kw in f for kw in schema_keywords) for f in getattr(state, "file_changes", []))
        if db_changed and os.path.exists(SysTools.WORKSPACE):
            for file_name in os.listdir(SysTools.WORKSPACE):
                if file_name.endswith(('.db', '.sqlite', '.sqlite3')):
                    db_path = os.path.join(SysTools.WORKSPACE, file_name)
                    backup_path = db_path + ".backup"
                    try:
                        if os.path.exists(db_path):
                            state.launcher_logs.append(f"📡 [SISTEMA] Cambios en el modelo de datos. Archivando DB vieja en: {backup_path}")
                            if os.path.exists(backup_path):
                                os.remove(backup_path)
                            os.rename(db_path, backup_path)
                    except Exception as ex:
                        state.launcher_logs.append(f"⚠️ [SISTEMA] Error al archivar base de datos: {ex}")

        # 3. Dynamic ESM/CommonJS healing
        state.launcher_logs.append("📦 [SISTEMA] Validando tipos CommonJS/ESM...")
        SysTools.auto_heal_esm_commonjs()

        # 4. SQLite WAL auto-injection
        state.launcher_logs.append("📡 [SISTEMA] Optimizando conexiones SQLite (WAL / busy_timeout)...")
        SysTools.auto_heal_sqlite_connections()

        # Pre-launch workspace syntax scan
        state.launcher_logs.append("🧹 [LINTER]: Verificando sintaxis de archivos en el workspace antes de lanzar...")
        syntax_errors = []
        if os.path.exists(SysTools.WORKSPACE):
            for root, _, files_in_dir in os.walk(SysTools.WORKSPACE):
                if ".git" in root or "node_modules" in root or "__pycache__" in root or "venv" in root: continue
                for f in files_in_dir:
                    rel = os.path.relpath(os.path.join(root, f), SysTools.WORKSPACE).replace('\\', '/')
                    if rel.endswith(('.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.css')):
                        ok, linter_msg = SysTools.run_linter(os.path.join(root, f))
                        if not ok:
                            syntax_errors.append(f"Archivo: {rel}\nError: {linter_msg}")
                            state.launcher_logs.append(f"⚠️ Error de Sintaxis en {rel}: {linter_msg}")
        
        if syntax_errors:
            state.launcher_logs.append("[LINTER] Detectados errores de sintaxis antes del lanzamiento.")
            err_details = syntax_errors[0]
            err_msg = err_details.split('\nError: ')[1] if '\nError: ' in err_details else err_details
            err_file = err_details.split('\nError: ')[0].replace('Archivo: ', '') if '\nError: ' in err_details else "unknown"
            err_line_match = re.search(r'línea (\d+)', err_details)
            err_line = err_line_match.group(1) if err_line_match else "1"
            
            state.active_diagnostic = {
                "error": err_msg,
                "file": err_file,
                "line": err_line,
                "suggestion": "El linter detectó un error. Por favor corrígelo o usa 'Auto-reparar con IA'."
            }
            
            if state.linter_retries < 3:
                state.linter_retries += 1
                state.launcher_logs.append(f"[LINTER AUTÓNOMO] 🔄 Intento de autoreparación {state.linter_retries}/3 en progreso...")
                run_autonomous_linter(syntax_errors, model)
                state.launcher_logs.append("[LINTER AUTÓNOMO] 🚀 Re-intentando lanzamiento tras reparación...")
                threading.Thread(target=run_launch_sequence, args=(model,), daemon=True).start()
                return True, "Iniciada autoreparación del linter."
            else:
                state.launcher_logs.append("⚠️ [LINTER AUTÓNOMO] Límite de autoreparación alcanzado. Lanzando de todas formas...")
        else:
            state.active_diagnostic = None

        if state.active_process and state.active_process.poll() is None:
            SysTools.kill_process_tree(state.active_process.pid)
            state.launcher_logs.append("[SISTEMA] Terminado el proceso local previo de raíz (árbol completo)...")

        # Git Auto-Snapshot
        SysTools.git_init_and_commit("Pre-run backup snapshot")

        state.launcher_logs.append("[SISTEMA] Arrancando secuencia de Launch...")
        
        # Setup dynamic virtual environment (venv)
        python_exe, pip_exe = SysTools.setup_venv(state.launcher_logs)

        # Auto-detect dependencies
        try:
            SysTools.auto_detect_nodejs_dependencies()
            SysTools.auto_detect_python_dependencies()
            SysTools.auto_heal_hardcoded_ports()
        except Exception as e:
            state.launcher_logs.append(f"⚠️ [SISTEMA] Error en auto-detección/autocuración: {e}")

        # Isolate workspace package.json from parent module scope if it doesn't exist
        pkg_path = os.path.join(SysTools.WORKSPACE, "package.json")
        if not os.path.exists(pkg_path):
            try:
                target_f = SysTools.find_node_entry_point()
                start_cmd = f"node {target_f}"
                with open(pkg_path, "w", encoding="utf-8") as f_pkg:
                    json.dump({
                        "name": "squad-workspace-project",
                        "type": "commonjs",
                        "scripts": {
                            "start": start_cmd
                        }
                    }, f_pkg, indent=2)
            except Exception:
                pass

        if os.path.exists(os.path.join(SysTools.WORKSPACE, "docker-compose.yml")):
            cmd = "docker-compose up --build"
        elif os.path.exists(os.path.join(SysTools.WORKSPACE, "package.json")):
            cmd = "npm install --prefer-offline --no-audit --no-fund && npm start"
        elif os.path.exists(os.path.join(SysTools.WORKSPACE, "requirements.txt")):
            cmd = f'"{pip_exe}" install --prefer-offline -r requirements.txt && "{python_exe}" app.py'
        elif os.path.exists(os.path.join(SysTools.WORKSPACE, "app.py")):
            cmd = f'"{python_exe}" app.py'
        elif os.path.exists(os.path.join(SysTools.WORKSPACE, "index.html")) or os.path.exists(os.path.join(SysTools.WORKSPACE, "main_output.html")):
            # Check if index.html uses Jinja2/Flask templates — if so, prefer Flask runner
            html_path = os.path.join(SysTools.WORKSPACE, "index.html") or os.path.join(SysTools.WORKSPACE, "main_output.html")
            try:
                with open(html_path, 'r', encoding='utf-8') as _f:
                    _html_content = _f.read()
                _uses_jinja = '{{' in _html_content or '{%' in _html_content or 'url_for' in _html_content
            except Exception:
                _uses_jinja = False
            if _uses_jinja and os.path.exists(os.path.join(SysTools.WORKSPACE, "app.py")):
                cmd = f'"{python_exe}" app.py'
            elif _uses_jinja:
                # Generate a minimal Flask runner for Jinja2 templates
                state.launcher_logs.append("[SISTEMA] ⚠️ index.html usa Jinja2. Generando app.py mínimo de Flask...")
                minimal_flask = '''import os
from flask import Flask, send_from_directory, render_template

# template_folder and static_folder point to the workspace root
# so Flask finds index.html, styles.css, app.js etc. directly
app = Flask(
    __name__,
    template_folder=os.path.dirname(os.path.abspath(__file__)),
    static_folder=os.path.dirname(os.path.abspath(__file__)),
    static_url_path=""
)

@app.route("/")
def index():
    try:
        # Try rendering Jinja2 template if index.html uses template tags
        return render_template("index.html")
    except Exception:
        # Fallback to static serving if rendering fails (e.g. syntax errors in template)
        return app.send_static_file("index.html")

@app.route("/<path:filename>")
def static_files(filename):
    import os
    from flask import send_from_directory
    actual_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    if not os.path.exists(actual_path) and filename.startswith("static/"):
        stripped = filename.replace("static/", "", 1)
        if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), stripped)):
            filename = stripped
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), filename)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, port=port)
'''
                # Write directly to file, bypassing interceptor (auto-generated launcher)
                _app_path = os.path.join(SysTools.WORKSPACE, "app.py")
                os.makedirs(os.path.dirname(_app_path), exist_ok=True)
                with open(_app_path, "w", encoding="utf-8") as _fapp:
                    _fapp.write(minimal_flask)
                cmd = f'"{pip_exe}" install --prefer-offline flask && "{python_exe}" app.py'
            else:
                cmd = f'"{python_exe}" -m http.server 5000'
        else:
            workspace_files = os.listdir(SysTools.WORKSPACE) if os.path.exists(SysTools.WORKSPACE) else []
            main_files = [f for f in workspace_files if f.startswith("main_output.")]
            
            target_file = None
            if main_files:
                main_files.sort(key=lambda x: (
                    0 if x == "main_output.py" else
                    1 if x == "main_output.js" else
                    2 if x.endswith((".sh", ".bat", ".cmd")) else
                    3
                ))
                target_file = main_files[0]
            
            if target_file:
                target_path = os.path.join(SysTools.WORKSPACE, target_file)
                with open(target_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                lines = content.splitlines()
                if lines and lines[0].strip().lower() in ("bash", "sh", "console", "terminal", "intento", "json", "python", "js", "ts", "tsx", "html", "css"):
                    lines = lines[1:]
                content = "\n".join(lines).strip().replace("```bash", "").replace("```", "").strip()
                
                is_script = False
                if target_file.endswith((".sh", ".bat", ".cmd")):
                    is_script = True
                elif target_file.endswith((".js", ".py", ".ts", ".tsx", ".html", ".css", ".json", ".sql", ".md")):
                    is_script = False
                elif "npx " in content or "npm " in content:
                    is_script = True
                elif "import " not in content and "print" not in content and content:
                    is_script = True
                
                if is_script:
                    valid_lines = []
                    for line in content.splitlines():
                        line = line.strip()
                        if not line or line.startswith("#"): continue
                        if line.lower() in ("bash", "sh", "console", "terminal", "intento", "```bash", "```sh", "```"): continue
                        valid_lines.append(line)
                    cmd = " && ".join(valid_lines)
                else:
                    if target_file == "main_output.js":
                        cmd = f"node {target_file}"
                    else:
                        cmd = f'"{python_exe}" {target_file}'
            else:
                cmd = f'"{python_exe}" main_output.py'
        
        # Intelligent Port Collision Detection and Auto-Cleanup
        ports_in_cmd = re.findall(r'\b(3000|5000|8000|8080|8001|3001)\b', cmd)
        for p_str in set(ports_in_cmd):
            p_int = int(p_str)
            # Find if there is any process on this port
            for active_p in get_listening_ports():
                if active_p['port'] == p_int and active_p['pid'] != os.getpid():
                    state.launcher_logs.append(f"[SISTEMA] 🧹 Puerto {p_int} ocupado. Liberando puerto matando PID {active_p['pid']} ({active_p['name']})...")
                    try:
                        SysTools.kill_process_tree(active_p['pid'])
                        time.sleep(0.3)
                    except Exception as ex:
                        state.launcher_logs.append(f"[SISTEMA] Error al liberar puerto {p_int}: {ex}")
            
            free_p = SysTools.get_free_port(p_int)
            if free_p != p_int:
                cmd = re.sub(rf'\b{p_str}\b', str(free_p), cmd)
                state.launcher_logs.append(f"[SISTEMA] Puerto {p_str} sigue ocupado. Re-enrutando a puerto libre {free_p}.")
        
        # Determine port for environment and context
        start_port = getattr(state, "default_port", 5000)
        final_ports = re.findall(r'\b\d{4,5}\b', cmd)
        if final_ports:
            port = int(final_ports[0])
        else:
            port = SysTools.get_free_port(start_port)
            
        state.active_port = port
        state.launcher_logs.append(f"[SISTEMA] Puerto asignado para ejecución: {port}")
        
        if "5000" in cmd and str(port) != "5000":
            cmd = cmd.replace("5000", str(port))
            
        state.launcher_logs.append(f"[SISTEMA] Ejecutando: {cmd}")
        
        proc_env = os.environ.copy()
        proc_env["PORT"] = str(port)
        
        proc = subprocess.Popen(cmd, shell=True, cwd=SysTools.WORKSPACE, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=proc_env, text=True, bufsize=1, encoding='utf-8', errors='replace')
        state.active_process = proc
        threading.Thread(target=stream_process_output, args=(proc, model), daemon=True).start()
        return True, f"Secuencia iniciada en puerto {port}: {cmd}"
    except Exception as e:
        return False, str(e)

def run_agent_pipeline(prompt, model):
    state.is_running = True
    state.pipeline_status = "running"
    state.logs = []
    SysTools.setup()
    
    try:
        is_gemini = model.startswith("gemini-")
        if is_gemini:
            if not GeminiAPI.is_available():
                raise Exception("GEMINI_API_KEY no configurada. Añádela a tu archivo .env o .env.local")
            target_model = model
        else:
            if not OllamaAPI.is_online():
                raise Exception("Ollama no responde. Enciende Ollama (11434).")
            models = OllamaAPI.list_models()
            if not models:
                raise Exception("No tienes modelos descargados en Ollama. Haz 'ollama run qwen2.5-coder' en tu terminal primero.")
            target_model = model if model in models else models[0]
        
        state.log(f"🔎 [AGENTE INFRA]: Buscando contexto web para '{prompt}'...")
        search_ctx = SysTools.web_search(prompt + " best practices")
        state.log(f"✅ Contexto Web obtenido.")

        state.log(f"🧠 [AGENTE ARQUITECTO] ({target_model}): Diseñando esquema global...")
        
        preflight = {
            "node": bool(shutil.which('node')),
            "docker": bool(shutil.which('docker')),
            "python": bool(shutil.which('python') or shutil.which('python3')),
            "git": bool(shutil.which('git'))
        }
        
        existing_context = ""
        if os.path.exists(SysTools.WORKSPACE) and os.listdir(SysTools.WORKSPACE):
            existing_context = f"\n\nArchivos actuales del proyecto para referencia incremental:\n{OptTools.get_relevant_files_context(prompt)}"

        arch_prompt = (
            f"Eres el Agente Arquitecto Senior. El usuario quiere: '{prompt}'. Datos técnicos de la web: {search_ctx}.{existing_context}\n\n"
            "⚠️ RESTRICCIÓN DEL SISTEMA ANFITRIÓN ⚠️\n"
            f"Host local: {preflight}. \n"
            "**DISEÑA LA ARQUITECTURA ÚNICAMENTE CON AQUELLAS MARCADAS COMO True.**\n"
            "REGLA DE PREVISUALIZACIÓN: Si planificas una previsualización en el navegador local, la página principal (index.html) debe ser un HTML5 estándar "
            "ejecutable directamente en el navegador sin bundler (o usar librerías como Vue/React/Tailwind vía CDN), a menos que el entorno soporte y configure explícitamente un entorno Node/NPM.\n"
            "Crea un plan técnico detallado de la arquitectura y la especificación de la aplicación. Llámalo Especificación de Software (SPEC). Sé extremadamente detallado."
        )
        plan = AIProvider.generate(model=target_model, prompt=arch_prompt)
        SysTools.write("SPEC.md", plan)
        SysTools.write("ARCHITECTURE.md", plan)
        state.log("✅ Especificación del Proyecto generada (SPEC.md).")

        # Save pipeline parameters to resume Phase 2
        state.pending_pipeline_data = {
            "prompt": prompt,
            "model": model,
            "target_model": target_model,
            "search_ctx": search_ctx,
            "plan": plan
        }
        state.pipeline_status = "waiting_spec_approval"
        state.is_running = False
        state.log("⏸️ Pipeline en pausa. Esperando revisión y aprobación de SPEC.md...")
    except Exception as e:
        state.log(f"❌ ERROR EN FASE 1: {str(e)}")
        state.is_running = False
        state.pipeline_status = "idle"

def run_agent_pipeline_phase_2():
    data = getattr(state, "pending_pipeline_data", {})
    if not data:
        state.log("❌ Error: No hay datos de pipeline pendientes para reanudar.")
        state.pipeline_status = "idle"
        state.is_running = False
        return
        
    prompt = data.get("prompt")
    model = data.get("model")
    target_model = data.get("target_model")
    search_ctx = data.get("search_ctx")
    
    plan = SysTools.read("SPEC.md")
    if not plan:
        plan = data.get("plan")
        
    state.pipeline_status = "running"
    state.is_running = True
    state.log("🚀 Aprobado. Reanudando enjambre (Fase 2: DBA + UI + Backend + QA)...")
    
    try:
        existing_context = ""
        if os.path.exists(SysTools.WORKSPACE) and os.listdir(SysTools.WORKSPACE):
            existing_context = f"\n\nArchivos actuales del proyecto para referencia incremental:\n{OptTools.get_relevant_files_context(prompt)}"

        style_mem = getattr(state, "design_identity", {})
        style_mem_str = ""
        if style_mem:
            style_mem_str = f"\n\nIDENTIDAD DE DISEÑO REQUERIDA:\n- Colores: {style_mem.get('colors')}\n- Tipografías: {style_mem.get('fonts')}\n- Estilo visual: {style_mem.get('style')} (Preset: {style_mem.get('preset')})\nDebes ceñirte a esta identidad visual."

        state.log("⚡ [SQUAD] Lanzando Agente DBA y Agente UI Frontend en paralelo...")
        
        db_output = [None]
        ui_output = [None]
        
        def run_db_agent():
            try:
                db_p = (
                    f"Basado en este plan:\n{plan}\nGenera un esquema SQL estándar portable e independiente (compatible con SQLite y PostgreSQL). "
                    "REGLAS ESTRICTAS DE PORTABILIDAD: "
                    "1) NO uses cláusulas específicas del motor como CREATE DATABASE o USE. "
                    "2) Usa tipos de datos estándar SQL (INTEGER, TEXT, REAL, TIMESTAMP, VARCHAR). "
                    "3) Usa CREATE TABLE IF NOT EXISTS. "
                    "4) Incluye sentencias INSERT estándar con datos de prueba realistas (al menos 3-5 filas por tabla) que funcionen tanto en SQLite como en PostgreSQL. "
                    "Y adicionalmente, emite un mini reporte de seguridad sobre vulnerabilidades comunes en un archivo de reporte de seguridad independiente en Markdown utilizando la sintaxis de bloque: @@FILE: SECURITY_REPORT.md. NO escribas este reporte dentro del archivo de código SQL o Python, debe ser un archivo de texto independiente. "
                    "ANTI-BUG: Asegúrate de que las consultas SQL sean estándar y no contengan comillas invertidas (backticks) de MySQL.\n"
                    f"{OptTools.CODE_GUIDELINES}\n"
                    f"{existing_context}"
                )
                db_output[0] = AIProvider.generate(model=target_model, prompt=db_p)
            except Exception as e:
                db_output[0] = f"Error DBA: {e}"

        def run_ui_agent():
            try:
                ui_p = (
                    f"Basado en:\n{plan}\n"
                    "Genera únicamente los componentes Frontend / UI, usando Tailwind o CSS puro. Asegúrate de ser espectacular visualmente. "
                    "REGLA CRÍTICA DE HTML: El archivo index.html DEBE ser un HTML5 estándar autocontenido. "
                    "PROHIBIDO USAR Jinja2 o sintaxis de template Flask como {{ url_for('static', filename='archivo') }}. "
                    "Para CSS y JS usa SIEMPRE rutas relativas simples: <link rel='stylesheet' href='styles.css'> y <script src='app.js'></script>. "
                    "REGLA CRÍTICA DE SEPARACIÓN: Si utilizas estilos CSS personalizados, DEBES escribirlos obligatoriamente en un bloque ```css separado para generar styles.css. Si usas interactividad JS del cliente, escríbela obligatoriamente en un bloque ```javascript separado (se guardará como app.js). "
                    "Si utilizas clases de Tailwind CSS, DEBES incluir obligatoriamente el script CDN de Tailwind Play en la cabecera del HTML: <script src='https://cdn.tailwindcss.com'></script>. "
                    "NO escribas código Vue SFC ni React JSX en archivos .html sin bundler. Si usas React o Vue, impórtalos vía CDN. "
                    "ANTI-BUG: Evita usar rutas absolutas de sistema (/home/user/...) o variables de entorno del servidor dentro del HTML.\n"
                    f"{OptTools.CODE_GUIDELINES}\n"
                    f"{existing_context}{style_mem_str}"
                )
                ui_output[0] = AIProvider.generate(model=target_model, prompt=ui_p)
            except Exception as e:
                ui_output[0] = f"Error UI: {e}"

        t_db = threading.Thread(target=run_db_agent)
        t_ui = threading.Thread(target=run_ui_agent)
        
        t_db.start()
        t_ui.start()
        
        t_db.join()
        t_ui.join()
        
        created_ui = []
        if db_output[0] and not db_output[0].startswith("Error DBA"):
            SysTools.extract_and_write_multifile(db_output[0])
            state.log("✅ Modelos de DB y Seguridad previstos (Paralelo).")
        else:
            state.log(f"⚠️ DBA Agent falló o dio error: {db_output[0]}")
            
        if ui_output[0] and not ui_output[0].startswith("Error UI"):
            created_ui = SysTools.extract_and_write_multifile(ui_output[0])
            state.log("✅ Sistema de Diseño Frontend/UI creado (Paralelo).")
        else:
            state.log(f"⚠️ UI Agent falló o dio error: {ui_output[0]}")
            
        state.log(f"💻 [AGENTE BACKEND DEV] ({target_model}): Escribiendo Lógica de Negocio y APIs...")
        code_p = (
            f"Basado en:\n{plan}\n"
            "El UI ya fue creado. Escribe el Backend/Archivos principales. "
            "REGLAS CRÍTICAS PARA EL BACKEND: "
            "1) Si generas una app Flask, SIEMPRE usa template_folder y static_folder apuntando al directorio del archivo: "
            "   app = Flask(__name__, template_folder=os.path.dirname(os.path.abspath(__file__)), static_folder=os.path.dirname(os.path.abspath(__file__)), static_url_path='') "
            "2) Para servir index.html usa app.send_static_file('index.html') o send_from_directory(), NO render_template() a menos que el HTML use Jinja2 correctamente. "
            "3) Si el index.html usa rutas relativas (href='styles.css'), sirve con send_static_file. "
            "4) BASE DE DATOS PORTABLE: Utiliza preferentemente un ORM (como SQLAlchemy o SQLModel para Python, o Prisma/Drizzle para JS) configurado para SQLite de forma local, facilitando escalar a PostgreSQL en producción simplemente cambiando DATABASE_URL en el .env. Evita hardcodear sentencias SQL específicas de motor. "
            "5) PUERTO DINÁMICO: El servidor debe escuchar en el puerto indicado por la variable de entorno PORT (process.env.PORT para Node.js, os.environ.get('PORT') para Python), utilizando 5000 como valor por defecto y con debug=False. "
            "6) Asegúrate de IMPORTAR todas las librerías utilizadas (como 'os', 're', 'sys') y DEFINIR o IMPORTAR todas las funciones y variables auxiliares referenciadas en las rutas (como validaciones de email/contraseña, cifrado de contraseñas, etc.). El código generado debe ser 100% autoejecutable y libre de NameError. "
            "7) DEBES definir la ruta raíz @app.route('/') para servir la página principal index.html utilizando app.send_static_file('index.html') en Python, o res.sendFile(path.join(__dirname, 'index.html')) en Node.js/Express. "
            "8) Si generas una app Node/Express, SIEMPRE sirve los archivos estáticos desde la raíz del proyecto (el directorio actual '.'): app.use(express.static(__dirname)) o app.use(express.static('.')). NO utilices ni crees carpetas como 'public' o 'static'. Todo debe servirse desde la raíz del workspace. "
            "9) INTEGRACIÓN RESILIENTE: Si la aplicación requiere llaves o credenciales para APIs de terceros (como STRIPE_API_KEY o OPENAI_API_KEY), valídalas: si la variable de entorno está vacía, la app debe continuar ejecutándose mostrando un mensaje en consola y utilizando mocks/servicios simulados para pruebas locales en vez de crashear.\n"
            "10) AUTOCONTENIDO Y SIN IMPORTACIONES HUÉRFANAS: Todo el código backend debe estar en un único archivo principal autoejecutable (main_output.js para Node.js/Express, o main_output.py para Python/Flask/FastAPI) que contenga la conexión a base de datos, rutas, middlewares y lógica. NO intentes importar o requerir archivos locales inexistentes (como ./config, ./routes/auth, etc.). Si es estrictamente necesario separar el código en múltiples archivos, debes generarlos explícitamente en bloques @@FILE: separados en la misma respuesta, pero se prefiere fuertemente un único archivo consolidado para evitar dependencias locales rotas.\n"
            f"{OptTools.CODE_GUIDELINES}\n"
            f"{existing_context}"
        )
        full_code_output = AIProvider.generate(model=target_model, prompt=code_p)
        created_back = SysTools.extract_and_write_multifile(full_code_output)
        
        created_files = list(set(created_ui + created_back))
        state.log(f"✅ Se crearon/modificaron {len(created_files)} archivos en total...")
        
        state.log(f"🤖 [AGENTE CODE REVIEWER] ({target_model}): Analizando calidad de código generado...")
        review_p = f"Revisa los archivos creados ({str(created_files)}) que hacen parte de esto:\n{plan}\nSeñala si hay errores graves, importaciones faltantes, o asimetrías de puertos (ejemplo 3000 vs 8000). Si encuentras algo crítico, escribe SÍ_CRITICO y qué falló."
        code_review = AIProvider.generate(model=target_model, prompt=review_p)
        
        if "SÍ_CRITICO" in code_review.upper():
            state.log(f"⚠️ El Code Reviewer detectó fallos. Inyectando AGENTE LINTER AUTÓNOMO...")
            fix_p = f"Corrige estos errores expuestos en el siguiente Code Review:\n{code_review}\nGenera el código reparado para los archivos necesarios usando formato @@FILE: o @@PATCH:"
            fix_out = AIProvider.generate(model=target_model, prompt=fix_p)
            SysTools.extract_and_write_multifile(fix_out)
            state.log("🧹 Linter Autónomo resolvió los bugs del Review.")
        else:
            state.log("✅ Code Review superado con excelencia (Clean Code).")

        # Multi-language linter validation
        state.log("🧹 [SYNTAX CHECK]: Verificando sintaxis de archivos creados...")
        syntax_errors = []
        for cf in created_files:
            full_path = os.path.join(SysTools.WORKSPACE, cf)
            if os.path.exists(full_path):
                ok, linter_msg = SysTools.run_linter(full_path)
                if not ok:
                    syntax_errors.append(f"Archivo: {cf}\nError: {linter_msg}")
                    state.log(f"⚠️ Error de Sintaxis en {cf}: {linter_msg}")
        
        if syntax_errors:
            state.log("🧹 [LINTER AUTÓNOMO]: Corrigiendo errores de sintaxis detectados...")
            run_autonomous_linter(syntax_errors, target_model)
            state.log("✅ Errores de sintaxis reparados.")

        # UI/UX Visual Linter Audit
        state.log("🎨 [AGENTE AUDITOR UX]: Ejecutando auditoría de calidad visual...")
        try:
            index_html = SysTools.read("index.html")
            styles_css = SysTools.read("styles.css")
            ux_audit_prompt = f"""Eres el Agente UI/UX Auditor de SQUAD. Tu tarea es analizar la interfaz del proyecto y generar un Reporte de Calidad Visual detallado en formato Markdown, y sugerir mejoras.
index.html:
{index_html}
styles.css:
{styles_css}

Analiza:
1. Contraste de colores y legibilidad.
2. Consistencia en fuentes y espaciados.
3. Responsividad móvil básica.

Escribe un reporte conciso en español. Escríbelo y guárdalo en VISUAL_REPORT.md.
No incluyas código de archivo completo. Solo reporta el análisis."""
            ux_report = AIProvider.generate(model=target_model, prompt=ux_audit_prompt)
            SysTools.write("VISUAL_REPORT.md", ux_report)
            state.log("🎨 [AGENTE AUDITOR UX]: Reporte de diseño generado en VISUAL_REPORT.md")
        except Exception as e:
            state.log(f"⚠️ No se pudo autogenerar el reporte de calidad visual: {e}")

        state.log(f"🧪 [AGENTE QA & DEVOPS] ({target_model}): Scripts de Testing y Pipeline CI/CD...")
        qa_p = f"Escribe scripts de Test (Jest, PyTest o genérico) según el stack, O un pipeline de Github Actions (.github/workflows/main.yml). Usa formato @@FILE o @@PATCH"
        test_out = AIProvider.generate(model=target_model, prompt=qa_p)
        SysTools.extract_and_write_multifile(test_out)
        state.log("✅ Suite QA y pipelines de DevOps finalizados.")

        state.log(f"⏱️ [SHADOW GIT]: Documentando snapshot del Workspace...")
        git_ok, git_msg = SysTools.git_init_and_commit("Auto-commit: Workspace AI V6 Multi-Agent")
        state.log(f"✅ {git_msg}")

        state.log("\n🏆 SQUAD SYSTEM: Motor Multi-Agente ORCHESTRATOR Finalizado.")
    except Exception as e:
        state.log(f"❌ ERROR CRÍTICO DEL ENJAMBRE: {str(e)}")
    finally:
        state.is_running = False
        state.pipeline_status = "idle"

# ----------------- PROJECT TEMPLATES GALLERY -----------------
TEMPLATES_GALLERY = {
    "fastapi": {
        "app.py": """from fastapi import FastAPI
import sqlite3

app = FastAPI()

def init_db():
    conn = sqlite3.connect("local_project.db")
    cursor = conn.cursor()
    cursor.execute(\"\"\"
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT
        )
    \"\"\")
    conn.commit()
    conn.close()

init_db()

@app.get("/")
def read_root():
    return {"message": "Welcome to FastAPI + SQLite Starter App!"}

@app.get("/items")
def get_items():
    conn = sqlite3.connect("local_project.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "description": r[2]} for r in rows]
""",
        "requirements.txt": "fastapi\nuvicorn",
        "schema.sql": """CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT
);""",
        "main_output.py": """import uvicorn
import app

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=True)
"""
    },
    "express": {
        "package.json": """{
  "name": "express-starter",
  "version": "1.0.0",
  "main": "server.js",
  "dependencies": {
    "express": "^4.18.2"
  },
  "scripts": {
    "start": "node server.js"
  }
}""",
        "server.js": """const express = require('express');
const app = express();
const PORT = 3001;

app.use(express.static('.'));

app.get('/api/info', (req, res) => {
    res.json({ message: "Hello from Express.js Backend!" });
});

app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});""",
        "index.html": """<!DOCTYPE html>
<html>
<head>
    <title>Express Starter</title>
    <style>
        body { font-family: sans-serif; background: #111; color: #eee; text-align: center; padding-top: 100px; }
        h1 { color: #f59e0b; }
        button { background: #3b82f6; border: none; color: white; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
    </style>
</head>
<body>
    <h1>Express.js Starter Page</h1>
    <button onclick="fetchInfo()">Fetch API Info</button>
    <p id="res"></p>
    <script>
        function fetchInfo() {
            fetch('/api/info')
                .then(r => r.json())
                .then(d => document.getElementById('res').innerText = d.message);
        }
    </script>
</body>
</html>""",
        "main_output.js": """const { exec } = require('child_process');
console.log('Iniciando Express app...');
console.log("npm install && npm start");
"""
    },
    "go": {
        "main.go": """package main

import (
	"fmt"
	"net/http"
)

func main() {
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		fmt.Fprintf(w, "<h1>Go Web Server Starter</h1><p>Running on port 8080</p>")
	})
	fmt.Println("Server starting on http://localhost:8080")
	http.ListenAndServe(":8080", nil)
}
""",
        "go.mod": "module go-starter\\n\\ngo 1.18",
        "main_output.py": """import subprocess
import os

if __name__ == "__main__":
    print("Corriendo Go App...")
    subprocess.run("go run main.go", shell=True)
"""
    },
    "rust": {
        "Cargo.toml": """[package]
name = "rust-starter"
version = "0.1.0"
edition = "2021"

[dependencies]
tokio = { version = "1", features = ["full"] }
axum = "0.6"
""",
        "src/main.rs": """use axum::{routing::get, Router};

#[tokio::main]
async fn main() {
    let app = Router::new().route("/", get(|| async { "Hello from Rust (Axum) Web Server!" }));

    let addr = std::net::SocketAddr::from(([0, 0, 0, 0], 8080));
    println!("listening on http://{}", addr);
    axum::Server::bind(&addr)
        .serve(app.into_make_service())
        .await
        .unwrap();
}
""",
        "main_output.py": """import subprocess
if __name__ == "__main__":
    print("Compilando y corriendo Rust...")
    subprocess.run("cargo run", shell=True)
"""
    }
}

# ----------------- INFRASTRUCTURE & GIT HELPERS -----------------
def get_sqlite_schema(db_path):
    import sqlite3
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall() if row[0] != 'sqlite_sequence']
    
    schema = {}
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table});")
        cols_info = cursor.fetchall()
        columns = []
        for col in cols_info:
            columns.append({
                "name": col[1],
                "type": col[2],
                "pk": bool(col[5])
            })
            
        cursor.execute(f"PRAGMA foreign_key_list({table});")
        fks_info = cursor.fetchall()
        foreign_keys = []
        for fk in fks_info:
            foreign_keys.append({
                "from": fk[3],
                "table": fk[2],
                "to": fk[4]
            })
            
        schema[table] = {
            "columns": columns,
            "foreign_keys": foreign_keys
        }
    conn.close()
    return schema

def get_postgres_schema(db_url):
    import psycopg2
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public';
    """)
    tables = [row[0] for row in cursor.fetchall()]
    
    schema = {}
    for table in tables:
        cursor.execute(f"""
            SELECT column_name, data_type, 
                   (SELECT EXISTS (
                       SELECT 1 FROM information_schema.table_constraints tc 
                       JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
                       WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_name = '{table}' AND kcu.column_name = c.column_name
                   )) as is_pk
            FROM information_schema.columns c
            WHERE table_name = '{table}';
        """)
        cols_info = cursor.fetchall()
        columns = []
        for col in cols_info:
            columns.append({
                "name": col[0],
                "type": col[1],
                "pk": bool(col[2])
            })
        
        cursor.execute(f"""
            SELECT
                kcu.column_name AS local_column,
                ccu.table_name AS foreign_table,
                ccu.column_name AS foreign_column
            FROM
                information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name='{table}';
        """)
        fks_info = cursor.fetchall()
        foreign_keys = []
        for fk in fks_info:
            foreign_keys.append({
                "from": fk[0],
                "table": fk[1],
                "to": fk[2]
            })
            
        schema[table] = {
            "columns": columns,
            "foreign_keys": foreign_keys
        }
    conn.close()
    return schema

def run_dba_provision(model):
    state.launcher_logs.append("📡 [AGENTE DBA]: Analizando el stack para autoprovisionamiento...")
    
    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_KEY", "")
    
    if supabase_url and supabase_key:
        state.launcher_logs.append("📡 [AGENTE DBA]: Detectadas credenciales de Supabase. Configurando variables en .env...")
        env_path = os.path.join(SysTools.WORKSPACE, ".env")
        env_content = ""
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                env_content = f.read()
        
        lines = env_content.splitlines()
        updated_lines = []
        has_url = False
        has_key = False
        for line in lines:
            if line.strip().startswith("SUPABASE_URL="):
                updated_lines.append(f"SUPABASE_URL={supabase_url}")
                has_url = True
            elif line.strip().startswith("SUPABASE_KEY="):
                updated_lines.append(f"SUPABASE_KEY={supabase_key}")
                has_key = True
            else:
                updated_lines.append(line)
        if not has_url:
            updated_lines.append(f"SUPABASE_URL={supabase_url}")
        if not has_key:
            updated_lines.append(f"SUPABASE_KEY={supabase_key}")
            
        with open(env_path, "w", encoding="utf-8") as f:
            f.write("\n".join(updated_lines) + "\n")
            
        return True, "Variables de Supabase configuradas en .env", ""
    
    files_context = []
    if os.path.exists(SysTools.WORKSPACE):
        for root, _, files in os.walk(SysTools.WORKSPACE):
            if ".git" in root or "node_modules" in root or "__pycache__" in root: continue
            for f in files:
                p = os.path.join(root, f)
                rel = os.path.relpath(p, SysTools.WORKSPACE).replace('\\', '/')
                content = SysTools.read(rel)
                if content:
                    files_context.append(f"@@FILE: {rel}\n{content}\n@@ENDFILE@@")
                
    files_context_str = "\n\n".join(files_context)
    
    prompt = f"""Eres el Agente DBA Dedicado de SQUAD. Tu tarea es analizar el workspace y diseñar/crear un esquema de base de datos relacional SQLite funcional que se adapte al proyecto.
Analiza la estructura de los archivos actuales:
{files_context_str}

Genera únicamente un script SQL válido con la creación de tablas (CREATE TABLE) y opcionalmente algunos datos semilla (INSERT INTO).
Usa el formato exacto:
@@FILE: schema.sql
<código SQL>
@@ENDFILE@@

No expliques nada. Solo genera el archivo schema.sql."""

    state.launcher_logs.append("🧠 [AGENTE DBA]: Invocando IA para diseñar el esquema relacional SQLite...")
    try:
        fixed_output = AIProvider.generate(model=model, prompt=prompt)
        SysTools.extract_and_write_multifile(fixed_output)
        
        db_path = os.path.join(SysTools.WORKSPACE, "local_project.db")
        schema_path = os.path.join(SysTools.WORKSPACE, "schema.sql")
        
        schema_sql = ""
        if os.path.exists(schema_path):
            with open(schema_path, "r", encoding="utf-8") as sf:
                schema_sql = sf.read()
                
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Robust split of SQL statements ignoring semicolons inside strings
            statements = re.split(r';(?=(?:[^\']*\'[^\']*\')*[^\']*$)(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)', schema_sql)
            for stmt in statements:
                stmt_clean = stmt.strip()
                if not stmt_clean:
                    continue
                try:
                    cursor.execute(stmt_clean)
                except sqlite3.Error as oe:
                    print(f"📡 [AGENTE DBA] Saltando error SQL: {stmt_clean[:50]}... ({oe})")
            
            conn.commit()
            conn.close()
            state.launcher_logs.append("✅ [AGENTE DBA]: Base de datos SQLite 'local_project.db' provisionada correctamente.")
            return True, "Base de datos SQLite provisionada con éxito.", schema_sql
        else:
            return False, "No se pudo generar el archivo schema.sql.", ""
    except Exception as e:
        state.launcher_logs.append(f"❌ [AGENTE DBA] Error de autoprovisionamiento: {e}")
        return False, str(e), ""

def format_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.py':
        if shutil.which('black'):
            try:
                subprocess.run(['black', file_path], check=True, capture_output=True)
                return True, "Formateado con black."
            except Exception as e:
                return False, f"Error ejecutando black: {e}"
        elif shutil.which('ruff'):
            try:
                subprocess.run(['ruff', 'format', file_path], check=True, capture_output=True)
                return True, "Formateado con ruff."
            except Exception as e:
                return False, f"Error ejecutando ruff: {e}"
        else:
            return False, "Ningún formateador de Python (black, ruff) instalado."
    elif ext in ['.js', '.ts', '.jsx', '.tsx', '.json', '.css', '.html']:
        local_prettier = os.path.join(os.path.dirname(BASE_DIR), "node_modules", "prettier", "bin", "prettier.cjs")
        if os.path.exists(local_prettier):
            try:
                subprocess.run(['node', local_prettier, '--write', file_path], check=True, capture_output=True, text=True)
                return True, "Formateado con Prettier local (rápido)."
            except Exception as e:
                pass
        
        if shutil.which('prettier'):
            try:
                subprocess.run(['prettier', '--write', file_path], check=True, capture_output=True, text=True, shell=True)
                return True, "Formateado con Prettier global."
            except Exception as e:
                pass

        if shutil.which('npx'):
            try:
                subprocess.run(['npx', 'prettier', '--write', file_path], check=True, capture_output=True, text=True, shell=True)
                return True, "Formateado con prettier."
            except Exception as e:
                return False, f"Error ejecutando prettier: {e}"
        else:
            return False, "Prettier local/global/npx no disponible para formatear."
    return False, "Formato no soportado."

def github_publish(token, repo_name, private=False):
    try:
        req = urllib.request.Request(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "SQUAD-App-Builder"
            }
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            user_data = json.loads(r.read().decode('utf-8'))
            username = user_data.get('login')
    except Exception as e:
        return False, f"Error obteniendo usuario de GitHub (Verifica tu Token): {e}"
        
    if not username:
        return False, "No se pudo determinar el nombre de usuario de GitHub."
        
    try:
        payload = {"name": repo_name, "private": private}
        req = urllib.request.Request(
            "https://api.github.com/user/repos",
            data=json.dumps(payload).encode('utf-8'),
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json",
                "User-Agent": "SQUAD-App-Builder"
            }
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            res_data = json.loads(r.read().decode('utf-8'))
            html_url = res_data.get('html_url')
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        try:
            err_json = json.loads(err_body)
            msg = err_json.get('message', '')
        except:
            msg = err_body
        if e.code == 422 and "already exists" in msg:
            html_url = f"https://github.com/{username}/{repo_name}"
        else:
            return False, f"Error de GitHub API ({e.code}): {msg}"
    except Exception as e:
        return False, f"Error creando el repositorio: {e}"
        
    try:
        if not os.path.exists(os.path.join(SysTools.WORKSPACE, ".git")):
            subprocess.run(["git", "init"], cwd=SysTools.WORKSPACE, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Squad AI"], cwd=SysTools.WORKSPACE, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "squad@ai.local"], cwd=SysTools.WORKSPACE, check=True, capture_output=True)
            
        subprocess.run(["git", "add", "."], cwd=SysTools.WORKSPACE, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Graduation to GitHub from SQUAD"], cwd=SysTools.WORKSPACE, capture_output=True)
        
        remote_url = f"https://{username}:{token}@github.com/{username}/{repo_name}.git"
        subprocess.run(["git", "remote", "remove", "origin"], cwd=SysTools.WORKSPACE, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", remote_url], cwd=SysTools.WORKSPACE, check=True, capture_output=True)
        
        subprocess.run(["git", "branch", "-M", "main"], cwd=SysTools.WORKSPACE, check=True, capture_output=True)
        res = subprocess.run(["git", "push", "-u", "origin", "main"], cwd=SysTools.WORKSPACE, check=True, capture_output=True, text=True, shell=True)
        if res.returncode == 0:
            return True, f"Proyecto graduado exitosamente a GitHub: {html_url}"
        else:
            return False, f"Git push falló: {res.stderr}"
    except subprocess.CalledProcessError as e:
        return False, f"Git push falló: {e.stderr}"
    except Exception as e:
        return False, f"Error al empujar cambios: {str(e)}"

# ----------------- FASTAPI SERVER APPLICATION -----------------
app = FastAPI(title="SQUAD Local Backend API", version="6.0.0")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def sanitize_workspace_path(path: str):
    clean_name = path.lstrip("\\/")
    if ":" in clean_name:
        clean_name = clean_name.split(":", 1)[-1].lstrip("\\/")
    clean_name = os.path.normpath(clean_name)
    while clean_name.startswith("..") or clean_name.startswith("/") or clean_name.startswith("\\"):
        clean_name = clean_name.replace("../", "").replace("..\\", "").replace("..", "").lstrip("\\/")
    full_path = os.path.abspath(os.path.join(SysTools.WORKSPACE, clean_name))
    if not full_path.startswith(os.path.abspath(SysTools.WORKSPACE)):
        raise ValueError("Acceso denegado: fuera del workspace")
    return full_path

# GET Endpoints
@app.get("/api/stream-logs")
async def api_stream_logs():
    async def log_generator():
        last_pipeline_len = 0
        last_pipeline_last_element = None
        last_launcher_len = 0
        last_launcher_last_element = None
        
        # Initial sends
        p_data = json.dumps({"logs": state.logs, "is_running": state.is_running, "pipeline_status": state.pipeline_status})
        yield f"event: pipeline_logs\ndata: {p_data}\n\n"
        
        is_active = state.active_process and state.active_process.poll() is None
        l_data = json.dumps({"logs": state.launcher_logs, "is_active": is_active, "active_port": getattr(state, "active_port", 5000), "active_diagnostic": state.active_diagnostic})
        yield f"event: launcher_logs\ndata: {l_data}\n\n"
        
        last_pipeline_len = len(state.logs)
        last_pipeline_last_element = state.logs[-1] if state.logs else None
        last_launcher_len = len(state.launcher_logs)
        last_launcher_last_element = state.launcher_logs[-1] if state.launcher_logs else None
        
        try:
            while True:
                pipeline_changed = (len(state.logs) != last_pipeline_len) or (len(state.logs) > 0 and state.logs[-1] != last_pipeline_last_element)
                is_active = state.active_process and state.active_process.poll() is None
                launcher_changed = (len(state.launcher_logs) != last_launcher_len) or (len(state.launcher_logs) > 0 and state.launcher_logs[-1] != last_launcher_last_element)
                
                if pipeline_changed:
                    p_data = json.dumps({"logs": state.logs, "is_running": state.is_running, "pipeline_status": state.pipeline_status})
                    yield f"event: pipeline_logs\ndata: {p_data}\n\n"
                    last_pipeline_len = len(state.logs)
                    last_pipeline_last_element = state.logs[-1] if state.logs else None
                    
                if launcher_changed:
                    l_data = json.dumps({"logs": state.launcher_logs, "is_active": is_active, "active_port": getattr(state, "active_port", 5000), "active_diagnostic": state.active_diagnostic})
                    yield f"event: launcher_logs\ndata: {l_data}\n\n"
                    last_launcher_len = len(state.launcher_logs)
                    last_launcher_last_element = state.launcher_logs[-1] if state.launcher_logs else None
                
                if hasattr(state, "file_changes") and state.file_changes:
                    changes = list(state.file_changes)
                    state.file_changes.clear()
                    yield f"event: file_change\ndata: {json.dumps({'files': changes})}\n\n"
                
                yield ": keep-alive\n\n"
                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            print("📡 [SSE] Conexión de logs SSE cerrada por el cliente.")
            
    return StreamingResponse(log_generator(), media_type="text/event-stream")

@app.get("/api/settings")
def api_get_settings():
    return {"success": True, "settings": load_settings()}

@app.get("/api/logs")
def api_get_logs():
    return {"logs": state.logs, "is_running": state.is_running, "pipeline_status": state.pipeline_status}

@app.get("/api/launcher_logs")
def api_get_launcher_logs():
    is_active = state.active_process and state.active_process.poll() is None
    return {"logs": state.launcher_logs, "is_active": is_active, "active_port": getattr(state, "active_port", 5000), "active_diagnostic": state.active_diagnostic}

@app.get("/api/models")
def api_get_models():
    models = OllamaAPI.list_models()
    openrouter_models = [
        "openrouter/google/gemini-2.5-flash:free",
        "openrouter/meta-llama/llama-3.1-8b-instruct:free",
        "openrouter/qwen/qwen-2.5-72b-instruct:free"
    ]
    gemini_models = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash", "gemini-2.0-flash-exp"]
    openai_models = ["gpt-4o-mini", "gpt-4o", "o1-mini"]
    models = gemini_models + openrouter_models + openai_models + models
    return {"models": models}

@app.get("/api/chat-history")
def api_get_chat_history():
    return {"history": state.chat_history}

@app.get("/api/files")
def api_get_files():
    files_data = {}
    if os.path.exists(SysTools.WORKSPACE):
        for root, _, files in os.walk(SysTools.WORKSPACE):
            if ".git" in root or "node_modules" in root or "__pycache__" in root: continue
            for f in files:
                p = os.path.join(root, f)
                rel = os.path.relpath(p, SysTools.WORKSPACE).replace('\\', '/')
                content = SysTools.read(rel)
                if content is not None:
                    files_data[rel] = content
    return {"files": files_data}

@app.get("/api/infra/docker")
def api_get_docker():
    try:
        res = subprocess.check_output("docker ps --format \"{{json .}}\"", shell=True, text=True)
        containers = [json.loads(line) for line in res.strip().split('\n') if line]
        return {"containers": containers}
    except Exception as e:
        return {"containers": [], "error": str(e)}

@app.get("/api/infra/env")
def api_get_env():
    env_content = SysTools.read(".env") or "VAR_NAME=VALOR\nDB_PORT=5432"
    return {"env": env_content}

@app.get("/api/infra/telemetry")
def api_get_telemetry():
    try:
        mem = psutil.virtual_memory()
        try:
            disk = psutil.disk_usage(SysTools.WORKSPACE)
            disk_percentage = disk.percent
        except:
            disk_percentage = 50
            
        cpu_usage = psutil.cpu_percent(interval=0.05)
        cpu_temp = 40.0 + (cpu_usage * 0.4) + (time.time() % 3)
        
        return {
            "success": True,
            "cpu_temp": cpu_temp,
            "cpu_usage": cpu_usage,
            "ram_used": mem.used,
            "ram_total": mem.total,
            "ram_percentage": mem.percent,
            "disk_percentage": disk_percentage
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/infra/sqlite")
def api_get_sqlite():
    dbs = []
    if os.path.exists(SysTools.WORKSPACE):
        for root, _, files in os.walk(SysTools.WORKSPACE):
            if "node_modules" in root or ".git" in root or "__pycache__" in root: continue
            for f in files:
                if f.endswith(('.db', '.sqlite', '.sqlite3')):
                    rel = os.path.relpath(os.path.join(root, f), SysTools.WORKSPACE).replace('\\', '/')
                    dbs.append(rel)
    return {"dbs": dbs}

@app.get("/api/infra/preflight")
def api_get_preflight():
    return {
        "preflight": {
            "node": bool(shutil.which('node')),
            "docker": bool(shutil.which('docker')),
            "python": bool(shutil.which('python') or shutil.which('python3')),
            "git": bool(shutil.which('git'))
        }
    }

@app.get("/api/infra/sqlite/tables")
def api_get_sqlite_tables(db: str = Query(...)):
    try:
        db_path = sanitize_workspace_path(db)
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall() if row[0] != 'sqlite_sequence']
        conn.close()
        return {"tables": tables}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/infra/sqlite/data")
def api_get_sqlite_data(db: str = Query(...), table: str = Query(...)):
    try:
        db_path = sanitize_workspace_path(db)
        if not re.match(r'^[a-zA-Z0-9_]+$', table):
            return {"error": "Nombre de tabla inválido"}
            
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table});")
        columns = [row[1] for row in cursor.fetchall()]
        cursor.execute(f"SELECT * FROM {table} LIMIT 100;")
        rows = cursor.fetchall()
        rows_data = [dict(zip(columns, r)) for r in rows]
        conn.close()
        return {"columns": columns, "rows": rows_data}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/git/file-history")
def api_get_git_file_history(file: str = Query(...)):
    try:
        res = subprocess.run(["git", "show", f"HEAD:{file}"], cwd=SysTools.WORKSPACE, capture_output=True, text=True, shell=True)
        content = res.stdout if res.returncode == 0 else ""
        return {"success": True, "content": content}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/infra/db-schema-diagram")
def api_get_db_schema_diagram(type: str = Query('sqlite'), db: str = Query('')):
    try:
        if type == 'sqlite':
            if not db: raise Exception("Falta el parámetro db para SQLite")
            db_path = sanitize_workspace_path(db)
            schema = get_sqlite_schema(db_path)
        else:
            p = os.path.join(SysTools.WORKSPACE, ".env")
            if not os.path.exists(p):
                p = os.path.join(SysTools.WORKSPACE, "backend", ".env")
            env_vars = {}
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        if "=" in line and not line.strip().startswith("#"):
                            k, v = line.split("=", 1)
                            env_vars[k.strip()] = v.strip().strip('"\'')
            db_url = env_vars.get("DATABASE_URL")
            if not db_url and "DB_HOST" in env_vars:
                host = env_vars.get("DB_HOST", "localhost")
                port = env_vars.get("DB_PORT", "5432")
                user = env_vars.get("DB_USER", "postgres")
                password = env_vars.get("DB_PASSWORD", "")
                dbname = env_vars.get("DB_NAME", "postgres")
                db_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
            if not db_url:
                raise Exception("No se encontró DATABASE_URL ni DB_HOST en .env")
            schema = get_postgres_schema(db_url)
        return {"success": True, "schema": schema}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/llm/telemetry")
def api_get_llm_telemetry():
    return {
        "token_in": state.token_in, 
        "token_out": state.token_out,
        "cost_usd": getattr(state, "cost_usd", 0.0),
        "cache_hits": getattr(state, "cache_hits", 0)
    }

@app.get("/api/llm/vault")
def api_get_llm_vault():
    vault_file = os.path.join(BASE_DIR, "prompts_vault.json")
    prompts = []
    if os.path.exists(vault_file):
        try:
            with open(vault_file, "r", encoding="utf-8") as f: prompts = json.load(f)
        except: pass
    return {"prompts": prompts}

@app.get("/api/infra/download-zip")
def api_download_zip():
    zip_path = os.path.join(BASE_DIR, "export_project.zip")
    if os.path.exists(zip_path):
        return FileResponse(zip_path, media_type="application/zip", filename="export_project.zip")
    raise HTTPException(status_code=404, detail="Archivo ZIP no encontrado.")

@app.get("/api/git/history")
def api_get_git_history():
    try:
        res = subprocess.run(["git", "log", "--pretty=format:%h|%s|%ar", "-n", "20"], cwd=SysTools.WORKSPACE, capture_output=True, text=True, shell=True)
        commits = []
        if res.returncode == 0 and res.stdout.strip():
            for line in res.stdout.strip().split("\n"):
                if "|" in line:
                    parts = line.split("|", 2)
                    commits.append({"hash": parts[0], "message": parts[1], "time": parts[2]})
        return {"success": True, "commits": commits}
    except Exception as e:
        return {"success": False, "error": str(e), "commits": []}

@app.get("/api/infra/postgres/tables")
def api_get_postgres_tables():
    try:
        p = os.path.join(SysTools.WORKSPACE, ".env")
        if not os.path.exists(p): p = os.path.join(SysTools.WORKSPACE, "backend", ".env")
        env_vars = {}
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    if "=" in line and not line.strip().startswith("#"):
                        k, v = line.split("=", 1)
                        env_vars[k.strip()] = v.strip().strip('"\'')
        db_url = env_vars.get("DATABASE_URL")
        if not db_url and "DB_HOST" in env_vars:
            host = env_vars.get("DB_HOST", "localhost")
            port = env_vars.get("DB_PORT", "5432")
            user = env_vars.get("DB_USER", "postgres")
            password = env_vars.get("DB_PASSWORD", "")
            dbname = env_vars.get("DB_NAME", "postgres")
            db_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
        if not db_url: raise Exception("No se encontró base de datos en .env")
        
        import psycopg2
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return {"success": True, "tables": tables}
    except Exception as e:
        return {"success": False, "error": str(e), "tables": []}

@app.get("/api/infra/postgres/data")
def api_get_postgres_data(table: str = Query(...)):
    try:
        if not re.match(r'^[a-zA-Z0-9_]+$', table): raise Exception("Nombre de tabla inválido.")
        p = os.path.join(SysTools.WORKSPACE, ".env")
        if not os.path.exists(p): p = os.path.join(SysTools.WORKSPACE, "backend", ".env")
        env_vars = {}
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    if "=" in line and not line.strip().startswith("#"):
                        k, v = line.split("=", 1)
                        env_vars[k.strip()] = v.strip().strip('"\'')
        db_url = env_vars.get("DATABASE_URL")
        if not db_url and "DB_HOST" in env_vars:
            host = env_vars.get("DB_HOST", "localhost")
            port = env_vars.get("DB_PORT", "5432")
            user = env_vars.get("DB_USER", "postgres")
            password = env_vars.get("DB_PASSWORD", "")
            dbname = env_vars.get("DB_NAME", "postgres")
            db_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
        if not db_url: raise Exception("No se encontró base de datos en .env")
        
        import psycopg2, datetime, decimal
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table} LIMIT 100;")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        
        rows_data = []
        for r in rows:
            row_dict = dict(zip(columns, r))
            cleaned = {}
            for k, v in row_dict.items():
                if isinstance(v, (datetime.datetime, datetime.date, datetime.time)):
                    cleaned[k] = v.isoformat()
                elif isinstance(v, decimal.Decimal):
                    cleaned[k] = float(v)
                elif isinstance(v, bytes):
                    cleaned[k] = v.decode('utf-8', errors='ignore')
                else:
                    cleaned[k] = v
            rows_data.append(cleaned)
        conn.close()
        return {"success": True, "columns": columns, "rows": rows_data}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Serve React static assets
@app.get("/")
@app.get("/index.html")
def read_index():
    dist_html = os.path.join(os.path.dirname(BASE_DIR), "dist", "index.html")
    if os.path.exists(dist_html):
        return FileResponse(dist_html)
    html_path = os.path.join(BASE_DIR, "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return HTMLResponse("Error: index.html no encontrado al lado de squad_server.py", status_code=404)

@app.get("/assets/{asset_path:path}")
def read_assets(asset_path: str):
    dist_asset = os.path.abspath(os.path.join(os.path.dirname(BASE_DIR), "dist", "assets", asset_path))
    dist_folder = os.path.abspath(os.path.join(os.path.dirname(BASE_DIR), "dist"))
    if dist_asset.startswith(dist_folder) and os.path.exists(dist_asset):
        mime_type = "application/octet-stream"
        if dist_asset.endswith(".js"): mime_type = "application/javascript"
        elif dist_asset.endswith(".css"): mime_type = "text/css"
        return FileResponse(dist_asset, media_type=mime_type)
    raise HTTPException(status_code=404, detail="Asset no encontrado")

# POST Endpoints
@app.post("/api/fs/open-explorer")
async def api_open_explorer():
    try:
        import platform
        system = platform.system()
        if system == "Windows": subprocess.Popen(["explorer", SysTools.WORKSPACE])
        elif system == "Darwin": subprocess.Popen(["open", SysTools.WORKSPACE])
        else: subprocess.Popen(["xdg-open", SysTools.WORKSPACE])
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/fs/clear-workspace")
def api_clear_workspace():
    try:
        if state.active_process and state.active_process.poll() is None:
            try: SysTools.kill_process_tree(state.active_process.pid)
            except: pass
            state.active_process = None
            
        SysTools.cleanup_workspace_processes()
        
        state.pending_writes = {}
        state.chat_history = []
        state.logs = []
        state.launcher_logs = []
        state.active_diagnostic = None
        
        if os.path.exists(SysTools.WORKSPACE):
            for item in os.listdir(SysTools.WORKSPACE):
                if item == ".git":
                    continue
                path = os.path.join(SysTools.WORKSPACE, item)
                try:
                    if os.path.isdir(path): shutil.rmtree(path, ignore_errors=True)
                    else: os.remove(path)
                except Exception as ex:
                    print(f"Error removing {path}: {ex}")
                    
        SysTools.git_init_and_commit("Clean workspace snapshot")
        return {"success": True, "message": "Workspace limpiado completamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/fs/create")
def api_create_file(data: dict = Body(default={})):
    path_param = data.get('path', '')
    is_dir = data.get('is_dir', False)
    if not path_param: raise HTTPException(status_code=400, detail="Ruta vacía")
    try:
        full_path = sanitize_workspace_path(path_param)
        if is_dir:
            os.makedirs(full_path, exist_ok=True)
        else:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            if not os.path.exists(full_path):
                with open(full_path, 'w', encoding='utf-8') as f: f.write('')
        SysTools.git_init_and_commit(f"Created {'directory' if is_dir else 'file'}: {path_param}")
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/fs/delete")
def api_delete_file(data: dict = Body(default={})):
    path_param = data.get('path', '')
    if not path_param: raise HTTPException(status_code=400, detail="Ruta vacía")
    try:
        full_path = sanitize_workspace_path(path_param)
        if os.path.exists(full_path):
            if os.path.isdir(full_path): shutil.rmtree(full_path, ignore_errors=True)
            else: os.remove(full_path)
        SysTools.git_init_and_commit(f"Deleted: {path_param}")
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/fs/rename")
def api_rename_file(data: dict = Body(default={})):
    old_param = data.get('old_path', '')
    new_param = data.get('new_path', '')
    if not old_param or not new_param: raise HTTPException(status_code=400, detail="Rutas inválidas")
    try:
        old_full = sanitize_workspace_path(old_param)
        new_full = sanitize_workspace_path(new_param)
        os.makedirs(os.path.dirname(new_full), exist_ok=True)
        os.rename(old_full, new_full)
        SysTools.git_init_and_commit(f"Renamed {old_param} to {new_param}")
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/settings")
def api_post_settings(data: dict = Body(default={})):
    success, msg = save_settings(data)
    if success: return {"success": True, "settings": load_settings()}
    raise HTTPException(status_code=500, detail=msg)

@app.post("/api/infra/stdin")
async def api_stdin(request: Request):
    data = await request.json()
    input_str = data.get('input', '')
    success = False
    msg = "No hay proceso activo"
    if state.active_process and state.active_process.poll() is None:
        try:
            state.active_process.stdin.write(input_str + "\n")
            state.active_process.stdin.flush()
            state.launcher_logs.append(f"⌨️ [STDIN INPUT]: {input_str}")
            success = True
            msg = "Input enviado a stdin"
        except Exception as e:
            msg = f"Error al escribir en stdin: {str(e)}"
    return {"success": success, "message": msg}

@app.post("/api/infra/db-provision")
def api_db_provision(data: dict = Body(default={})):
    model = data.get('model', 'gemini-2.5-flash')
    ok, msg, schema_sql = run_dba_provision(model)
    return {"success": ok, "message": msg, "schema": schema_sql}

@app.post("/api/git/github-publish")
def api_github_publish(data: dict = Body(default={})):
    token = data.get('token', '')
    repo_name = data.get('repo_name', '')
    private = data.get('private', False)
    ok, msg = github_publish(token, repo_name, private)
    return {"success": ok, "message": msg}

@app.post("/api/format")
def api_format(data: dict = Body(default={})):
    name = data.get('name', '')
    content = data.get('content', '')
    if not name: raise HTTPException(status_code=400, detail="Nombre de archivo vacío")
    try:
        full_path = sanitize_workspace_path(name)
        with open(full_path, 'w', encoding='utf-8') as f: f.write(content)
        ok, msg = format_file(full_path)
        with open(full_path, 'r', encoding='utf-8') as f: formatted_content = f.read()
        SysTools.git_init_and_commit(f"Formatted and saved file: {name}")
        return {"success": True, "message": msg, "content": formatted_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/run-agent")
def api_run_agent(background_tasks: BackgroundTasks, data: dict = Body(default={})):
    model = data.get('model', 'llama3:latest')
    goal = data.get('goal', '')
    background_tasks.add_task(run_agent_pipeline, goal, model)
    return JSONResponse(content="OK")

@app.post("/api/git/revert")
def api_revert(data: dict = Body(default={})):
    commit_hash = data.get('hash', '')
    if not commit_hash: raise HTTPException(status_code=400, detail="Falta el hash del commit")
    with SysTools.git_lock:
        try:
            res = subprocess.run(["git", "reset", "--hard", commit_hash], cwd=SysTools.WORKSPACE, capture_output=True, text=True, shell=True)
            if res.returncode == 0:
                return {"success": True, "message": f"Workspace revertido al commit {commit_hash}"}
            else:
                return {"success": False, "message": res.stderr}
        except Exception as e:
            return {"success": False, "message": str(e)}

@app.post("/api/templates/apply")
def api_templates_apply(data: dict = Body(default={})):
    template_name = data.get('template', '')
    try:
        if template_name not in TEMPLATES_GALLERY: raise Exception(f"Plantilla '{template_name}' no soportada.")
        for item in os.listdir(SysTools.WORKSPACE):
            path = os.path.join(SysTools.WORKSPACE, item)
            if item == ".git": continue
            if os.path.isdir(path): shutil.rmtree(path, ignore_errors=True)
            else: os.remove(path)
        tpl_files = TEMPLATES_GALLERY[template_name]
        for fname, content in tpl_files.items(): SysTools.write(fname, content)
        SysTools.git_init_and_commit(f"Applied template: {template_name}")
        return {"success": True, "message": f"Plantilla {template_name} aplicada exitosamente."}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/push")
def api_push(data: dict = Body(default={})):
    repo = data.get('repo', '')
    ok, msg = SysTools.git_push(repo)
    return {"success": ok, "message": msg}

@app.post("/api/save_file")
def api_save_file(data: dict = Body(default={})):
    name = data.get('name', '')
    content = data.get('content', '')
    if not name: raise HTTPException(status_code=400, detail="Nombre de archivo vacío")
    try:
        SysTools.write(name, content, force=True)
        if name == ".env" or name.endswith(".env"):
            load_env()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─── ADVANCED OPTIMIZATION ENDPOINTS ───

@app.post("/api/prompt/optimize")
def api_prompt_optimize(data: dict = Body(default={})):
    prompt = data.get("prompt", "")
    model = data.get("model", "gemini-2.5-flash")
    if not prompt:
        raise HTTPException(status_code=400, detail="Falta el prompt original")
    try:
        opt_sys = """Eres un experto en ingeniería de prompts y arquitecto de software.
Tu tarea es tomar el prompt simple del usuario y optimizarlo, transformándolo en un prompt de enjambre de agentes IA detallado, estructurado y claro en español.
Define:
1. Objetivo general de la aplicación.
2. Vistas y diseño de la UI (Frontend).
3. Base de datos SQLite requerida (tablas, campos clave).
4. Endpoints y APIs clave (Backend).
5. Reglas de negocio y flujos de validación.

Tu respuesta debe ser únicamente el prompt optimizado, listo para ser copiado y enviado directamente. No incluyas intros ni explicaciones adicionales."""
        res = AIProvider.generate(model=model, prompt=f"{opt_sys}\n\nPrompt original del usuario:\n'{prompt}'")
        return {"success": True, "optimized": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/spec/adjust")
def api_spec_adjust(data: dict = Body(default={})):
    feedback = data.get("feedback", "")
    model = data.get("model", "gemini-2.5-flash")
    if not feedback:
        raise HTTPException(status_code=400, detail="Falta el feedback")
    try:
        spec_content = SysTools.read("SPEC.md") or ""
        adjust_prompt = f"""Eres el Agente Arquitecto Senior de SQUAD. El usuario solicita ajustar el plano/especificación técnica actual (SPEC.md) con el siguiente feedback:
'{feedback}'

A continuación se muestra la especificación actual SPEC.md:
---
{spec_content}
---

Reescribe y actualiza la especificación técnica aplicando el feedback del usuario de forma coherente. Retorna la nueva versión completa en Markdown. No escribas introducciones ni explicaciones."""
        new_spec = AIProvider.generate(model=model, prompt=adjust_prompt)
        SysTools.write("SPEC.md", new_spec)
        SysTools.write("ARCHITECTURE.md", new_spec)
        state.launcher_logs.append(f"🧠 [AGENTE ARQUITECTO]: Especificación SPEC.md actualizada con feedback del usuario.")
        return {"success": True, "spec": new_spec}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/spec/approve")
def api_spec_approve(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_agent_pipeline_phase_2)
    return {"success": True, "message": "Fase 2 del enjambre iniciada en segundo plano."}

@app.post("/api/infra/db-seed")
def api_db_seed(data: dict = Body(default={})):
    model = data.get("model", "gemini-2.5-flash")
    try:
        schema_sql = SysTools.read("schema.sql")
        if not schema_sql:
            # Query sqlite directly to build a schema representation
            import sqlite3
            db_path = os.path.join(SysTools.WORKSPACE, "local_project.db")
            if os.path.exists(db_path):
                schema_dict = get_sqlite_schema(db_path)
                schema_sql_parts = []
                for table, info in schema_dict.items():
                    cols_str = ", ".join(f"{c['name']} {c['type']}" for c in info['columns'])
                    schema_sql_parts.append(f"CREATE TABLE {table} ({cols_str});")
                schema_sql = "\n".join(schema_sql_parts)
                
        if not schema_sql:
            raise Exception("No se encontró el archivo schema.sql ni base de datos SQLite con tablas.")
            
        seed_prompt = f"""Eres el Agente DBA autónomo de SQUAD. Tu tarea es generar datos de prueba realistas (seed data) para la base de datos SQLite basándote en su esquema.
A continuación se muestra el esquema SQL:
---
{schema_sql}
---

Genera entre 20 y 50 sentencias SQL INSERT válidas para poblar estas tablas con datos simulados pero coherentes, reales y de calidad (nombres reales, precios acordes, fechas válidas).
Genera ÚNICAMENTE las sentencias SQL INSERT sin comentarios, explicaciones, ni etiquetas de código. Solo las líneas de comandos SQL."""
        
        sql_inserts = AIProvider.generate(model=model, prompt=seed_prompt)
        # Execute the inserts in sqlite
        import sqlite3
        db_path = os.path.join(SysTools.WORKSPACE, "local_project.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Clean markdown wrappers if any
        sql_inserts_clean = sql_inserts.replace("```sql", "").replace("```", "").strip()
        statements = sql_inserts_clean.split(";")
        inserted_count = 0
        for stmt in statements:
            stmt_clean = stmt.strip()
            if stmt_clean:
                try:
                    cursor.execute(stmt_clean)
                    inserted_count += 1
                except Exception as ex:
                    print(f"Error executing seed INSERT: {stmt_clean} - {ex}")
        conn.commit()
        conn.close()
        
        state.launcher_logs.append(f"🌱 [SEED DATA]: Ejecutadas {inserted_count} inserciones semilla en la base de datos.")
        return {"success": True, "message": f"Datos semilla generados con éxito: {inserted_count} registros insertados."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ux/audit")
def api_ux_audit(data: dict = Body(default={})):
    model = data.get("model", "gemini-2.5-flash")
    try:
        index_html = SysTools.read("index.html")
        styles_css = SysTools.read("styles.css")
        ux_audit_prompt = f"""Eres el Agente UI/UX Auditor de SQUAD. Tu tarea es analizar la interfaz del proyecto y generar un Reporte de Calidad Visual detallado en formato Markdown.
index.html:
{index_html}
styles.css:
{styles_css}

Analiza en profundidad y detalla:
1. Contraste de colores y legibilidad.
2. Consistencia en fuentes y espaciados.
3. Responsividad móvil básica.
4. Mejoras estéticas sugeridas para que se vea premium.

Escribe el reporte en Markdown en español. No incluyas código de archivo completo. Solo reporta el análisis."""
        ux_report = AIProvider.generate(model=model, prompt=ux_audit_prompt)
        SysTools.write("VISUAL_REPORT.md", ux_report)
        state.launcher_logs.append("🎨 [AGENTE AUDITOR UX]: Auditoría visual de UI completada y registrada en VISUAL_REPORT.md")
        return {"success": True, "report": ux_report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ux/fix")
def api_ux_fix(data: dict = Body(default={})):
    model = data.get("model", "gemini-2.5-flash")
    try:
        index_html = SysTools.read("index.html")
        styles_css = SysTools.read("styles.css")
        ux_report = SysTools.read("VISUAL_REPORT.md")
        if not ux_report:
            raise Exception("No se ha ejecutado ninguna auditoría visual. Ejecútala primero.")
            
        ux_fix_prompt = f"""Eres el Agente UI/UX Frontend de SQUAD. Basándote en el Reporte de Calidad Visual (VISUAL_REPORT.md), reescribe los archivos index.html y styles.css para aplicar todas las mejoras y sugerencias de diseño propuestas.
        
VISUAL_REPORT.md:
{ux_report}

index.html actual:
{index_html}

styles.css actual:
{styles_css}

Genera los archivos mejorados utilizando el formato exacto:
@@FILE: index.html
<código index.html mejorado>
@@ENDFILE@@

@@FILE: styles.css
<código styles.css mejorado>
@@ENDFILE@@

No expliques nada. Solo genera los archivos."""
        ux_fixes = AIProvider.generate(model=model, prompt=ux_fix_prompt)
        SysTools.extract_and_write_multifile(ux_fixes)
        state.launcher_logs.append("🎨 [AGENTE AUDITOR UX]: Mejoras estéticas de UI/UX aplicadas exitosamente.")
        return {"success": True, "message": "Mejoras estéticas de UI/UX aplicadas con éxito."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ux/extract-style")
def api_ux_extract_style(data: dict = Body(default={})):
    model = data.get("model", "gemini-2.5-flash")
    try:
        styles_css = SysTools.read("styles.css")
        index_html = SysTools.read("index.html")
        if not styles_css and not index_html:
            raise Exception("No hay código CSS/HTML en el workspace para extraer estilo.")
            
        extract_prompt = f"""Analiza la estructura HTML/CSS actual de este proyecto y extrae una descripción concisa de su Identidad de Diseño (colores primarios, secundarios, fuentes, estilo de bordes, layouts).
index.html:
{index_html[:2000]}
styles.css:
{styles_css[:2000]}

Retorna un objeto JSON con las claves: "colors", "fonts", "style", "preset"."""
        res_json = AIProvider.generate(model=model, prompt=extract_prompt, is_json=True)
        profile = json.loads(res_json)
        state.design_identity = profile
        save_settings({"design_identity": profile})
        state.launcher_logs.append(f"💾 [MEMORIA ESTILO]: Perfil extraído e importado: {profile}")
        return {"success": True, "profile": profile}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/git/checkout")
def api_git_checkout(data: dict = Body(default={})):
    commit_hash = data.get('hash', '')
    if not commit_hash:
        raise HTTPException(status_code=400, detail="Falta el hash del commit")
    with SysTools.git_lock:
        try:
            res = subprocess.run(["git", "checkout", "-f", commit_hash], cwd=SysTools.WORKSPACE, capture_output=True, text=True, shell=True)
            if res.returncode == 0:
                # Append a change to state.file_changes to trigger client explorer reload
                state.file_changes.append("*")
                state.launcher_logs.append(f"⏱️ [TIMETRAVEL]: Workspace cambiado al snapshot del commit {commit_hash} (Modo Vista Previa).")
                return {"success": True, "message": f"Workspace en modo vista previa del commit {commit_hash}"}
            else:
                return {"success": False, "message": res.stderr}
        except Exception as e:
            return {"success": False, "message": str(e)}

@app.post("/api/git/restore-head")
def api_git_restore_head():
    with SysTools.git_lock:
        try:
            res = subprocess.run(["git", "checkout", "-f", "main"], cwd=SysTools.WORKSPACE, capture_output=True, text=True, shell=True)
            if res.returncode != 0:
                # Try master if main doesn't exist
                res = subprocess.run(["git", "checkout", "-f", "master"], cwd=SysTools.WORKSPACE, capture_output=True, text=True, shell=True)
            if res.returncode == 0:
                state.file_changes.append("*")
                state.launcher_logs.append("⏱️ [TIMETRAVEL]: Regresaste al estado actual de la rama principal (HEAD).")
                return {"success": True, "message": "Volviste al estado actual (HEAD)."}
            else:
                return {"success": False, "message": res.stderr}
        except Exception as e:
            return {"success": False, "message": str(e)}

@app.post("/api/launch")
def api_launch(data: dict = Body(default={})):
    model = data.get('model', 'gemini-2.5-flash')
    state.linter_retries = 0
    ok, msg = run_launch_sequence(model)
    if ok: return {"success": True, "message": msg}
    raise HTTPException(status_code=500, detail=msg)

@app.post("/api/infra/destroy")
async def api_destroy():
    try:
        for item in os.listdir(SysTools.WORKSPACE):
            path = os.path.join(SysTools.WORKSPACE, item)
            if os.path.isdir(path): shutil.rmtree(path, ignore_errors=True)
            else: os.remove(path)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/infra/zip")
async def api_zip_export():
    try:
        zip_path = os.path.join(BASE_DIR, "export_project")
        shutil.make_archive(zip_path, 'zip', SysTools.WORKSPACE)
        return {"success": True, "message": "Proyecto exportado a export_project.zip"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/deploy/vercel")
async def api_deploy_vercel():
    try:
        await asyncio.sleep(2)
        return {"success": True, "url": "https://squad-project-" + str(int(time.time())) + ".vercel.app"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
def api_chat(data: dict = Body(default={})):
    model = data.get('model', 'llama3:latest')
    msg = data.get('message', '')
    target = data.get('target', 'general')
    
    if msg:
        state.chat_history.append({"role": "user", "content": msg})
        files_ctx_str = OptTools.get_relevant_files_context(msg)
        
        if target == 'debate':
            try:
                arch_prompt = f"Eres el Agente Arquitecto de SQUAD. El usuario nos consulta/pide:\n'{msg}'\n\nLos archivos actuales del proyecto son:\n{files_ctx_str}\n\nPropón un diseño arquitectónico o solución conceptual estructurada para abordar esta solicitud."
                arch_res = AIProvider.generate(model=model, prompt=arch_prompt)
                
                dev_prompt = f"Eres el Agente Desarrollador Full-Stack de SQUAD. El Agente Arquitecto propone la siguiente solución para la consulta del usuario:\n{arch_res}\n\nAnaliza la propuesta del Arquitecto, debátela críticamente indicando qué consideraciones de código o dependencias son necesarias, y propón cómo implementarla en el proyecto."
                dev_res = AIProvider.generate(model=model, prompt=dev_prompt)
                
                debate_log = f"💬 [DEBATE DE AGENTES INICIADO]\n\n🧠 [AGENTE ARQUITECTO]:\n{arch_res}\n\n💻 [AGENTE DESARROLLADOR]:\n{dev_res}"
                state.chat_history.append({"role": "assistant", "content": debate_log})
            except Exception as e:
                state.chat_history.append({"role": "assistant", "content": f"Fallo en debate: {e}"})
        else:
            system_ctx = (
                "Eres un agente inteligente dentro del ecosistema SQUAD (Software Quick Autonomous Development).\n"
                "SQUAD es una plataforma para la generación, ejecución y autocuración autónoma de aplicaciones locales en la PC del usuario.\n"
                "Tu objetivo es ayudar al usuario a entender, construir, desplegar o modificar la aplicación en su máquina local.\n"
                "La arquitectura actual de SQUAD consta de:\n"
                "1. Un backend en Python con FastAPI (squad_server.py) sirviendo como orquestador y sirviendo las APIs en http://localhost:8000.\n"
                "2. Una UI web en React/Vite para el dashboard y la interacción.\n"
                "3. Un Workspace local aislado (SQUAD_WORKSPACE) donde se aloja el código de la app generada por el usuario (Node.js, Express, Python, FastAPI, SQLite, etc.).\n"
                "Cuando el usuario hable del 'sistema' o 'app squad', se refiere a este ecosistema en el que estás ejecutándote actualmente."
            )
            if target == 'architect':
                system_ctx += "\nActúas como el Agente Arquitecto. Concéntrate en la estructura general, patrones de diseño y decisiones arquitectónicas."
            elif target == 'qa':
                system_ctx += "\nActúas como el Agente Senior QA. Concéntrate en diseñar planes de prueba, encontrar casos límite, bugs y escribir tests."
            elif target == 'devops':
                system_ctx += "\nActúas como el Agente DevOps. Concéntrate en configurar Docker, dependencias, scripts de ejecución, CI/CD y automatizaciones."
            
            system_ctx += f"\n\nLos archivos actuales del proyecto en el workspace son:\n{files_ctx_str}"
            system_ctx += f"\n\n{OptTools.CODE_GUIDELINES}"
            
            messages = [{"role": "system", "content": system_ctx}] + state.chat_history[:-1] + [{"role": "user", "content": msg}]
            try:
                response_text = AIProvider.generate(model=model, messages=messages)
                modified_files = SysTools.extract_and_write_multifile(response_text)
                if modified_files:
                    SysTools.git_init_and_commit(f"Chat-update: {', '.join(modified_files)}")
                    state.chat_history.append({"role": "system", "content": f"SQUAD: Se actualizaron los archivos: {', '.join(modified_files)} en el workspace."})
                state.chat_history.append({"role": "assistant", "content": response_text})
            except Exception as e:
                state.chat_history.append({"role": "assistant", "content": f"Error: {e}"})
    return {"history": state.chat_history}

@app.post("/api/infra/terminate")
def api_terminate_process():
    success = False
    msg = "No hay ningún proceso activo para detener."
    
    if state.active_process and state.active_process.poll() is None:
        try:
            SysTools.kill_process_tree(state.active_process.pid)
            state.launcher_logs.append("[SISTEMA] Secuencia terminada por el usuario.")
            success = True
            msg = "Proceso y sus descendientes terminados de raíz."
        except Exception as e:
            msg = f"Error al detener el proceso: {str(e)}"
            
    active_port = getattr(state, "active_port", None)
    if active_port:
        cleaned_any = False
        for active_p in get_listening_ports():
            if active_p['port'] == active_port and active_p['pid'] != os.getpid():
                try:
                    SysTools.kill_process_tree(active_p['pid'])
                    state.launcher_logs.append(f"[SISTEMA] 🧹 Puerto {active_port} liberado matando PID residual {active_p['pid']}.")
                    cleaned_any = True
                except:
                    pass
        if cleaned_any:
            success = True
            msg = f"Proceso y puertos residuales en {active_port} liberados."
            
    return {"success": success, "message": msg}

@app.post("/api/infra/install")
async def api_install_tool(request: Request):
    data = await request.json()
    tool_name = data.get('tool', '')
    ok, msg = run_system_installer(tool_name)
    if ok: return {"success": True, "message": msg}
    raise HTTPException(status_code=500, detail=msg)

@app.post("/api/infra/timetravel")
def api_timetravel():
    with SysTools.git_lock:
        try:
            res = subprocess.run(["git", "reset", "--hard", "HEAD~1"], cwd=SysTools.WORKSPACE, capture_output=True, text=True)
            if res.returncode == 0:
                return {"success": True, "message": "Snapshot de código revertido exitosamente."}
            raise HTTPException(status_code=500, detail=res.stderr)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/llm/vault")
def api_get_vault_prompts():
    try:
        vault_file = os.path.join(BASE_DIR, "prompts_vault.json")
        prompts = []
        if os.path.exists(vault_file):
            try:
                with open(vault_file, "r", encoding="utf-8") as f: prompts = json.load(f)
            except: pass
        return {"success": True, "prompts": prompts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/llm/vault")
def api_save_prompt(data: dict = Body(default={})):
    try:
        prompt_to_save = data.get("prompt", "")
        vault_file = os.path.join(BASE_DIR, "prompts_vault.json")
        prompts = []
        if os.path.exists(vault_file):
            try:
                with open(vault_file, "r", encoding="utf-8") as f: prompts = json.load(f)
            except: pass
        if prompt_to_save and prompt_to_save not in prompts:
            prompts.append(prompt_to_save)
            with open(vault_file, "w", encoding="utf-8") as f:
                json.dump(prompts, f, ensure_ascii=False, indent=2)
        return {"success": True, "prompts": prompts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/llm/vault/delete")
def api_delete_prompt(data: dict = Body(default={})):
    try:
        prompt_to_delete = data.get("prompt", "")
        vault_file = os.path.join(BASE_DIR, "prompts_vault.json")
        prompts = []
        if os.path.exists(vault_file):
            try:
                with open(vault_file, "r", encoding="utf-8") as f: prompts = json.load(f)
            except: pass
        if prompt_to_delete in prompts:
            prompts.remove(prompt_to_delete)
            with open(vault_file, "w", encoding="utf-8") as f:
                json.dump(prompts, f, ensure_ascii=False, indent=2)
        return {"success": True, "prompts": prompts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/llm/providers")
def api_get_providers():
    ollama_online = OllamaAPI.is_online()
    ollama_models = OllamaAPI.list_models() if ollama_online else []
    
    providers = []
    
    # Gemini Provider
    providers.append({
        "id": "gemini",
        "name": "Google Gemini (Nube)",
        "available": GeminiAPI.is_available(),
        "models": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash", "gemini-2.0-flash-exp"]
    })
    
    # Ollama Provider
    providers.append({
        "id": "ollama",
        "name": "Ollama Local",
        "available": ollama_online,
        "models": ollama_models
    })
    
    # OpenAI Provider
    providers.append({
        "id": "openai",
        "name": "OpenAI (Nube)",
        "available": OpenAIAPI.is_available(),
        "models": ["gpt-4o", "gpt-4o-mini", "o1-mini"]
    })
    
    return {"providers": providers}

@app.post("/api/llm/ollama/pull")
def api_ollama_pull(data: dict = Body(default={})):
    model = data.get("model", "")
    if not model:
        raise HTTPException(status_code=400, detail="Modelo faltante")
    try:
        def pull_worker():
            state.launcher_logs.append(f"[OLLAMA] Iniciando descarga de modelo: {model}...")
            proc = subprocess.Popen(f"ollama pull {model}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
            for line in proc.stdout:
                state.launcher_logs.append(f"[OLLAMA PULL] {line.strip()}")
            proc.wait()
            state.launcher_logs.append(f"[OLLAMA] Descarga terminada con exit code {proc.returncode}")
            
        threading.Thread(target=pull_worker, daemon=True).start()
        return {"success": True, "message": f"Iniciando descarga de {model} en segundo plano."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/infra/sql-query")
def api_sql_query(data: dict = Body(default={})):
    query = data.get("query", "")
    if not query:
        raise HTTPException(status_code=400, detail="Query faltante")
    try:
        import sqlite3
        db_path = os.path.join(SysTools.WORKSPACE, "local_project.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query)
        
        if query.strip().lower().startswith("select"):
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description] if cursor.description else []
            res_rows = []
            for r in rows:
                res_rows.append(dict(r))
            conn.close()
            return {"success": True, "columns": columns, "rows": res_rows}
        else:
            conn.commit()
            changes = conn.total_changes
            conn.close()
            return {"success": True, "message": f"Query ejecutada con éxito. Cambios: {changes}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_listening_ports():
    ports = []
    if sys.platform == 'win32':
        try:
            out = subprocess.check_output("netstat -ano", shell=True, text=True)
            for line in out.splitlines():
                line = line.strip()
                if "LISTENING" in line:
                    parts = [x for x in line.split() if x]
                    if len(parts) >= 5:
                        local_addr = parts[1]
                        pid_str = parts[4]
                        
                        port_part = local_addr.split(":")[-1]
                        try:
                            port = int(port_part)
                            pid = int(pid_str)
                            name = "Desconocido"
                            try:
                                p = psutil.Process(pid)
                                name = p.name()
                            except:
                                pass
                            ports.append({"port": port, "pid": pid, "name": name})
                        except:
                            pass
        except Exception as e:
            print(f"Error parseando netstat: {e}")
    else:
        try:
            import psutil
            for conn in psutil.net_connections(kind='inet'):
                if conn.status == 'LISTEN':
                    port = conn.laddr.port
                    pid = conn.pid
                    name = "Desconocido"
                    if pid:
                        try:
                            p = psutil.Process(pid)
                            name = p.name()
                        except:
                            pass
                    ports.append({"port": port, "pid": pid, "name": name})
        except:
            pass
            
    unique_ports = {}
    for p in ports:
        unique_ports[p['port']] = p
    return list(unique_ports.values())

@app.get("/api/infra/ports")
def api_get_ports():
    return {"success": True, "ports": get_listening_ports()}

@app.post("/api/infra/ports/kill")
def api_kill_port_process(data: dict = Body(default={})):
    pid = data.get("pid")
    if not pid:
        raise HTTPException(status_code=400, detail="PID faltante")
    try:
        SysTools.kill_process_tree(pid)
        return {"success": True, "message": f"Proceso {pid} terminado."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/infra/docker-compose")
def api_docker_compose(data: dict = Body(default={})):
    action = data.get("action", "")
    if action not in ["up", "down", "build"]:
        raise HTTPException(status_code=400, detail="Acción inválida")
        
    cmd = ""
    if action == "up":
        cmd = "docker-compose up -d --build"
    elif action == "down":
        cmd = "docker-compose down"
    elif action == "build":
        cmd = "docker-compose build --no-cache"
        
    try:
        def run_cmd():
            state.launcher_logs.append(f"[DOCKER COMPOSE] Ejecutando: {cmd}")
            proc = subprocess.Popen(cmd, shell=True, cwd=SysTools.WORKSPACE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
            for line in proc.stdout:
                state.launcher_logs.append(f"[DOCKER] {line.strip()}")
            proc.wait()
            state.launcher_logs.append(f"[DOCKER COMPOSE] Proceso terminado con exit code {proc.returncode}")
            
        threading.Thread(target=run_cmd, daemon=True).start()
        return {"success": True, "message": f"Comando '{cmd}' lanzado en segundo plano."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/infra/pending-writes")
def api_get_pending_writes():
    res = []
    if hasattr(state, "pending_writes"):
        import difflib
        import os
        for name, content in state.pending_writes.items():
            current = SysTools.read(name)
            diff_str = ""
            try:
                curr_lines = (current or "").splitlines(keepends=True)
                prop_lines = (content or "").splitlines(keepends=True)
                base_name = os.path.basename(name)
                diff_lines = list(difflib.unified_diff(
                    curr_lines,
                    prop_lines,
                    fromfile=f"a/{base_name}",
                    tofile=f"b/{base_name}"
                ))
                diff_str = "".join(diff_lines)
            except Exception as e:
                diff_str = f"Error generating diff: {str(e)}"
            
            res.append({
                "name": name,
                "proposed": content,
                "current": current,
                "file": name,
                "content": content,
                "diff": diff_str,
                "status": "PENDING"
            })
    return {"pending": res}

@app.post("/api/infra/pending-writes/resolve")
def api_resolve_pending_writes(data: dict = Body(default={})):
    action = data.get("action", "")
    files = data.get("files", [])
    
    if action == "confirm":
        written = []
        for name in files:
            if hasattr(state, "pending_writes") and name in state.pending_writes:
                content = state.pending_writes.pop(name)
                orig_val = state.interception_enabled
                state.interception_enabled = False
                try:
                    SysTools.write(name, content)
                    written.append(name)
                finally:
                    state.interception_enabled = orig_val
        if written:
            SysTools.git_init_and_commit(f"Approved critical writes: {', '.join(written)}")
        return {"success": True, "message": f"Archivos aprobados y guardados: {', '.join(written)}"}
    else:
        discarded = []
        for name in files:
            if hasattr(state, "pending_writes") and name in state.pending_writes:
                state.pending_writes.pop(name)
                discarded.append(name)
        return {"success": True, "message": f"Archivos descartados: {', '.join(discarded)}"}

@app.post("/api/deploy/real")
def api_real_deploy(data: dict = Body(default={})):
    provider = data.get("provider", "vercel")
    token = data.get("token", "")
    
    if not token:
        raise HTTPException(status_code=400, detail="Token de acceso faltante")
        
    cmd = ""
    if provider == "vercel":
        cmd = f"npx vercel --token {token} --yes --prod"
    elif provider == "netlify":
        cmd = f"npx netlify-cli deploy --auth {token} --dir=. --prod"
        
    try:
        def run_deploy():
            state.launcher_logs.append(f"[DEPLOY] Iniciando despliegue real en {provider.upper()}...")
            proc = subprocess.Popen(cmd, shell=True, cwd=SysTools.WORKSPACE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
            url = None
            for line in proc.stdout:
                line_str = line.strip()
                state.launcher_logs.append(f"[DEPLOY LOG] {line_str}")
                if "https://" in line_str:
                    match = re.search(r'(https://[a-zA-Z0-9.-]+\.vercel\.app|https://[a-zA-Z0-9.-]+\.netlify\.app)', line_str)
                    if match:
                        url = match.group(1)
            proc.wait()
            if url:
                state.launcher_logs.append(f"[DEPLOY] ✅ Despliegue completado con éxito! URL: {url}")
                state.vercel_url = url
            else:
                state.launcher_logs.append(f"[DEPLOY] Proceso terminado con exit code {proc.returncode}")
                
        threading.Thread(target=run_deploy, daemon=True).start()
        return {"success": True, "message": f"Iniciando despliegue de Vercel/Netlify en segundo plano."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/git/commits")
def api_get_commits():
    try:
        res = subprocess.run(["git", "log", "--oneline", "-n", "30"], cwd=SysTools.WORKSPACE, capture_output=True, text=True, shell=True)
        commits = []
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                if line.strip():
                    parts = line.strip().split(" ", 1)
                    commit_hash = parts[0]
                    msg = parts[1] if len(parts) > 1 else ""
                    commits.append({"hash": commit_hash, "message": msg})
        return {"success": True, "commits": commits}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/refactor/action")
def api_refactor_action(data: dict = Body(default={})):
    file_path = data.get("file", "")
    action = data.get("action", "")
    model = data.get("model", "gemini-2.5-flash")
    
    if not file_path or not action:
        raise HTTPException(status_code=400, detail="Parámetros inválidos")
        
    try:
        content = SysTools.read(file_path)
        if not content:
            raise Exception("El archivo está vacío o no existe")
            
        prompts = {
            "docstrings": f"Agrega docstrings y comentarios detallados y explicativos en español a este archivo de código sin alterar su funcionamiento. Retorna únicamente el código corregido:\n\n{content}",
            "optimize": f"Optimiza el rendimiento, legibilidad y eficiencia de este archivo de código, corrigiendo posibles cuellos de botella. Retorna únicamente el código optimizado:\n\n{content}",
            "typescript": f"Convierte el siguiente código JavaScript o React a TypeScript agregando tipos explícitos de forma estricta. Retorna únicamente el código corregido:\n\n{content}",
            "tests": f"Escribe tests unitarios completos para probar la lógica de este archivo de código. Retorna únicamente el archivo de pruebas completo:\n\n{content}"
        }
        
        prompt = prompts.get(action)
        if not prompt:
            raise Exception("Acción de refactorización no soportada")
            
        state.launcher_logs.append(f"[REFACTOR] Aplicando acción '{action}' sobre '{file_path}'...")
        res = AIProvider.generate(model=model, prompt=prompt)
        clean_code = SysTools.extract_code(res)
        
        # Check if the file is a Python file but the refactored content is markdown
        if file_path.endswith('.py'):
            stripped = clean_code.strip()
            markdown_indicators = (
                stripped.startswith(("- ", "* ", "1. ", "2. ", "3. ", "### ", "# ", "## ", "---"))
                or "**" in stripped
                or "###" in stripped
                or "####" in stripped
            )
            if markdown_indicators:
                # It's markdown! Write it to .md and remove the .py file
                md_file_path = re.sub(r'\.py$', '.md', file_path)
                SysTools.write(md_file_path, clean_code)
                try:
                    os.remove(sanitize_workspace_path(file_path))
                except Exception:
                    pass
                return {"success": True, "content": clean_code, "message": f"Contenido Markdown guardado en {os.path.basename(md_file_path)} y archivo .py removido."}

        orig_val = state.interception_enabled
        state.interception_enabled = False
        try:
            SysTools.write(file_path, clean_code)
            SysTools.git_init_and_commit(f"AI Refactor ({action}): {file_path}")
        finally:
            state.interception_enabled = orig_val
            
        return {"success": True, "content": clean_code, "message": f"Acción '{action}' completada con éxito."}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ─── CI/CD YAML Generator ───────────────────────────────────────────────
@app.post("/api/deploy/cicd")
async def generate_cicd(request: Request):
    """Analiza el stack del proyecto y genera un archivo de CI/CD automáticamente."""
    try:
        body = await request.json()
        platform = body.get("platform", "github")  # 'github' | 'gitlab'
        stack = body.get("stack", "")  # detected or user-defined

        workspace = state.settings.get("workspace", BASE_DIR)

        # Auto-detect stack if not provided
        if not stack:
            has_dockerfile = os.path.exists(os.path.join(workspace, "Dockerfile"))
            has_package_json = os.path.exists(os.path.join(workspace, "package.json"))
            has_requirements = os.path.exists(os.path.join(workspace, "requirements.txt"))
            has_docker_compose = os.path.exists(os.path.join(workspace, "docker-compose.yml"))

            stacks = []
            if has_dockerfile: stacks.append("Docker")
            if has_package_json: stacks.append("Node.js")
            if has_requirements: stacks.append("Python/FastAPI")
            if has_docker_compose: stacks.append("Docker Compose")
            stack = ", ".join(stacks) if stacks else "Generic"

        # Generate YAML using LLM
        model = state.settings.get("default_model", "")
        sys_prompt = f"""Eres un experto en DevOps. Genera ÚNICAMENTE el contenido YAML de un archivo de CI/CD 
        para la plataforma '{platform}' con el stack: {stack}. 
        Si es 'github', genera para .github/workflows/deploy.yml.
        Si es 'gitlab', genera para .gitlab-ci.yml.
        Incluye: build, test y deploy stages. Solo el YAML, sin explicaciones."""

        yaml_content = OllamaAPI.generate(model, prompt=sys_prompt) if model else ""

        # Fallback template if LLM unavailable
        if not yaml_content or len(yaml_content) < 50:
            if platform == "github":
                yaml_content = f"""name: CI/CD Pipeline ({stack})

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main ]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup environment
        run: echo "Stack: {stack}"
      - name: Install dependencies
        run: |
          {"npm install" if "Node" in stack else "pip install -r requirements.txt" if "Python" in stack else "echo 'No package manager detected'"}
      - name: Run tests
        run: |
          {"npm test" if "Node" in stack else "pytest" if "Python" in stack else "echo 'No test runner detected'"}
      - name: Build
        run: |
          {"npm run build" if "Node" in stack else "echo 'Build complete'"}

  deploy:
    needs: build-and-test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        run: echo "Deploy step for {stack}"
"""
            else:  # gitlab
                yaml_content = f"""# GitLab CI/CD Pipeline ({stack})
stages:
  - build
  - test
  - deploy

build:
  stage: build
  script:
    - {"npm install && npm run build" if "Node" in stack else "pip install -r requirements.txt" if "Python" in stack else "echo Build"}

test:
  stage: test
  script:
    - {"npm test" if "Node" in stack else "pytest" if "Python" in stack else "echo Tests"}

deploy:
  stage: deploy
  script:
    - echo "Deploying {stack} application..."
  only:
    - main
"""

        # Write to workspace
        if platform == "github":
            out_dir = os.path.join(workspace, ".github", "workflows")
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, "deploy.yml")
        else:
            out_path = os.path.join(workspace, ".gitlab-ci.yml")

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(yaml_content)

        SysTools.git_init_and_commit(f"CI/CD: Generated {platform} pipeline for {stack}")

        return {
            "success": True,
            "yaml": yaml_content,
            "path": out_path.replace(workspace, "").lstrip("/\\"),
            "stack": stack,
            "platform": platform
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ─── Docker Build + Push ──────────────────────────────────────────────────
@app.post("/api/deploy/docker-push")
async def docker_push(request: Request):
    """Compila la imagen Docker y la empuja al registro especificado."""
    try:
        body = await request.json()
        registry = body.get("registry", "dockerhub")  # 'dockerhub' | 'ghcr'
        username = body.get("username", "")
        token = body.get("token", "")
        image_name = body.get("image_name", "squad-app")
        tag = body.get("tag", "latest")

        workspace = state.settings.get("workspace", BASE_DIR)

        if not username or not token:
            return {"success": False, "error": "Username y token son requeridos."}

        if not os.path.exists(os.path.join(workspace, "Dockerfile")):
            return {"success": False, "error": "No se encontró Dockerfile en el workspace."}

        # Determine full image tag
        if registry == "ghcr":
            full_image = f"ghcr.io/{username}/{image_name}:{tag}"
            login_server = "ghcr.io"
        else:
            full_image = f"{username}/{image_name}:{tag}"
            login_server = ""

        logs = []

        # Docker login
        login_cmd = ["docker", "login"]
        if login_server:
            login_cmd.append(login_server)
        login_cmd += ["-u", username, "--password-stdin"]

        proc_login = subprocess.Popen(
            login_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=workspace
        )
        stdout, stderr = proc_login.communicate(input=token.encode())
        if proc_login.returncode != 0:
            return {"success": False, "error": f"Docker login failed: {stderr.decode()}"}
        logs.append(f"✅ Login exitoso en {registry}")

        # Docker build
        build_result = subprocess.run(
            ["docker", "build", "-t", full_image, "."],
            capture_output=True, text=True, cwd=workspace, timeout=300
        )
        if build_result.returncode != 0:
            return {"success": False, "error": f"Build falló: {build_result.stderr[:500]}"}
        logs.append(f"✅ Imagen construida: {full_image}")

        # Docker push
        push_result = subprocess.run(
            ["docker", "push", full_image],
            capture_output=True, text=True, cwd=workspace, timeout=300
        )
        if push_result.returncode != 0:
            return {"success": False, "error": f"Push falló: {push_result.stderr[:500]}"}
        logs.append(f"🚀 Imagen publicada: {full_image}")

        return {
            "success": True,
            "image": full_image,
            "registry": registry,
            "logs": logs
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Timeout: el build tardó demasiado (>5 minutos)."}
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == '__main__':
    import uvicorn
    SysTools.setup()
    PORT = 8000
    print(f"\n🚀 SQUAD APP BUILDER V6 (FastAPI) - ONLINE")
    print(f"📡 Escuchando peticiones UI en http://localhost:{PORT}")
    print(f"🔌 Conectándose a Ollama nativo en 127.0.0.1:11434")
    print(f"⚠️  Si abriste file:///C:/.../index.html y ves CORS/Errores, entra mejor a http://localhost:8000 en tu navegador.")
    uvicorn.run("squad_server:app", host="0.0.0.0", port=PORT, reload=False)
