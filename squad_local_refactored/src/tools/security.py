import ast
import re
from typing import List, Tuple, Set
from pydantic import BaseModel

class SecurityFinding(BaseModel):
    filename: str
    line: int
    severity: str  # "critical" | "high" | "medium"
    pattern: str
    message: str

class SecurityScanner:
    DANGEROUS_PYTHON_PATTERNS: List[Tuple[str, str]] = [
        (r"rm\s+-rf", "Uso del comando destructivo rm -rf"),
        (r":\(\)\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", "Bomba Fork detectada"),
        (r"/etc/passwd", "Intento de lectura del archivo de contraseñas /etc/passwd"),
        (r"\.\./\.\.", "Intento de escape del workspace mediante directory traversal"),
    ]

    DANGEROUS_SHELL_PATTERNS: List[Tuple[str, str]] = [
        (r"rm\s+-rf", "Uso del comando destructivo rm -rf"),
        (r":\(\)\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", "Bomba Fork detectada"),
        (r"/etc/passwd", "Intento de lectura del archivo de contraseñas /etc/passwd"),
        (r"\.\./\.\.", "Intento de escape del workspace mediante directory traversal"),
    ]

    PIP_ALLOWLIST: Set[str] = {
        "fastapi", "uvicorn", "pydantic", "jinja2", "flask", "sqlalchemy", 
        "sqlmodel", "requests", "streamlit", "bcrypt", "pyjwt", "pandas", 
        "numpy", "matplotlib", "beautifulsoup4", "pytest"
    }

    NPM_ALLOWLIST: Set[str] = {
        "express", "ejs", "cors", "sqlite3", "better-sqlite3", "axios", 
        "react", "react-dom"
    }

    @staticmethod
    def scan_python_code(content: str, filename: str) -> List[SecurityFinding]:
        findings: List[SecurityFinding] = []

        # 1. Regex scanning
        for line_no, line in enumerate(content.splitlines(), 1):
            for pattern, reason in SecurityScanner.DANGEROUS_PYTHON_PATTERNS:
                m = re.search(pattern, line)
                if m:
                    findings.append(SecurityFinding(
                        filename=filename,
                        line=line_no,
                        severity="critical",
                        pattern=m.group(0),
                        message=f"Patrón crítico detectado por regex: {reason}."
                    ))

        # 2. AST parsing & scanning
        try:
            tree = ast.parse(content, filename=filename)
            class PythonSecurityVisitor(ast.NodeVisitor):
                def __init__(self, fname: str):
                    self.fname = fname

                def visit_Call(self, node: ast.Call):
                    func_name = None
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        parts = []
                        curr = node.func
                        while isinstance(curr, ast.Attribute):
                            parts.append(curr.attr)
                            curr = curr.value
                        if isinstance(curr, ast.Name):
                            parts.append(curr.id)
                        func_name = ".".join(reversed(parts))

                    if func_name in ("eval", "exec", "__import__", "compile"):
                        findings.append(SecurityFinding(
                            filename=self.fname,
                            line=node.lineno,
                            severity="critical",
                            pattern=func_name,
                            message=f"Uso peligroso detectado de la función nativa: '{func_name}'."
                        ))
                    elif func_name == "os.system":
                        findings.append(SecurityFinding(
                            filename=self.fname,
                            line=node.lineno,
                            severity="critical",
                            pattern="os.system",
                            message="Llamada prohibida a os.system."
                        ))
                    elif func_name == "pickle.loads":
                        findings.append(SecurityFinding(
                            filename=self.fname,
                            line=node.lineno,
                            severity="critical",
                            pattern="pickle.loads",
                            message="Deserialización insegura detectada con pickle.loads."
                        ))
                    elif func_name and func_name.startswith("subprocess."):
                        # Check string arguments for dangerous commands
                        for arg in node.args:
                            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                                for pattern, reason in SecurityScanner.DANGEROUS_SHELL_PATTERNS:
                                    if re.search(pattern, arg.value):
                                        findings.append(SecurityFinding(
                                            filename=self.fname,
                                            line=node.lineno,
                                            severity="critical",
                                            pattern=pattern,
                                            message=f"Llamada a subprocess con comando shell peligroso: '{reason}'."
                                        ))
                    self.generic_visit(node)

            visitor = PythonSecurityVisitor(filename)
            visitor.visit(tree)
        except SyntaxError as e:
            findings.append(SecurityFinding(
                filename=filename,
                line=e.lineno or 1,
                severity="critical",
                pattern="SyntaxError",
                message=f"Error de sintaxis detectado: {e.msg}."
            ))
        except Exception:
            pass

        return findings

    @staticmethod
    def scan_javascript_code(content: str, filename: str) -> List[SecurityFinding]:
        findings: List[SecurityFinding] = []

        # 1. Common regex scanning
        for line_no, line in enumerate(content.splitlines(), 1):
            for pattern, reason in SecurityScanner.DANGEROUS_SHELL_PATTERNS:
                m = re.search(pattern, line)
                if m:
                    findings.append(SecurityFinding(
                        filename=filename,
                        line=line_no,
                        severity="critical",
                        pattern=m.group(0),
                        message=f"Patrón crítico detectado por regex: {reason}."
                    ))

        js_patterns = [
            (r"eval\s*\(", "Uso peligroso de eval() en JavaScript", "critical"),
            (r"new\s+Function\s*\(", "Uso de constructor Function inseguro", "critical"),
            (r"child_process\.exec", "Ejecución de subproceso en JS", "critical"),
            (r'require\s*\(\s*["\']child_process["\']\s*\)', "Importación de child_process", "critical"),
            (r"fs\.rm\s*\(", "Remoción de archivos con fs.rm", "high"),
            (r"fs\.unlinkSync\s*\(\s*['\"][/\\]", "Eliminación absoluta de archivos", "high"),
            (r"process\.exit\s*\(", "Terminación forzada del proceso", "medium"),
        ]

        # 2. JS-specific scanning
        for line_no, line in enumerate(content.splitlines(), 1):
            for pattern, reason, severity in js_patterns:
                m = re.search(pattern, line)
                if m:
                    findings.append(SecurityFinding(
                        filename=filename,
                        line=line_no,
                        severity=severity,
                        pattern=m.group(0),
                        message=reason
                    ))
        return findings

    @staticmethod
    def validate_python_deps(requirements_text: str) -> Tuple[List[str], List[str]]:
        accepted = []
        rejected = []
        for line in requirements_text.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            name = re.split(r'==|>=|<=|>|<|;|@', line)[0].strip()
            if name:
                if name.lower() in [pkg.lower() for pkg in SecurityScanner.PIP_ALLOWLIST]:
                    accepted.append(name)
                else:
                    rejected.append(name)
        return accepted, rejected

    @staticmethod
    def validate_npm_deps(package_json_text: str) -> Tuple[List[str], List[str]]:
        import json
        accepted = []
        rejected = []
        try:
            data = json.loads(package_json_text)
            deps = {}
            if "dependencies" in data and isinstance(data["dependencies"], dict):
                deps.update(data["dependencies"])
            if "devDependencies" in data and isinstance(data["devDependencies"], dict):
                deps.update(data["devDependencies"])

            for pkg in deps.keys():
                if pkg.lower() in [p.lower() for p in SecurityScanner.NPM_ALLOWLIST]:
                    accepted.append(pkg)
                else:
                    rejected.append(pkg)
        except Exception:
            pass
        return accepted, rejected
