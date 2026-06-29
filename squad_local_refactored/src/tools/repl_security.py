import ast
from .security import SecurityScanner


class REPLSecurityValidator:
    @staticmethod
    def validate_python(code_str: str) -> tuple[bool, str]:
        # 1. Reuse existing SQUAD SecurityScanner python code scanner
        findings = SecurityScanner.scan_python_code(code_str, "<repl_input>")
        critical_findings = [f for f in findings if f.severity in ("critical", "high")]
        if critical_findings:
            return False, f"Bloqueo de seguridad REPL: {critical_findings[0].message}"

        # 2. Advanced AST walk for runtime escapes
        try:
            tree = ast.parse(code_str)
            for node in ast.walk(tree):
                # Block attribute escapes (e.g. sys.exit, os._exit, shutil.rmtree)
                if isinstance(node, ast.Attribute):
                    if node.attr in ("_exit", "exit", "system", "popen", "spawn", "rmtree"):
                        return False, f"Bloqueo de seguridad REPL: Acceso prohibido al atributo '{node.attr}'."
                # Block builtin dynamic executors
                elif isinstance(node, ast.Name):
                    if node.id in ("eval", "exec", "compile", "__import__"):
                        return False, f"Bloqueo de seguridad REPL: Uso prohibido del builtin '{node.id}'."
        except SyntaxError:
            # Let the interactive interpreter capture syntax errors to report line numbers
            pass

        return True, ""

    @staticmethod
    def validate_javascript(code_str: str) -> tuple[bool, str]:
        # Reuse existing JS scanner
        findings = SecurityScanner.scan_javascript_code(code_str, "<repl_input>")
        critical_findings = [f for f in findings if f.severity in ("critical", "high")]
        if critical_findings:
            return False, f"Bloqueo de seguridad REPL (JS): {critical_findings[0].message}"
        return True, ""
