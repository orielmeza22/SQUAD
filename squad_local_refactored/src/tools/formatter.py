"""Code formatter (black / ruff / prettier).

Migrated 1:1 from the legacy monolith ``format_file``.
"""

import os
import shutil
import subprocess
from typing import Tuple

from ..core.config import settings


def format_file(file_path: str) -> Tuple[bool, str]:
    """Format a file with the appropriate formatter based on its extension.

    Args:
        file_path: Absolute path to the file.

    Returns:
        Tuple of (success, message).
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.py':
        if shutil.which('black'):
            try:
                subprocess.run(['black', file_path], check=True, capture_output=True)
                return True, "Formateado con black."
            except Exception as e:
                return False, f"Error ejecutando black: {e}"
        elif shutil.which('ruff'):
            try:
                subprocess.run(['ruff', 'format', file_path], check=True, capture_output=True)
                return True, "Formateado con ruff."
            except Exception as e:
                return False, f"Error ejecutando ruff: {e}"
        else:
            return False, "Ningún formateador de Python (black, ruff) instalado."
    elif ext in ['.js', '.ts', '.jsx', '.tsx', '.json', '.css', '.html']:
        local_prettier = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
            "node_modules", "prettier", "bin", "prettier.cjs"
        )
        if os.path.exists(local_prettier):
            try:
                subprocess.run(['node', local_prettier, '--write', file_path], check=True, capture_output=True, text=True)
                return True, "Formateado con Prettier local (rápido)."
            except Exception:
                pass

        if shutil.which('prettier'):
            try:
                subprocess.run(['prettier', '--write', file_path], check=True, capture_output=True, text=True, shell=True)
                return True, "Formateado con Prettier global."
            except Exception:
                pass

        if shutil.which('npx'):
            try:
                subprocess.run(['npx', 'prettier', '--write', file_path], check=True, capture_output=True, text=True, shell=True)
                return True, "Formateado con prettier."
            except Exception as e:
                return False, f"Error ejecutando prettier: {e}"
        else:
            return False, "Prettier local/global/npx no disponible para formatear."
    return False, "Formato no soportado."
