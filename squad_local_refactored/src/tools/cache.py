"""LLM response caching utilities and code context optimization."""

import json
import hashlib
import threading
import os
from typing import Optional, Tuple, Any, List

from ..core.state import state
from .sys_tools import SysTools


class OptTools:
    """Utilities for caching LLM responses and optimizing code context.

    Features:
    - Thread-safe cache access
    - JSON-based persistent storage
    - Automatic cache key generation
    - Dynamic context window calculation
    - Code pruning for token efficiency
    - Relevant file context retrieval
    """

    CACHE_FILE = "llm_cache.json"
    
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

    _cache_data: Optional[dict] = None
    _cache_lock = threading.Lock()

    @staticmethod
    def load_cache() -> dict:
        """Load cache from disk (thread-safe)."""
        with OptTools._cache_lock:
            if OptTools._cache_data is not None:
                return OptTools._cache_data

            if os.path.exists(OptTools.CACHE_FILE):
                try:
                    with open(OptTools.CACHE_FILE, "r", encoding="utf-8") as f:
                        OptTools._cache_data = json.load(f)
                        return OptTools._cache_data
                except Exception:
                    pass

            OptTools._cache_data = {}
            return OptTools._cache_data

    @staticmethod
    def save_cache(cache: dict) -> None:
        """Save cache to disk (thread-safe)."""
        with OptTools._cache_lock:
            OptTools._cache_data = cache
            try:
                with open(OptTools.CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(cache, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"⚠️ Error saving cache: {e}")

    @staticmethod
    def get_cache(model: str, prompt_or_messages: Any, temp: float) -> Tuple[Optional[str], str]:
        """Retrieve cached response for given parameters."""
        key = hashlib.md5(
            f"{model}:{json.dumps(prompt_or_messages)}:{temp}".encode('utf-8')
        ).hexdigest()
        cache = OptTools.load_cache()
        return cache.get(key), key

    @staticmethod
    def set_cache(key: str, response: str) -> None:
        """Store response in cache."""
        cache = OptTools.load_cache()
        cache[key] = response
        OptTools.save_cache(cache)

    @staticmethod
    def calculate_dynamic_ctx() -> int:
        """Calculate optimal context window based on workspace size."""
        if hasattr(state, "context_window") and state.context_window:
            return state.context_window
            
        total_chars = 0
        if os.path.exists(SysTools.WORKSPACE):
            for root, _, files in os.walk(SysTools.WORKSPACE):
                skip_dirs = {".git", "node_modules", "__pycache__"}
                if any(skip_dir in root for skip_dir in skip_dirs):
                    continue
                for f in files:
                    try:
                        total_chars += os.path.getsize(os.path.join(root, f))
                    except Exception:
                        pass
                        
        est_tokens = (total_chars // 4) + 4000
        
        if est_tokens <= 8192:
            return 8192
        elif est_tokens <= 16384:
            return 16384
        else:
            return min(32768, ((est_tokens + 4095) // 4096) * 4096)

    @staticmethod
    def prune_code_agnostic(code: str, file_path: str) -> str:
        """Prune code to essential structures for token efficiency.
        
        Args:
            code: Source code to prune.
            file_path: File path to determine language.
            
        Returns:
            Pruned code with only essential structures.
        """
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
    def compress_context_headroom(code: str, file_path: str) -> str:
        """Compress code context (inspired by Headroom) to save 60-95% tokens.
        
        Removes comments, blank lines, and docstrings.
        """
        ext = os.path.splitext(file_path)[1].lower()
        lines = code.splitlines()
        compressed = []
        in_block_comment = False
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
                
            # Python compression
            if ext == '.py':
                if stripped.startswith('#') and not any(tag in stripped for tag in ["SQUAD_INJECT", "TODO", "FIXME"]):
                    continue
                if stripped.startswith(('"""', "'''")) and stripped.endswith(('"""', "'''")) and len(stripped) > 3:
                    continue
                if stripped.startswith(('"""', "'''")):
                    in_block_comment = not in_block_comment
                    continue
                if in_block_comment:
                    continue
                
            # JS/TS compression
            elif ext in ('.js', '.ts', '.jsx', '.tsx'):
                if stripped.startswith('//') and not any(tag in stripped for tag in ["SQUAD_INJECT", "TODO", "FIXME"]):
                    continue
                if stripped.startswith('/*'):
                    if '*/' not in stripped:
                        in_block_comment = True
                    continue
                if '*/' in stripped:
                    in_block_comment = False
                    continue
                if in_block_comment:
                    continue
                    
            # CSS/HTML compression
            elif ext in ('.css', '.html', '.ejs'):
                if ext == '.css':
                    if stripped.startswith('/*') and stripped.endswith('*/'):
                        continue
                if ext in ('.html', '.ejs'):
                    if stripped.startswith('<!--') and stripped.endswith('-->'):
                        continue
                        
            compressed.append(line)
            
        return "\n".join(compressed)

    @staticmethod
    def get_relevant_files_context(query: str, max_tokens: int = 15000) -> str:
        """Get context from relevant files based on query.
        
        Args:
            query: Search query to find relevant files.
            max_tokens: Maximum tokens to include.
            
        Returns:
            Concatenated content of relevant files.
        """
        all_files: List[str] = []
        if not os.path.exists(SysTools.WORKSPACE):
            return ""
            
        # Collect all files
        for root, _, files in os.walk(SysTools.WORKSPACE):
            skip_dirs = {".git", "node_modules", "__pycache__"}
            if any(skip_dir in root for skip_dir in skip_dirs):
                continue
            for f in files:
                p = os.path.join(root, f)
                rel = os.path.relpath(p, SysTools.WORKSPACE).replace('\\', '/')
                all_files.append(rel)

        # Check if we can include all files
        total_size = sum(
            os.path.getsize(os.path.join(SysTools.WORKSPACE, f))
            for f in all_files
            if os.path.exists(os.path.join(SysTools.WORKSPACE, f))
        )
        
        if total_size < max_tokens * 3:
            return "\n\n".join(
                f"Archivo: {f}\n{OptTools.compress_context_headroom(SysTools.read(f), f)}"
                for f in all_files
            )

        # Score files by relevance
        words = [w.lower() for w in query.split() if len(w) > 2]
        scores = {}
        for f in all_files:
            try:
                content = SysTools.read(f)
                score = sum(content.lower().count(w) for w in words)
                scores[f] = score
            except Exception:
                scores[f] = 0

        sorted_files = sorted(all_files, key=lambda x: scores[x], reverse=True)
        included_files = []
        current_chars = 0
        max_chars = max_tokens * 4

        for f in sorted_files:
            try:
                content = SysTools.read(f)
                compressed_content = OptTools.compress_context_headroom(content, f)
                file_desc = f"Archivo: {f}\n{compressed_content}"
                
                if current_chars + len(file_desc) > max_chars:
                    pruned_content = OptTools.prune_code_agnostic(compressed_content, f)
                    pruned_desc = f"Archivo: {f} (Poda de Contexto para Ahorro de Tokens)\n{pruned_content}"
                    if current_chars + len(pruned_desc) <= max_chars:
                        included_files.append(pruned_desc)
                        current_chars += len(pruned_desc)
                else:
                    included_files.append(file_desc)
                    current_chars += len(file_desc)
            except Exception:
                continue

        summary = f"Lista de todos los archivos del proyecto: {', '.join(all_files)}\n\n"
        return summary + "\n\n".join(included_files)

    @staticmethod
    def clear_cache() -> None:
        """Clear all cached responses."""
        OptTools.save_cache({})
        print("✅ Caché limpiada.")

    @staticmethod
    def get_cache_stats() -> dict:
        """Get cache statistics."""
        cache = OptTools.load_cache()
        return {
            "size": len(cache),
            "file": os.path.abspath(OptTools.CACHE_FILE)
        }
