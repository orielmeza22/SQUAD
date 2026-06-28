from typing import List, Dict, Any

WRITE_FILE_SCHEMA = {
    "name": "write_file",
    "description": "Crea o sobrescribe un archivo en el workspace.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Ruta relativa del archivo a crear/sobrescribir en el workspace."},
            "content": {"type": "string", "description": "Contenido completo del archivo."}
        },
        "required": ["path", "content"]
    }
}

APPLY_PATCH_SCHEMA = {
    "name": "apply_patch",
    "description": "Aplica una edición puntual (patch) reemplazando un bloque de código por otro.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Ruta relativa del archivo a modificar."},
            "search": {"type": "string", "description": "Bloque de código original exacto a buscar."},
            "replace": {"type": "string", "description": "Bloque de código nuevo con las modificaciones."}
        },
        "required": ["path", "search", "replace"]
    }
}

DELETE_FILE_SCHEMA = {
    "name": "delete_file",
    "description": "Elimina un archivo del workspace.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Ruta relativa del archivo a eliminar."}
        },
        "required": ["path"]
    }
}

EXECUTE_CMD_SCHEMA = {
    "name": "execute_cmd",
    "description": "Ejecuta un comando en el sandbox.",
    "parameters": {
        "type": "object",
        "properties": {
            "cmd": {"type": "string", "description": "Comando a ejecutar en el entorno."},
            "expected_exit": {"type": "integer", "description": "Código de retorno esperado (opcional)."}
        },
        "required": ["cmd"]
    }
}

SEARCH_MEMORY_SCHEMA = {
    "name": "search_memory",
    "description": "Busca información relevante en el historial o memoria indexada (RAG placeholder).",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Término o frase a buscar en la memoria."}
        },
        "required": ["query"]
    }
}

AVAILABLE_TOOLS: List[Dict[str, Any]] = [
    WRITE_FILE_SCHEMA,
    APPLY_PATCH_SCHEMA,
    DELETE_FILE_SCHEMA,
    EXECUTE_CMD_SCHEMA,
    SEARCH_MEMORY_SCHEMA
]
