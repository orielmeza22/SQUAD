import os
import json
import re
import shlex
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from .sys_tools import SysTools
from ..core.state import state

class ToolCall(BaseModel):
    tool: str
    parameters: Dict[str, Any]

class ToolResult(BaseModel):
    tool: str
    success: bool
    message: str

class ActionExecutor:
    def parse(self, llm_output: str) -> List[ToolCall]:
        # 1. Try pure JSON first
        content = llm_output.strip()
        try:
            data = json.loads(content)
            calls = self._parse_json_data(data)
            if calls:
                return calls
        except Exception:
            pass

        # 2. Try ```json ... ``` blocks next
        blocks = re.findall(r'```(?:json)?\s*(.*?)\s*```', llm_output, re.DOTALL)
        for b in blocks:
            try:
                data = json.loads(b.strip())
                calls = self._parse_json_data(data)
                if calls:
                    return calls
            except Exception:
                pass

        # 3. Fallback: legacy @@FILE: markers
        if any(tag in llm_output for tag in ("@@FILE:", "@@PATCH:", "@@DELETE:")):
            state.launcher_logs.append("⚠️ [DEPRECACIÓN] Salida en formato legacy detectada. Migrando a JSON schemas.")
            files = SysTools._legacy_extract_and_write_multifile(llm_output)
            return [ToolCall(tool="legacy_fallback", parameters={"files": files})]

        # 4. Fallback: markdown code blocks with filename hints
        #    Supports: ```python\n# filename.py, ```html\n<!-- index.html -->, or ```lang:filename
        markdown_calls = self._parse_markdown_blocks(llm_output)
        if markdown_calls:
            state.launcher_logs.append("⚠️ [COMPATIBILIDAD] Salida en formato markdown detectada. El modelo no sigue JSON tool calling.")
            return markdown_calls

        return []

    def _parse_json_data(self, data: Any) -> List[ToolCall]:
        calls = []
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and "tool" in item and "parameters" in item:
                    calls.append(ToolCall(tool=item["tool"], parameters=item["parameters"]))
        elif isinstance(data, dict):
            if "tool" in data and "parameters" in data:
                calls.append(ToolCall(tool=data["tool"], parameters=data["parameters"]))
        return calls

    def _parse_markdown_blocks(self, llm_output: str) -> List[ToolCall]:
        """Extract write_file calls from markdown code blocks with filename hints.
        
        Supports these patterns (common in local models):
        - ```python\n# filename.py
        - ```html\n<!-- filename.html -->
        - ```css\n/* filename.css */
        - ```lang:filename.ext
        - # filename.ext\n```lang
        """
        calls = []
        # Pattern: ```lang:filename or ```lang filename
        named_block = re.findall(
            r'```(?:[a-zA-Z]*[:\s]+)?([\w./\-]+\.(?:py|html|css|js|ts|json|yaml|yml|md|sql|sh|txt))\n([\s\S]*?)```',
            llm_output
        )
        for filename, content in named_block:
            calls.append(ToolCall(tool="write_file", parameters={"path": filename.strip(), "content": content}))

        if calls:
            return calls

        # Pattern: comment with filename on first line of code block
        comment_block = re.finditer(
            r'```[a-zA-Z]*\n'
            r'(?:'
            r'#\s*([\w./\-]+\.(?:py|sql|sh|txt|md))|'
            r'<!--\s*([\w./\-]+\.(?:html|htm|xml))\s*-->|'
            r'/\*\s*([\w./\-]+\.(?:css|js|ts))\s*\*/|'
            r'//\s*([\w./\-]+\.(?:js|ts|json))'
            r')\n'
            r'([\s\S]*?)```',
            llm_output
        )
        for m in comment_block:
            filename = next(g for g in m.groups()[:-1] if g)
            content_with_comment = m.group(0)
            # Strip the ```lang line and the comment line, keep the rest
            lines = content_with_comment.split('\n')
            # lines[0] = ```lang, lines[1] = comment, lines[2:-1] = content, lines[-1] = ```
            content = '\n'.join(lines[2:-1])
            calls.append(ToolCall(tool="write_file", parameters={"path": filename.strip(), "content": content}))

        return calls

    def execute(self, call: ToolCall) -> ToolResult:
        tool = call.tool
        params = call.parameters
        
        if tool == "legacy_fallback":
            return ToolResult(tool=tool, success=True, message=f"Archivos procesados vía fallback legacy: {params.get('files')}")

        path = params.get("path")
        if path:
            clean_path = path.lstrip("\\/")
            # Prevent workspace escape
            if ".." in clean_path or os.path.isabs(path):
                return ToolResult(
                    tool=tool,
                    success=False,
                    message=f"SecurityError: Acceso no permitido fuera del workspace para la ruta '{path}'."
                )

        if tool == "write_file":
            content = params.get("content", "")
            # Pass through SecurityScanner first
            from .security import SecurityScanner
            if path.endswith('.py'):
                findings = SecurityScanner.scan_python_code(content, path)
                for f in findings:
                    if f.severity == "critical":
                        return ToolResult(tool=tool, success=False, message=f"SecurityError: {f.message} (Línea {f.line})")
            elif path.endswith(('.js', '.jsx', '.ts', '.tsx')):
                findings = SecurityScanner.scan_javascript_code(content, path)
                for f in findings:
                    if f.severity == "critical":
                        return ToolResult(tool=tool, success=False, message=f"SecurityError: {f.message} (Línea {f.line})")
            
            try:
                SysTools.write(path, content)
                return ToolResult(tool=tool, success=True, message=f"Archivo '{path}' creado/sobrescrito con éxito.")
            except Exception as e:
                return ToolResult(tool=tool, success=False, message=str(e))

        elif tool == "apply_patch":
            search = params.get("search", "")
            replace = params.get("replace", "")
            try:
                full_path = os.path.join(SysTools.WORKSPACE, path)
                if os.path.exists(full_path):
                    with open(full_path, "r", encoding="utf-8") as f:
                        file_content = f.read()
                    if search not in file_content:
                        return ToolResult(tool=tool, success=False, message=f"Error: Bloque original 'search' no encontrado en '{path}'.")
                    new_content = file_content.replace(search, replace, 1)
                    
                    from .security import SecurityScanner
                    if path.endswith('.py'):
                        findings = SecurityScanner.scan_python_code(new_content, path)
                        for f in findings:
                            if f.severity == "critical":
                                return ToolResult(tool=tool, success=False, message=f"SecurityError: {f.message} (Línea {f.line})")
                    elif path.endswith(('.js', '.jsx', '.ts', '.tsx')):
                        findings = SecurityScanner.scan_javascript_code(new_content, path)
                        for f in findings:
                            if f.severity == "critical":
                                return ToolResult(tool=tool, success=False, message=f"SecurityError: {f.message} (Línea {f.line})")
                
                # Format to SEARCH/REPLACE format expected by apply_patch helper
                patch_str = f"<<<<<<< SEARCH\n{search}\n=======\n{replace}\n>>>>>>> END"
                SysTools.apply_patch(path, patch_str)
                return ToolResult(tool=tool, success=True, message=f"Parche aplicado con éxito sobre '{path}'.")
            except Exception as e:
                return ToolResult(tool=tool, success=False, message=str(e))

        elif tool == "delete_file":
            try:
                full_path = os.path.abspath(os.path.join(SysTools.WORKSPACE, path))
                if full_path.startswith(os.path.abspath(SysTools.WORKSPACE)) and os.path.exists(full_path):
                    os.remove(full_path)
                    return ToolResult(tool=tool, success=True, message=f"Archivo '{path}' eliminado.")
                  
                return ToolResult(tool=tool, success=False, message=f"Archivo '{path}' no existe o está fuera del workspace.")
            except Exception as e:
                return ToolResult(tool=tool, success=False, message=str(e))

        elif tool == "execute_cmd":
            cmd = params.get("cmd", "")
            from .security import SecurityScanner
            import re
            for pattern, reason in SecurityScanner.DANGEROUS_SHELL_PATTERNS:
                if re.search(pattern, cmd):
                    return ToolResult(
                        tool=tool,
                        success=False,
                        message=f"SecurityError: Comando bloqueado: {reason}."
                    )
            cmd_list = shlex.split(cmd)
            try:
                rc, out, err = SysTools.run_command(cmd_list)
                expected = params.get("expected_exit", 0)
                success = (rc == expected)
                msg = f"Comando ejecutado. Código retorno: {rc}. Stdout: {out}. Stderr: {err}."
                return ToolResult(tool=tool, success=success, message=msg)
            except Exception as e:
                return ToolResult(tool=tool, success=False, message=str(e))

        elif tool == "search_memory":
            return ToolResult(tool=tool, success=True, message="Búsqueda en memoria ejecutada (RAG placeholder).")

        return ToolResult(tool=tool, success=False, message=f"Herramienta '{tool}' desconocida.")

    def execute_all(self, llm_output: str) -> List[ToolResult]:
        calls = self.parse(llm_output)
        results = []
        for call in calls:
            results.append(self.execute(call))
        return results
