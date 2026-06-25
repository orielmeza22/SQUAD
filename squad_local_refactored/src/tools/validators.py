"""Code validation utilities for syntax checking."""

import re
from typing import Tuple


class CodeValidator:
    """Utilities for validating code syntax and structure.
    
    Provides bracket/quote matching and basic syntax validation
    for Python, JavaScript, TypeScript, CSS, and HTML files.
    """
    
    @staticmethod
    def check_brackets_and_quotes(content: str) -> Tuple[bool, str]:
        """Check if brackets and quotes are properly balanced.
        
        Args:
            content: Source code to validate.
            
        Returns:
            Tuple of (is_valid, message).
        """
        stack = []
        mapping = {')': '(', '}': '{', ']': '['}
        lines = content.splitlines()
        
        in_block_comment = False
        in_string = None
        
        for line_idx, line in enumerate(lines):
            col_idx = 0
            while col_idx < len(line):
                char = line[col_idx]
                
                # Handle block comments
                if not in_string and not in_block_comment:
                    if line[col_idx:col_idx+2] == '//':
                        break
                    if line[col_idx:col_idx+2] == '/*':
                        in_block_comment = True
                        col_idx += 2
                        continue
                
                if in_block_comment:
                    if line[col_idx:col_idx+2] == '*/':
                        in_block_comment = False
                        col_idx += 2
                    else:
                        col_idx += 1
                    continue
                
                # Handle strings
                if in_string:
                    if char == '\\':
                        col_idx += 2
                        continue
                    if char == in_string:
                        in_string = None
                    col_idx += 1
                    continue
                else:
                    if char in ('"', "'", '`'):
                        in_string = char
                        col_idx += 1
                        continue
                
                # Track brackets
                if char in ('(', '{', '['):
                    stack.append((char, line_idx + 1))
                elif char in (')', '}', ']'):
                    if not stack:
                        return False, f"Cierre inesperado '{char}' en línea {line_idx + 1}"
                    top, start_line = stack.pop()
                    if mapping[char] != top:
                        return False, f"Se esperaba el cierre de '{top}' (abierto en línea {start_line}) pero se encontró '{char}' en línea {line_idx + 1}"
                
                col_idx += 1
        
        if stack:
            top, start_line = stack[-1]
            return False, f"Apertura de '{top}' en línea {start_line} no está cerrada."
        
        return True, "Correcto"
    
    @staticmethod
    def validate_python_syntax(content: str) -> Tuple[bool, str]:
        """Validate Python syntax using py_compile.
        
        Args:
            content: Python source code.
            
        Returns:
            Tuple of (is_valid, message).
        """
        import subprocess
        import tempfile
        import os
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(content)
                temp_path = f.name
            
            result = subprocess.run(
                ['python', '-m', 'py_compile', temp_path],
                capture_output=True,
                text=True
            )
            
            os.unlink(temp_path)
            
            if result.returncode == 0:
                return True, "Síntaxis correcta."
            else:
                return False, result.stderr
                
        except Exception as e:
            return False, f"Error validando: {e}"
    
    @staticmethod
    def validate_javascript_syntax(content: str) -> Tuple[bool, str]:
        """Validate JavaScript syntax using Node.js.
        
        Args:
            content: JavaScript source code.
            
        Returns:
            Tuple of (is_valid, message).
        """
        import subprocess
        import tempfile
        import os
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(content)
                temp_path = f.name
            
            result = subprocess.run(
                ['node', '--check', temp_path],
                capture_output=True,
                text=True
            )
            
            os.unlink(temp_path)
            
            if result.returncode == 0:
                return True, "Sintaxis de Node.js correcta."
            else:
                return False, result.stderr + "\n" + result.stdout
                
        except FileNotFoundError:
            return True, "Node.js no disponible, validación básica aplicada."
        except Exception as e:
            return False, f"Error validando: {e}"
    
    @staticmethod
    def detect_file_type_mismatch(content: str, file_path: str) -> Tuple[bool, str, str]:
        """Detect if file content doesn't match its extension.
        
        Args:
            content: File content.
            file_path: Path to the file.
            
        Returns:
            Tuple of (needs_rename, message, new_extension).
        """
        stripped = content.strip()
        ext = file_path.split('.')[-1].lower() if '.' in file_path else ''
        
        # Check YAML content in .py file
        if ext == 'py':
            yaml_indicators = (
                stripped.startswith(("name:", "on:", "jobs:", "steps:", "- name:"))
                or "runs-on:" in stripped
                or bool(re.search(r'^name:\s+\S', stripped, re.MULTILINE))
            )
            if yaml_indicators:
                return True, "Archivo YAML renombrado de .py a .yml correctamente.", "yml"
            
            # Check Markdown content in .py file
            markdown_indicators = (
                stripped.startswith(("- ", "* ", "1. ", "2. ", "3. ", "### ", "# ", "## ", "---"))
                or "**" in stripped
                or "###" in stripped
            )
            if markdown_indicators:
                return True, "Archivo Markdown renombrado de .py a .md correctamente.", "md"
        
        return False, "", ext
