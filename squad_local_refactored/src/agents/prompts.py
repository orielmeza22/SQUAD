"""Agent system prompts and prompt builders for the SQUAD swarm.

These are the faithful directives migrated from the legacy monolith
``squad_local/squad_server.py`` (``run_agent_pipeline`` / ``run_agent_pipeline_phase_2``),
preserving the original Spanish wording and the strict portability / self-containment rules.
"""

from typing import Optional

from ..tools.cache import OptTools
from ..core.templates import FASTAPI_HTMX_TEMPLATE, NODE_EJS_TEMPLATE, PYTHON_STREAMLIT_TEMPLATE


SYNTAX_SAFETY_GUIDELINES = """
⚠️ IMPORTANTE: REGLA DE SEGURIDAD DE SINTAXIS E INTEGRIDAD ⚠️
Para evitar errores de sintaxis (SyntaxError, ReferenceError):
1. Asegúrate de cerrar CORRECTAMENTE todos los bloques, llaves ({}), paréntesis (()) y corchetes ([]).
2. NUNCA trunques la generación de código. Escribe el archivo completo o el bloque de reemplazo completo.
3. No utilices placeholders o código elidido (ej. "// el resto del código aquí..."). Todo el código debe estar completo y listo para ejecutarse.
4. En Javascript/Frontend, asegúrate de no usar palabras clave de Node.js (como 'require', 'module.exports') si se ejecuta en navegador, y viceversa (no uses 'document' o 'window' en código backend a menos que sea servido estáticamente al navegador).
5. En Python, verifica que la indentación sea consistente (4 espacios por nivel) y no mezcles tabuladores y espacios.

🔍 FILTRADO LAZY-SENIOR (YAGNI):
- ¿Esta funcionalidad o función es estrictamente necesaria para cumplir el SPEC? Si no, elimínala y no la programes.
- Prioriza las funciones nativas y la biblioteca estándar del lenguaje sobre la adición de nuevas dependencias externas.
- Escribe la menor cantidad de código posible para lograr el objetivo. Evita sobre-ingeniería, clases accesorias o helpers redundantes.
"""



def architect_prompt(prompt: str, search_ctx: str, preflight: dict, existing_context: str = "") -> str:
    """Phase 1 — Senior Architect agent prompt.

    Designs the technical architecture and software specification (SPEC.md).
    """
    return (
        f"Eres el Agente Arquitecto Senior. El usuario quiere: '{prompt}'. "
        f"Datos técnicos de la web: {search_ctx}.{existing_context}\n\n"
        "⚠️ RESTRICCIÓN DEL SISTEMA ANFITRIÓN ⚠️\n"
        f"Host local: {preflight}. \n"
        "**DISEÑA LA ARQUITECTURA ÚNICAMENTE CON AQUELLAS MARCADAS COMO True.**\n"
        "REGLA DE SELECCIÓN DE STACK (MANDATORIA):\n"
        "Analiza la petición del usuario y selecciona uno de los siguientes 3 stacks tecnológicos para maximizar la fiabilidad:\n"
        "1. FASTAPI_HTMX: Python + FastAPI + HTMX (interactividad vía hx-get/hx-post) + SQLite. Es el STACK POR DEFECTO para dashboards, CRUDs, sistemas de gestión y herramientas de administración. Úsalo siempre a menos que se requiera lo contrario.\n"
        "2. NODE_EJS: Node.js + Express + EJS templates + SQLite. Úsalo si el usuario pide explícitamente una Web App o landing page con JavaScript unificado.\n"
        "3. PYTHON_STREAMLIT: Python + Streamlit + SQLite. Úsalo exclusivamente si el usuario pide visualizaciones de datos pesadas, analíticas o interfaces auto-generadas basadas en datos.\n\n"
        "Debes escribir de forma obligatoria en la primera línea de tu archivo SPEC.md una línea exacta indicando el stack elegido:\n"
        "STACK: [FASTAPI_HTMX | NODE_EJS | PYTHON_STREAMLIT]\n\n"
        "REGLAS ESTRICTAS DE STACK PARA EVITAR BUGS:\n"
        "- Si el stack seleccionado es FASTAPI_HTMX:\n"
        "  * NO generes ni planifiques NUNCA archivos .js para la lógica del servidor, ni package.json, ni node_modules.\n"
        "  * El punto de entrada DEBE ser main_output.py usando uvicorn.\n"
        "  * Todo el frontend (HTML/CSS) debe ser servido por FastAPI.\n"
        "- Si el stack seleccionado es NODE_EJS:\n"
        "  * El punto de entrada DEBE ser server.js.\n"
        "  * Se permite usar package.json y plantillas ejs.\n\n"
        "REGLA DE SEPARACIÓN ARQUITECTÓNICA: Debes separar de forma explícita y clara en tu SPEC.md los archivos "
        "correspondientes al Frontend (HTML, CSS, JS del cliente) de los del Backend (código del servidor) según el stack elegido. "
        "Está prohibido mezclar lógica de base de datos o APIs en archivos del cliente, o código de manipulación "
        "del DOM en archivos del servidor.\n"
        "Crea un plan técnico detallado de la arquitectura y la especificación de la aplicación. "
        "Llámalo Especificación de Software (SPEC). Sé extremadamente detallado."
    )


def dba_prompt(plan: str, existing_context: str = "") -> str:
    """Phase 2 (parallel) — DBA agent prompt.

    Generates a portable SQL schema and a security report.
    """
    return (
        f"Basado en este plan:\n{plan}\n"
        "Genera un esquema SQL estándar portable e independiente (compatible con SQLite y PostgreSQL). "
        "REGLAS ESTRICTAS DE PORTABILIDAD: "
        "1) NO uses cláusulas específicas del motor como CREATE DATABASE o USE. "
        "2) Usa tipos de datos estándar SQL (INTEGER, TEXT, REAL, TIMESTAMP, VARCHAR). "
        "3) Usa CREATE TABLE IF NOT EXISTS. "
        "4) Incluye sentencias INSERT estándar con datos de prueba realistas (al menos 3-5 filas por tabla) "
        "que funcionen tanto en SQLite como en PostgreSQL. "
        "Y adicionalmente, emite un mini reporte de seguridad sobre vulnerabilidades comunes en un archivo "
        "de reporte de seguridad independiente en Markdown utilizando la sintaxis de bloque: "
        "@@FILE: SECURITY_REPORT.md. NO escribas este reporte dentro del archivo de código SQL o Python, "
        "debe ser un archivo de texto independiente. "
        "ANTI-BUG: Asegúrate de que las consultas SQL sean estándar y no contengan comillas invertidas "
        "(backticks) de MySQL.\n"
        f"{OptTools.CODE_GUIDELINES}\n"
        f"{SYNTAX_SAFETY_GUIDELINES}\n"
        f"{existing_context}"
    )


def frontend_prompt(plan: str, existing_context: str = "", style_mem_str: str = "", stack: str = "FASTAPI_HTMX") -> str:
    """Phase 2 (parallel) — UI/Frontend agent prompt.
    
    Generates template views / index.html / styles.css / client JS according to chosen stack.
    """
    if stack == "PYTHON_STREAMLIT":
        return (
            f"Basado en:\n{plan}\n"
            "⚠️ STACK SELECCIONADO: PYTHON_STREAMLIT ⚠️\n"
            "El Agente Frontend NO DEBE generar ningún archivo HTML, CSS o JS, ya que Streamlit auto-genera "
            "la UI directamente desde Python.\n"
            "Escribe únicamente un archivo de documentación temporal indicando que el diseño visual correrá en Streamlit:\n"
            "@@FILE: visual_notes.md\n"
            "El proyecto utiliza Streamlit para la UI. Toda la interactividad visual se define en app.py.\n"
            "@@ENDFILE@@\n\n"
            f"{existing_context}{style_mem_str}"
        )
        
    elif stack == "NODE_EJS":
        return (
            f"Basado en:\n{plan}\n"
            "⚠️ STACK SELECCIONADO: NODE_EJS ⚠️\n"
            "Genera la interfaz frontend usando plantillas EJS para el servidor Express.\n"
            "1) Crea la plantilla HTML principal en: views/index.ejs.\n"
            "2) En index.ejs, puedes usar clases de Tailwind CSS (incluyendo el script CDN en la cabecera: <script src='https://cdn.tailwindcss.com'></script>).\n"
            "3) Si utilizas interactividad JS del cliente (navegador), escribe un bloque javascript separado para public/app.js y enlázalo en el EJS con <script src='/app.js'></script>.\n"
            "4) Si utilizas estilos personalizados, escríbelos en public/styles.css y enlázalos con <link rel='stylesheet' href='/styles.css'>.\n"
            "REGLA DE ENTORNOS (FRONTEND EXCLUSIVO): Todo el código JS para el navegador (como public/app.js) tiene prohibido importar librerías backend de Node o usar bases de datos directamente.\n"
            "REGLA DE FORMATO OBLIGATORIA: Genera tus archivos completos utilizando @@FILE:. Está TOTALMENTE PROHIBIDO usar @@PATCH.\n"
            f"{OptTools.CODE_GUIDELINES}\n"
            f"{SYNTAX_SAFETY_GUIDELINES}\n"
            f"{existing_context}{style_mem_str}"
        )

    else:  # FASTAPI_HTMX (default)
        return (
            f"Basado en:\n{plan}\n"
            "⚠️ STACK SELECCIONADO: FASTAPI_HTMX ⚠️\n"
            "Genera la interfaz de usuario espectacular usando HTML5, CSS y HTMX (para dinamismo sin JS complejo).\n"
            "1) index.html debe ser un HTML5 estándar. DEBES incluir el CDN de HTMX en la cabecera:\n"
            "<script src='https://unpkg.com/htmx.org@2.0.0'></script>\n"
            "Y el CDN de Tailwind CSS:\n"
            "<script src='https://cdn.tailwindcss.com'></script>\n"
            "Y opcionalmente Alpine.js si necesitas interactividad de cliente ligera:\n"
            "<script defer src='https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js'></script>\n"
            "2) Utiliza atributos de HTMX (como hx-get, hx-post, hx-target, hx-swap, hx-trigger) en tus etiquetas HTML "
            "para realizar peticiones AJAX al backend de FastAPI de forma limpia y transparente, actualizando partes "
            "de la página de manera reactiva sin escribir JS de cliente.\n"
            "3) Si requieres estilos personalizados, escríbelos en un archivo styles.css independiente y enlázalo con <link rel='stylesheet' href='styles.css'>.\n"
            "4) Evita escribir archivos Javascript de cliente (como app.js) a menos que sea estrictamente necesario. HTMX y Alpine.js deben resolver el dinamismo.\n"
            "REGLA DE ENTORNOS: Todo el código que se ejecuta en el navegador tiene prohibido acceder a bases de datos o importar librerías backend de servidor.\n"
            "REGLA DE FORMATO OBLIGATORIA: Genera tus archivos completos utilizando @@FILE:. Está TOTALMENTE PROHIBIDO usar @@PATCH.\n"
            f"{OptTools.CODE_GUIDELINES}\n"
            f"{SYNTAX_SAFETY_GUIDELINES}\n"
            f"{existing_context}{style_mem_str}"
        )


def backend_prompt(plan: str, existing_context: str = "", stack: str = "FASTAPI_HTMX") -> str:
    """Phase 2 — Backend Dev agent prompt.

    Generates business logic / APIs / main_output.{py,js} with portable-DB and dynamic-PORT rules.
    """
    if stack == "PYTHON_STREAMLIT":
        return (
            f"Basado en:\n{plan}\n"
            "⚠️ STACK SELECCIONADO: PYTHON_STREAMLIT ⚠️\n"
            "Escribe la lógica del negocio y la interfaz de usuario auto-generada por Streamlit en un único archivo: app.py.\n"
            "REGLAS CRÍTICAS PARA PYTHON_STREAMLIT:\n"
            "1) DEBES basar tu código en la siguiente plantilla inmutable:\n"
            f"{PYTHON_STREAMLIT_TEMPLATE}\n"
            "Rellena los marcadores de inyección (# SQUAD_INJECT_DB_SCHEMA y # SQUAD_INJECT_LOGIC) con tu lógica y genera el archivo completo.\n"
            "2) REGLA DE FORMATO OBLIGATORIA: Genera el archivo app.py completo utilizando la etiqueta @@FILE: app.py. Está TOTALMENTE PROHIBIDO usar @@PATCH.\n"
            f"{OptTools.CODE_GUIDELINES}\n"
            f"{SYNTAX_SAFETY_GUIDELINES}\n"
            f"{existing_context}"
        )

    elif stack == "NODE_EJS":
        return (
            f"Basado en:\n{plan}\n"
            "⚠️ STACK SELECCIONADO: NODE_EJS ⚠️\n"
            "Escribe la lógica del servidor Express y sirve las vistas EJS generadas.\n"
            "REGLAS CRÍTICAS PARA EXPRESS + EJS:\n"
            "1) DEBES basar tu código en la siguiente plantilla inmutable:\n"
            f"{NODE_EJS_TEMPLATE}\n"
            "Rellena los marcadores de inyección (// SQUAD_INJECT_DB_SCHEMA y // SQUAD_INJECT_LOGIC) con tu lógica y genera el archivo completo.\n"
            "2) REGLA DE FORMATO OBLIGATORIA: Genera el archivo server.js completo utilizando la etiqueta @@FILE: server.js. Está TOTALMENTE PROHIBIDO usar @@PATCH.\n"
            f"{OptTools.CODE_GUIDELINES}\n"
            f"{SYNTAX_SAFETY_GUIDELINES}\n"
            f"{existing_context}"
        )

    else:  # FASTAPI_HTMX (default)
        return (
            f"Basado en:\n{plan}\n"
            "⚠️ STACK SELECCIONADO: FASTAPI_HTMX ⚠️\n"
            "Escribe el backend de FastAPI en un único archivo: main_output.py.\n"
            "REGLAS CRÍTICAS PARA FASTAPI + HTMX:\n"
            "1) DEBES basar tu código en la siguiente plantilla inmutable:\n"
            f"{FASTAPI_HTMX_TEMPLATE}\n"
            "Rellena los marcadores de inyección (# SQUAD_INJECT_DB_SCHEMA y # SQUAD_INJECT_LOGIC) con tu lógica y genera el archivo completo.\n"
            "2) REGLA DE FORMATO OBLIGATORIA: Genera el archivo main_output.py completo utilizando la etiqueta @@FILE: main_output.py. Está TOTALMENTE PROHIBIDO usar @@PATCH.\n"
            f"{OptTools.CODE_GUIDELINES}\n"
            f"{SYNTAX_SAFETY_GUIDELINES}\n"
            f"{existing_context}"
        )


def code_review_prompt(plan: str, created_files: list) -> str:
    """Phase 2 — Code Reviewer agent prompt."""
    return (
        f"Revisa los archivos creados ({str(created_files)}) que hacen parte de esto:\n{plan}\n"
        "Señala si hay errores graves, importaciones faltantes, asimetrías de puertos, "
        "o contaminación de entornos (como uso de 'document/window/DOM' en backend, o importaciones de base de datos/require en frontend). "
        "Si encuentras algo crítico, escribe SÍ_CRITICO y qué falló."
    )


def fix_prompt(code_review: str) -> str:
    """Phase 2 — Fix agent prompt (triggered when the reviewer flags critical issues)."""
    return (
        "Corrige estos errores expuestos en el siguiente Code Review:\n"
        f"{code_review}\n"
        f"Genera el código reparado para los archivos necesarios usando formato @@FILE: o @@PATCH:\n"
        f"{SYNTAX_SAFETY_GUIDELINES}"
    )


def ux_audit_prompt(index_html: str, styles_css: str) -> str:
    """Phase 2 — UX Auditor agent prompt."""
    return f"""Eres el Agente UI/UX Auditor de SQUAD. Tu tarea es analizar la interfaz del proyecto y generar un Reporte de Calidad Visual detallado en formato Markdown, y sugerir mejoras.
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


def qa_devops_prompt() -> str:
    """Phase 2 — QA & DevOps agent prompt (tests + CI/CD pipeline)."""
    return (
        "Escribe scripts de Test (pytest para Python/FastAPI/Streamlit, o Jest para Node/EJS) según el stack tecnológico elegido, "
        "O un pipeline de Github Actions (.github/workflows/main.yml).\n"
        "REGLA CRÍTICA DE EJECUCIÓN:\n"
        "- Si el stack en SPEC.md es FASTAPI_HTMX o PYTHON_STREAMLIT: Genera pruebas y pipelines basados estrictamente en Python (pytest). Ignora por completo npm o node.\n"
        "- Si el stack es NODE_EJS: Genera pruebas y pipelines basados en Node (Jest/npm).\n"
        "Usa formato @@FILE o @@PATCH\n"
        f"{SYNTAX_SAFETY_GUIDELINES}"
    )


def linter_prompt(error_summary: str, files_context: str) -> str:
    """Autonomous linter prompt (self-healing from runtime/syntax errors)."""
    return (
        "Eres el Agente LINTER AUTÓNOMO de SQUAD. Se produjeron los siguientes errores:\n\n"
        f"{error_summary}\n\n"
        "Corrige los archivos afectados para resolver TODOS los errores. "
        "Genera el código reparado usando el formato @@FILE: para archivos completos o @@PATCH: para "
        "ediciones incrementales (<<<<<<< SEARCH / ======= / >>>>>>> END).\n\n"
        f"Contexto actual de los archivos del proyecto:\n{files_context}\n"
        "NO expliques, solo entrega los archivos corregidos."
    )


def style_memory_str(design_identity: Optional[dict]) -> str:
    """Render the design-identity constraint string used by the frontend agent."""
    if not design_identity:
        return ""
    return (
        "\n\nIDENTIDAD DE DISEÑO REQUERIDA:\n"
        f"- Colores: {design_identity.get('colors')}\n"
        f"- Tipografías: {design_identity.get('fonts')}\n"
        f"- Estilo visual: {design_identity.get('style')} (Preset: {design_identity.get('preset')})\n"
        "Debes ceñirte a esta identidad visual."
    )
