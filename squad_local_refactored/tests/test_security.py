import pytest
from squad_local_refactored.src.tools.security import SecurityScanner, SecurityFinding

def test_python_eval():
    code = "eval('1+1')"
    findings = SecurityScanner.scan_python_code(code, "test.py")
    assert len(findings) > 0
    assert any(f.severity == "critical" and "eval" in f.pattern for f in findings)

def test_rm_rf_pattern():
    code_py = "# Some comments\nimport os\n# rm -rf /\nos.system('echo Hello')"
    findings_py = SecurityScanner.scan_python_code(code_py, "test.py")
    assert any(f.severity == "critical" and "rm -rf" in f.pattern for f in findings_py)

    code_js = "// Some comment\nconsole.log('hello'); // rm -rf /"
    findings_js = SecurityScanner.scan_javascript_code(code_js, "test.js")
    assert any(f.severity == "critical" and "rm -rf" in f.pattern for f in findings_js)

def test_validate_python_deps():
    reqs = "fastapi==0.100.0\nmalicious-pkg==1.0\nuvicorn>=0.20\n"
    accepted, rejected = SecurityScanner.validate_python_deps(reqs)
    assert "fastapi" in accepted
    assert "uvicorn" in accepted
    assert "malicious-pkg" in rejected

def test_clean_code():
    code = "def hello():\n    print('Hello World')\n"
    findings = SecurityScanner.scan_python_code(code, "test.py")
    assert len(findings) == 0

def test_validate_npm_deps():
    package_json = '{"dependencies": {"express": "^4.18.2", "malicious-npm-pkg": "1.0.0"}}'
    accepted, rejected = SecurityScanner.validate_npm_deps(package_json)
    assert "express" in accepted
    assert "malicious-npm-pkg" in rejected
