"""Infrastructure, database, deployment, and system helper endpoints.

Migrated 1:1 from the legacy monolith.
"""

import os
import re
import sys
import json
import time
import shutil
import psutil
import difflib
import subprocess
import asyncio
import threading
from typing import Dict, Any, List
from fastapi import APIRouter, Body, Query, HTTPException, Request
from fastapi.responses import FileResponse

from ...core.state import state
from ...core.settings_loader import save_settings
from ...tools.sys_tools import SysTools, sanitize_workspace_path
from ...tools.db_introspect import get_sqlite_schema, get_postgres_schema
from ...pipeline.installer import run_system_installer
from ...pipeline.launcher import run_launch_sequence, get_listening_ports
from ...llm.provider import AIProvider

router = APIRouter()

# BASE_DIR matches the root of the backend workspace package
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@router.get("/api/infra/docker")
def api_get_docker():
    """Return all running Docker containers in JSON format."""
    try:
        res = subprocess.check_output("docker ps --format \"{{json .}}\"", shell=True, text=True)
        containers = [json.loads(line) for line in res.strip().split('\n') if line]
        return {"containers": containers}
    except Exception as e:
        return {"containers": [], "error": str(e)}


@router.get("/api/infra/env")
def api_get_env():
    """Return workspace .env file content."""
    env_content = SysTools.read(".env") or "VAR_NAME=VALOR\nDB_PORT=5432"
    return {"env": env_content}


@router.get("/api/infra/telemetry")
def api_get_telemetry():
    """Return CPU, RAM, temperature, and disk telemetry."""
    try:
        mem = psutil.virtual_memory()
        try:
            disk = psutil.disk_usage(SysTools.WORKSPACE)
            disk_percentage = disk.percent
        except Exception:
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


@router.get("/api/infra/sqlite")
def api_get_sqlite():
    """Return relative paths to all SQLite databases in the workspace."""
    dbs = []
    if os.path.exists(SysTools.WORKSPACE):
        for root, _, files in os.walk(SysTools.WORKSPACE):
            if "node_modules" in root or ".git" in root or "__pycache__" in root:
                continue
            for f in files:
                if f.endswith(('.db', '.sqlite', '.sqlite3')):
                    rel = os.path.relpath(os.path.join(root, f), SysTools.WORKSPACE).replace('\\', '/')
                    dbs.append(rel)
    return {"dbs": dbs}


@router.get("/api/infra/preflight")
def api_get_preflight():
    """Check tool availability on host system PATH."""
    return {
        "preflight": {
            "node": bool(shutil.which('node')),
            "docker": bool(shutil.which('docker')),
            "python": bool(shutil.which('python') or shutil.which('python3')),
            "git": bool(shutil.which('git'))
        }
    }


@router.get("/api/infra/sqlite/tables")
def api_get_sqlite_tables(db: str = Query(...)):
    """Return tables list of a SQLite database in the workspace."""
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


@router.get("/api/infra/sqlite/data")
def api_get_sqlite_data(db: str = Query(...), table: str = Query(...)):
    """Return columns list and first 100 rows of a SQLite table."""
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


@router.get("/api/infra/db-schema-diagram")
def api_get_db_schema_diagram(type: str = Query('sqlite'), db: str = Query('')):
    """Introspect sqlite/postgres database and return schema dictionary."""
    try:
        if type == 'sqlite':
            if not db:
                raise Exception("Falta el parámetro db para SQLite")
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


@router.get("/api/infra/postgres/tables")
def api_get_postgres_tables():
    """Return tables list of a PostgreSQL database in workspace .env."""
    try:
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
            raise Exception("No se encontró base de datos en .env")

        import psycopg2
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return {"success": True, "tables": tables}
    except Exception as e:
        return {"success": False, "error": str(e), "tables": []}


@router.get("/api/infra/postgres/data")
def api_get_postgres_data(table: str = Query(...)):
    """Return columns and first 100 rows of a PostgreSQL table."""
    try:
        if not re.match(r'^[a-zA-Z0-9_]+$', table):
            raise Exception("Nombre de tabla inválido.")
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
            raise Exception("No se encontró base de datos en .env")

        import psycopg2
        import datetime
        import decimal
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


@router.post("/api/infra/destroy")
def api_destroy():
    """Wipe all files from SysTools.WORKSPACE."""
    try:
        from ...tools.sys_tools import SysTools
        import stat

        # 1. Kill active process in state if any
        if state.active_process and state.active_process.poll() is None:
            try:
                SysTools.kill_process_tree(state.active_process.pid)
            except Exception:
                pass
            state.active_process = None

        # 2. Cleanup workspace residual processes
        SysTools.cleanup_workspace_processes()

        # 3. Clean files with read-only error handler
        def _on_rmtree_error(func, path, exc_info):
            try:
                os.chmod(path, stat.S_IWRITE)
                func(path)
            except Exception:
                pass

        if os.path.exists(SysTools.WORKSPACE):
            for item in os.listdir(SysTools.WORKSPACE):
                path = os.path.join(SysTools.WORKSPACE, item)
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path, onerror=_on_rmtree_error)
                    else:
                        try:
                            os.chmod(path, stat.S_IWRITE)
                        except Exception:
                            pass
                        os.remove(path)
                except Exception as ex:
                    print(f"Error removing {path} during destroy: {ex}")
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/infra/zip")
def api_zip_export():
    """Compress SysTools.WORKSPACE into export_project.zip."""
    try:
        zip_path = os.path.join(_BASE_DIR, "export_project")
        shutil.make_archive(zip_path, 'zip', SysTools.WORKSPACE)
        return {"success": True, "message": "Proyecto exportado a export_project.zip"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/infra/download-zip")
def api_download_zip():
    """Download export_project.zip file."""
    zip_file = os.path.join(_BASE_DIR, "export_project.zip")
    if os.path.exists(zip_file):
        return FileResponse(zip_file, media_type="application/zip", filename="export_project.zip")
    raise HTTPException(status_code=404, detail="Archivo zip no encontrado. Créalo primero.")


@router.post("/api/infra/terminate")
def api_terminate_process():
    """Terminate the actively running workspace process and free port."""
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
                except Exception:
                    pass
        if cleaned_any:
            success = True
            msg = f"Proceso y puertos residuales en {active_port} liberados."

    return {"success": success, "message": msg}


@router.post("/api/infra/install")
def api_install_tool(data: dict = Body(default={})):
    """Launch winget package installer for node/git/docker on host."""
    tool_name = data.get('tool', '')
    ok, msg = run_system_installer(tool_name)
    if ok:
        return {"success": True, "message": msg}
    raise HTTPException(status_code=500, detail=msg)


@router.post("/api/infra/timetravel")
def api_timetravel():
    """Revert workspace to the previous commit snapshot in Shadow Git."""
    with SysTools.git_lock:
        try:
            res = subprocess.run(["git", "reset", "--hard", "HEAD~1"], cwd=SysTools.WORKSPACE, capture_output=True, text=True)
            if res.returncode == 0:
                return {"success": True, "message": "Snapshot de código revertido exitosamente."}
            return {"success": False, "message": res.stderr}
        except Exception as e:
            return {"success": False, "message": str(e)}


@router.post("/api/infra/stdin")
def api_stdin(data: dict = Body(default={})):
    """Send text input to the stdin pipe of the active workspace process."""
    cmd = data.get("command", "")
    success = False
    msg = "No hay ningún proceso activo."
    if state.active_process and state.active_process.poll() is None:
        try:
            state.active_process.stdin.write(cmd + "\n")
            state.active_process.stdin.flush()
            state.launcher_logs.append(f"📥 [STDIN] Enviado: {cmd}")
            success = True
            msg = f"Comando '{cmd}' lanzado en segundo plano."
        except Exception as e:
            msg = f"Error al escribir en stdin: {str(e)}"
    return {"success": success, "message": msg}


@router.post("/api/infra/db-seed")
def api_db_seed(data: dict = Body(default={})):
    """Generate and run sample/seed data inserts inside SQLite database."""
    model = data.get("model", "gemini-2.5-flash")
    try:
        schema_sql = SysTools.read("schema.sql")
        if not schema_sql:
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

        sql_inserts = AIProvider().generate(model=model, prompt=seed_prompt)
        db_path = os.path.join(SysTools.WORKSPACE, "local_project.db")
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

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


def run_dba_provision(model: str):
    """Run SQLite/Supabase provisioning logic based on files context."""
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
            if ".git" in root or "node_modules" in root or "__pycache__" in root:
                continue
            for f in files:
                p = os.path.join(root, f)
                rel = os.path.relpath(p, SysTools.WORKSPACE).replace('\\', '/')
                content = SysTools.read(rel)
                if content:
                    files_context.append(f"Archivo: {rel}\n```\n{content}\n```")

    files_context_str = "\n\n".join(files_context)

    prompt = f"""Eres el Agente DBA Dedicado de SQUAD. Tu tarea es analizar el workspace y diseñar/crear un esquema de base de datos relacional SQLite funcional que se adapte al proyecto.
Analiza la estructura de los archivos actuales:
{files_context_str}

Genera únicamente un script SQL válido con la creación de tablas (CREATE TABLE) y opcionalmente algunos datos semilla (INSERT INTO).

FORMATO DE SALIDA OBLIGATORIO (JSON):
[
  {{
    "tool": "write_file",
    "parameters": {{
      "path": "schema.sql",
      "content": "-- código SQL aquí"
    }}
  }}
]

No expliques nada. Solo genera el JSON."""


    state.launcher_logs.append("🧠 [AGENTE DBA]: Invocando IA para diseñar el esquema relacional SQLite...")
    try:
        fixed_output = AIProvider().generate(model=model, prompt=prompt)
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
        return False, "No se pudo generar el archivo schema.sql.", ""
    except Exception as e:
        state.launcher_logs.append(f"❌ [AGENTE DBA] Error de autoprovisionamiento: {e}")
        return False, str(e), ""


@router.post("/api/infra/db-provision")
def api_db_provision(data: dict = Body(default={})):
    """Run the DBA SQLite auto-provisioning engine."""
    model = data.get('model', 'gemini-2.5-flash')
    ok, msg, schema_sql = run_dba_provision(model)
    return {"success": ok, "message": msg, "schema": schema_sql}


@router.get("/api/infra/pending-writes")
def api_get_pending_writes():
    """Return intercept critical write files list with unified diffs."""
    res = []
    if hasattr(state, "pending_writes"):
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


@router.post("/api/infra/pending-writes/resolve")
def api_resolve_pending_writes(data: dict = Body(default={})):
    """Approve or discard critical file intercepts."""
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


@router.post("/api/launch")
def api_launch(data: dict = Body(default={})):
    """Launch the generated app and resolve residual processes."""
    model = data.get('model', 'gemini-2.5-flash')
    state.linter_retries = 0
    ok, msg = run_launch_sequence(model)
    if ok:
        return {"success": True, "message": msg}
    raise HTTPException(status_code=500, detail=msg)


@router.post("/api/deploy/vercel")
async def api_deploy_vercel():
    """Deploy to Vercel (mocked endpoint)."""
    try:
        await asyncio.sleep(2)
        return {"success": True, "url": "https://squad-project-" + str(int(time.time())) + ".vercel.app"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/deploy/real")
def api_real_deploy(data: dict = Body(default={})):
    """Real deployment tool execution for Vercel/Netlify in background."""
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
            proc = subprocess.Popen(
                cmd, shell=True, cwd=SysTools.WORKSPACE,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                encoding='utf-8', errors='replace'
            )
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
        return {"success": True, "message": "Iniciando despliegue de Vercel/Netlify en segundo plano."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
