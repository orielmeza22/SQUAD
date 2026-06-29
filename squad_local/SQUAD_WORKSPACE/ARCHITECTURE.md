STACK: FASTAPI_HTMX

# Especificación de Software (SPEC)

## Resumen del Proyecto
El objetivo principal es crear un sistema de API utilizando el stack FASTAPI_HTMX, que incluye Python, FastAPI y HTMX para interactividad vía hx-get/hx-post. El sistema se basará en SQLite como base de datos.

## Arquitectura del Sistema

### Backend
- **Punto de Entrada**: main_output.py
  - Usar `uvicorn` para ejecutar el servidor.
  
### Frontend
- **HTML/CSS/JS**: Servido por FastAPI, no se generará código frontend independiente.

## Estructura del Proyecto

### Backend (main_output.py)
```plaintext
├── main_output.py
└── db.sqlite3  # Base de datos SQLite
```

### Frontend (Servido por FastAPI)
- No hay archivos frontend específicos, todo el frontend será generado dinámicamente por FastAPI.

## Estructura del Backend

### Endpoints y Rutas
1. **Ruta para Crear un Nuevo Registro**
   - Método: POST
   - URL: `/api/crear`
   - Input: JSON con los datos necesarios.
   - Output: JSON con el ID del nuevo registro o un mensaje de error.

2. **Ruta para Obtener Todos los Registros**
   - Método: GET
   - URL: `/api/listar`
   - Input: Ninguno.
   - Output: JSON con una lista de todos los registros.

3. **Ruta para Obtener Un Registro por ID**
   - Método: GET
   - URL: `/api/obtener/<id>`
   - Input: ID del registro.
   - Output: JSON con el registro correspondiente o un mensaje de error si no existe.

4. **Ruta para Actualizar un Registro**
   - Método: PUT
   - URL: `/api/actualizar/<id>`
   - Input: JSON con los datos actualizados y el ID del registro.
   - Output: JSON con un mensaje de éxito o un mensaje de error.

5. **Ruta para Eliminar Un Registro**
   - Método: DELETE
   - URL: `/api/eliminar/<id>`
   - Input: ID del registro.
   - Output: JSON con un mensaje de éxito o un mensaje de error si no existe el registro.

## Estructura de la Base de Datos (SQLite)

### Tablas

1. **Tabla `registros`**
   ```plaintext
   CREATE TABLE registros (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       nombre TEXT NOT NULL,
       edad INTEGER NOT NULL,
       email TEXT UNIQUE NOT NULL
   );
   ```

## Documentación y Descripción de Endpoints

### Ruta para Crear un Nuevo Registro
```plaintext
POST /api/crear
Input: {
    "nombre": "Juan",
    "edad": 30,
    "email": "juan@example.com"
}
Output: {
    "id": 1, 
    "mensaje": "Registro creado con éxito."
} o {
    "error": "Error al crear el registro."
}
```

### Ruta para Obtener Todos los Registros
```plaintext
GET /api/listar
Input: Ninguno.
Output: [
    {"id": 1, "nombre": "Juan", "edad": 30, "email": "juan@example.com"},
    {"id": 2, "nombre": "María", "edad": 25, "email": "maria@example.com"}
]
```

### Ruta para Obtener Un Registro por ID
```plaintext
GET /api/obtener/<id>
Input: ID del registro.
Output: {
    "id": 1,
    "nombre": "Juan",
    "edad": 30,
    "email": "juan@example.com"
} o {
    "error": "No se encontró el registro con ese ID."
}
```

### Ruta para Actualizar un Registro
```plaintext
PUT /api/actualizar/<id>
Input: {
    "nombre": "Juan",
    "edad": 31,
    "email": "juan@example.com"
} y el ID del registro.
Output: {
    "mensaje": "Registro actualizado con éxito."
} o {
    "error": "Error al actualizar el registro."
}
```

### Ruta para Eliminar Un Registro
```plaintext
DELETE /api/eliminar/<id>
Input: ID del registro.
Output: {
    "mensaje": "Registro eliminado con éxito."
} o {
    "error": "No se encontró el registro con ese ID."
}
```

## Documentación de HTMX

### Interactividad vía hx-get/hx-post
- **hx-get**: Usar para obtener datos.
- **hx-post**: Usar para enviar datos y actualizar la página.

Ejemplo:
```plaintext
hx-get="/api/listar" 
hx-target="#lista-registros"
hx-swap="innerHTML"
```

Este documento proporciona una estructura clara y detallada de cómo se implementará el sistema de API utilizando el stack FASTAPI_HTMX. El backend estará completamente autocontenido en `main_output.py`, y todo el frontend será generado dinámicamente por FastAPI, siguiendo las reglas establecidas para evitar bugs y mantener la arquitectura limpia y eficiente.