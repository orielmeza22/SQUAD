import ast
from typing import Tuple


class TestConsensusValidator:
    @staticmethod
    def validate_test_code(test_code_str: str) -> Tuple[bool, str]:
        """
        Validates the generated QA tests to ensure they are syntactically and structurally correct.
        Returns (success, error_message).
        """
        try:
            tree = ast.parse(test_code_str)
        except SyntaxError as e:
            return False, f"Error de sintaxis en el test: {e.msg} (línea {e.lineno})"

        class TestCodeVisitor(ast.NodeVisitor):
            def __init__(self):
                self.has_tests = False
                self.has_assertions = False

            def visit_FunctionDef(self, node: ast.FunctionDef):
                if node.name.startswith("test_"):
                    self.has_tests = True
                self.generic_visit(node)

            def visit_Assert(self, node: ast.Assert):
                self.has_assertions = True
                self.generic_visit(node)

        visitor = TestCodeVisitor()
        visitor.visit(tree)

        if not visitor.has_tests:
            return (
                False,
                "Consenso de Test rechazado: El archivo de prueba no define ninguna función que empiece con 'test_'."
            )

        if not visitor.has_assertions:
            return (
                False,
                "Consenso de Test rechazado: El archivo de prueba no contiene sentencias 'assert' para verificar resultados."
            )

        return True, ""
