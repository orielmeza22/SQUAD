"""Agent system prompts and prompt builders for the SQUAD swarm.

These are the faithful directives migrated from the legacy monolith
``squad_local/squad_server.py`` (``run_agent_pipeline`` / ``run_agent_pipeline_phase_2``),
preserving the original Spanish wording and the strict portability / self-containment rules.
"""

from typing import Optional

from ..tools.cache import OptTools


SYNTAX_SAFETY_GUIDELINES = """
⚠️ IMPORTANTE: REGLA DE SEGURIDAD DE SINTAXIS E INTEGRIDAD ⚠️
Para evitar errores de sintaxis (SyntaxError, ReferenceError):
1. Asegúrate de cerrar CORRECTAMENTE todos los bloques, llaves ({}), paréntesis (()) y corchetes ([]).
2. NUNCA trunques la generación de código. Escribe el archivo completo o el bloque de reemplazo completo.
3. No utilices placeholders o código elidido (ej. "// el resto del código aquí..."). Todo el código debe estar completo y listo para ejecutarse.
4. En Javascript/Frontend, asegúrate de no usar palabras clave de Node.js (como 'require', 'module.exports') si se ejecuta en navegador, y viceversa (no uses 'document' o 'window' en código backend a menos que sea servido estáticamente al navegador).
5. En Python, verifica que la indentación sea consistente (4 espacios por nivel) y no mezcles tabuladores y espacios.
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
        "REGLA DE SEPARACIÓN ARQUITECTÓNICA: Debes separar de forma explícita y clara en tu SPEC.md los archivos "
        "correspondientes al Frontend (HTML, CSS, JS del cliente) de los del Backend (código del servidor). "
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


def frontend_prompt(plan: str, existing_context: str = "", style_mem_str: str = "") -> str:
    """Phase 2 (parallel) — UI/Frontend agent prompt.

    Generates index.html, styles.css and app.js with strict HTML5 + CDN rules.
    """
    return (
        f"Basado en:\n{plan}\n"
        "Genera únicamente los componentes Frontend / UI, usando Tailwind o CSS puro. "
        "Asegúrate de ser espectacular visualmente. "
        "REGLA CRÍTICA DE HTML: El archivo index.html DEBE ser un HTML5 estándar autocontenido. "
        "PROHIBIDO USAR Jinja2 o sintaxis de template Flask como {{ url_for('static', filename='archivo') }}. "
        "Para CSS y JS usa SIEMPRE rutas relativas simples: "
        "<link rel='stylesheet' href='styles.css'> y <script src='app.js'></script>. "
        "REGLA CRÍTICA DE SEPARACIÓN: Si utilizas estilos CSS personalizados, DEBES escribirlos "
        "obligatoriamente en un bloque ```css separado para generar styles.css. Si usas interactividad "
        "JS del cliente, escríbela obligatoriamente en un bloque ```javascript separado (se guardará como app.js). "
        "Si utilizas clases de Tailwind CSS, DEBES incluir obligatoriamente el script CDN de Tailwind Play "
        "en la cabecera del HTML: <script src='https://cdn.tailwindcss.com'></script>. "
        "NO escribas código Vue SFC ni React JSX en archivos .html sin bundler. Si usas React o Vue, "
        "impórtalos vía CDN. "
        "REGLA DE ENTORNOS (FRONTEND EXCLUSIVO): Todo el código JS generado para el cliente (como app.js) se ejecutará "
        "únicamente en el navegador web del usuario. Está estrictamente prohibido intentar importar librerías de "
        "Node.js/Backend (como express, sqlite3, fs, path, pg) o utilizar variables de entorno del servidor (como "
        "process.env o os.environ). Toda comunicación con el backend debe realizarse mediante llamadas HTTP fetch() "
        "relativas (ej: fetch('/api/turnos')).\n"
        f"{OptTools.CODE_GUIDELINES}\n"
        f"{SYNTAX_SAFETY_GUIDELINES}\n"
        f"{existing_context}{style_mem_str}"
    )


def backend_prompt(plan: str, existing_context: str = "") -> str:
    """Phase 2 — Backend Dev agent prompt.

    Generates business logic / APIs / main_output.{py,js} with portable-DB and dynamic-PORT rules.
    """
    return (
        f"Basado en:\n{plan}\n"
        "El UI ya fue creado. Escribe el Backend/Archivos principales. "
        "REGLAS CRÍTICAS PARA EL BACKEND: "
        "1) Si generas una app Flask, SIEMPRE usa template_folder y static_folder apuntando al directorio "
        "del archivo: "
        "app = Flask(__name__, template_folder=os.path.dirname(os.path.abspath(__file__)), "
        "static_folder=os.path.dirname(os.path.abspath(__file__)), static_url_path='') "
        "2) Para servir index.html usa app.send_static_file('index.html') o send_from_directory(), "
        "NO render_template() a menos que el HTML use Jinja2 correctamente. "
        "3) Si el index.html usa rutas relativas (href='styles.css'), sirve con send_static_file. "
        "4) BASE DE DATOS PORTABLE: Utiliza preferentemente un ORM (como SQLAlchemy o SQLModel para Python, "
        "o Prisma/Drizzle para JS) configurado para SQLite de forma local, facilitando escalar a PostgreSQL "
        "en producción simplemente cambiando DATABASE_URL en el .env. Evita hardcodear sentencias SQL "
        "específicas de motor. "
        "5) PUERTO DINÁMICO: El servidor debe escuchar en el puerto indicado por la variable de entorno PORT "
        "(process.env.PORT para Node.js, os.environ.get('PORT') para Python), utilizando 5000 como valor por "
        "defecto y con debug=False. "
        "6) Asegúrate de IMPORTAR todas las librerías utilizadas (como 'os', 're', 'sys') y DEFINIR o IMPORTAR "
        "todas las funciones y variables auxiliares referenciadas en las rutas (como validaciones de "
        "email/contraseña, cifrado de contraseñas, etc.). El código generado debe ser 100% autoejecutable y "
        "libre de NameError. "
        "7) DEBES definir la ruta raíz @app.route('/') para servir la página principal index.html utilizando "
        "app.send_static_file('index.html') en Python, o res.sendFile(path.join(__dirname, 'index.html')) en "
        "Node.js/Express. "
        "8) Si generas una app Node/Express, SIEMPRE sirve los archivos estáticos desde la raíz del proyecto "
        "(el directorio actual '.'): app.use(express.static(__dirname)) o app.use(express.static('.')). "
        "NO utilices ni crees carpetas como 'public' o 'static'. Todo debe servirse desde la raíz del workspace. "
        "9) INTEGRACIÓN RESILIENTE: Si la aplicación requiere llaves o credenciales para APIs de terceros "
        "(como STRIPE_API_KEY o OPENAI_API_KEY), valídalas: si la variable de entorno está vacía, la app debe "
        "continuar ejecuténdose mostrando un mensaje en consola y utilizando mocks/servicios simulados para "
        "pruebas locales en vez de crashear.\n"
        "10) AUTOCONTENIDO Y SIN IMPORTACIONES HUÉRFANAS: Todo el código backend debe estar en un único archivo "
        "principal autoejecutable (main_output.js para Node.js/Express, o main_output.py para "
        "Python/Flask/FastAPI) que contenga la conexión a base de datos, rutas, middlewares y lógica. "
        "NO intentes importar o requerir archivos locales inexistentes (como ./config, ./routes/auth, etc.). "
        "Si es estrictamente necesario separar el código en múltiples archivos, debes generarlos explícitamente "
        "en bloques @@FILE: separados en la misma respuesta, pero se prefiere fuertemente un único archivo "
        "consolidado para evitar dependencias locales rotas.\n"
        "REGLA DE ENTORNOS (BACKEND EXCLUSIVO): Todo el código generado en esta fase se ejecutará únicamente en el "
        "servidor (Node.js o Python). Está estrictamente prohibido utilizar objetos globales del navegador o interactuar "
        "con el DOM (como 'document', 'window', 'localStorage', 'alert'). Si necesitas enviar respuestas al cliente, "
        "hazlo mediante APIs JSON o sirviendo archivos estáticos completos. El servidor no tiene entorno visual.\n"
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
        "Escribe scripts de Test (Jest, PyTest o genérico) según el stack, "
        "O un pipeline de Github Actions (.github/workflows/main.yml). "
        f"Usa formato @@FILE o @@PATCH\n"
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
