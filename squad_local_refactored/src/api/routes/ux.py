"""UX and visual audit endpoints.

Migrated 1:1 from the legacy monolith.
"""

import json
from fastapi import APIRouter, Body, HTTPException

from ...core.state import state
from ...core.settings_loader import save_settings
from ...tools.sys_tools import SysTools
from ...llm.provider import AIProvider

router = APIRouter()


@router.post("/api/ux/audit")
def api_ux_audit(data: dict = Body(default={})):
    """Analyze the project UI and generate VISUAL_REPORT.md."""
    model = data.get("model", "gemini-2.5-flash")
    try:
        index_html = SysTools.read("index.html") or ""
        styles_css = SysTools.read("styles.css") or ""
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
        ux_report = AIProvider().generate(model=model, prompt=ux_audit_prompt)
        SysTools.write("VISUAL_REPORT.md", ux_report)
        state.launcher_logs.append("🎨 [AGENTE AUDITOR UX]: Auditoría visual de UI completada y registrada en VISUAL_REPORT.md")
        return {"success": True, "report": ux_report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/ux/fix")
def api_ux_fix(data: dict = Body(default={})):
    """Apply the visual recommendations from VISUAL_REPORT.md to HTML/CSS."""
    model = data.get("model", "gemini-2.5-flash")
    try:
        index_html = SysTools.read("index.html") or ""
        styles_css = SysTools.read("styles.css") or ""
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

FORMATO DE SALIDA OBLIGATORIO (JSON):
[
  {{
    "tool": "write_file",
    "parameters": {{
      "path": "index.html",
      "content": "<código index.html mejorado>"
    }}
  }},
  {{
    "tool": "write_file",
    "parameters": {{
      "path": "styles.css",
      "content": "<código styles.css mejorado>"
    }}
  }}
]

No expliques nada. Solo genera el JSON."""

        ux_fixes = AIProvider().generate(model=model, prompt=ux_fix_prompt)
        SysTools.extract_and_write_multifile(ux_fixes)
        state.launcher_logs.append("🎨 [AGENTE AUDITOR UX]: Mejoras estéticas de UI/UX aplicadas exitosamente.")
        return {"success": True, "message": "Mejoras estéticas de UI/UX aplicadas con éxito."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/ux/extract-style")
def api_ux_extract_style(data: dict = Body(default={})):
    """Extract design identity from existing HTML/CSS code and save it."""
    model = data.get("model", "gemini-2.5-flash")
    try:
        styles_css = SysTools.read("styles.css") or ""
        index_html = SysTools.read("index.html") or ""
        if not styles_css and not index_html:
            raise Exception("No hay código CSS/HTML en el workspace para extraer estilo.")

        extract_prompt = f"""Analiza la estructura HTML/CSS actual de este proyecto y extrae una descripción concisa de su Identidad de Diseño (colores primarios, secundarios, fuentes, estilo de bordes, layouts).
index.html:
{index_html[:2000]}
styles.css:
{styles_css[:2000]}

Retorna un objeto JSON con las claves: "colors", "fonts", "style", "preset"."""
        res_json = AIProvider().generate(model=model, prompt=extract_prompt, is_json=True)
        profile = json.loads(res_json)
        state.design_identity = profile
        save_settings({"design_identity": profile})
        state.launcher_logs.append(f"💾 [MEMORIA ESTILO]: Perfil extraído e importado: {profile}")
        return {"success": True, "profile": profile}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
