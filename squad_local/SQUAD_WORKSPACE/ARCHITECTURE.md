STACK: FASTAPI_HTMX

# Especificación de Software (SPEC)

## Resumen del Proyecto:
El proyecto se enfoca en el desarrollo de un sistema de gestión de arquitecturas de servidor, como un alojamiento. Este sistema debe ser capaz de manejar y administrar diferentes arquitecturas de servidores de manera eficiente.

## Arquitectura del Sistema:

### Backend
- **Lenguaje de Programación:** Python (FastAPI)
- **Framework:** FastAPI
- **Interacción Cliente-Servidor:** HTMX para interactividad vía hx-get/hx-post
- **Base de Datos:** SQLite

### Frontend
- **Interfaz:** HTML/CSS/JavaScript proporcionado por FastAPI
- **Interacción con el Servidor:** HTMX

## Estructura del Proyecto:

### Backend (main_output.py)
```plaintext
# Este archivo es el punto de entrada para el backend.
# Todos los endpoints, modelos y lógica del servidor deben estar aquí.

from fastapi import FastAPI
import sqlite3
from pydantic import BaseModel
from typing import List

app = FastAPI()

class ServerArchitecture(BaseModel):
    id: int
    name: str
    description: str
    status: bool  # True si está activo, False si no

# Conexión a la base de datos SQLite
conn = sqlite3.connect('server_architectures.db')
cursor = conn.cursor()

# Crear tabla en la base de datos (si no existe)
cursor.execute("""
CREATE TABLE IF NOT EXISTS server_architectures (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    description TEXT,
    status BOOLEAN DEFAULT True
);
""")
conn.commit()

# Rutas del servidor

@app.post("/server-architectures/")
async def create_server_architecture(server_architecture: ServerArchitecture):
    cursor.execute("""
        INSERT INTO server_architectures (name, description, status)
        VALUES (?, ?, ?)
    """, (server_architecture.name, server_architecture.description, server_architecture.status))
    conn.commit()
    return {"message": "Server architecture created"}

@app.get("/server-architectures/")
async def read_server_architectures():
    cursor.execute("SELECT * FROM server_architectures")
    rows = cursor.fetchall()
    return [{"id": row[0], "name": row[1], "description": row[2], "status": row[3]} for row in rows]

@app.get("/server-architectures/{id}")
async def read_server_architecture(id: int):
    cursor.execute("SELECT * FROM server_architectures WHERE id = ?", (id,))
    row = cursor.fetchone()
    if row is None:
        return {"error": "Server architecture not found"}
    else:
        return {"id": row[0], "name": row[1], "description": row[2], "status": row[3]}

@app.put("/server-architectures/{id}")
async def update_server_architecture(id: int, server_architecture: ServerArchitecture):
    cursor.execute("""
        UPDATE server_architectures
        SET name = ?, description = ?, status = ?
        WHERE id = ?
    """, (server_architecture.name, server_architecture.description, server_architecture.status, id))
    conn.commit()
    return {"message": "Server architecture updated"}

@app.delete("/server-architectures/{id}")
async def delete_server_architecture(id: int):
    cursor.execute("DELETE FROM server_architectures WHERE id = ?", (id,))
    conn.commit()
    if cursor.rowcount == 0:
        return {"error": "Server architecture not found"}
    else:
        return {"message": "Server architecture deleted"}

# Ejecutar el servidor
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

### Frontend (HTML/CSS/JS)
- **HTML:** index.html
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Server Architecture Management</title>
    <!-- Estilos CSS -->
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div id="app"></div>

    <!-- JavaScript para HTMX -->
    <script src="https://unpkg.com/htmx.org@1.0.2"></script>
    <script src="scripts.js"></script>
</body>
</html>
```

- **CSS:** styles.css
```css
/* Estilos CSS */
body {
    font-family: Arial, sans-serif;
}

#app {
    margin-top: 50px;
}
```

- **JavaScript:** scripts.js
```javascript
// JavaScript para HTMX
document.addEventListener("DOMContentLoaded", function() {
    // Ejemplo de uso de HTMX en el frontend
});
```

## Documentación del Proyecto:

### Endpoints y Rutas

1. **Crear una nueva arquitectura de servidor**
   - Método: POST
   - URL: `/server-architectures/`
   - Input:
     ```json
     {
         "name": "Nombre de la arquitectura",
         "description": "Descripción de la arquitectura",
         "status": true  // True si está activa, False si no
     }
     ```
   - Output: JSON con el mensaje de éxito o error.

2. **Obtener todas las arquitecturas de servidor**
   - Método: GET
   - URL: `/server-architectures/`
   - Input: Ninguno.
   - Output:
     ```json
     [
         {"id": 1, "name": "Arquitectura 1", "description": "Descripción 1", "status": true},
         ...
     ]
     ```

3. **Obtener una arquitectura de servidor específica**
   - Método: GET
   - URL: `/server-architectures/{id}`
   - Input:
     ```json
     {
         "id": 1
     }
     ```
   - Output:
     ```json
     {"id": 1, "name": "Arquitectura 1", "description": "Descripción 1", "status": true}
     ```

4. **Actualizar una arquitectura de servidor**
   - Método: PUT
   - URL: `/server-architectures/{id}`
   - Input:
     ```json
     {
         "name": "Arquitectura actualizada",
         "description": "Descripción actualizada",
         "status": true  // True si está activa, False si no
     }
     ```
   - Output: JSON con el mensaje de éxito o error.

5. **Eliminar una arquitectura de servidor**
   - Método: DELETE
   - URL: `/server-architectures/{id}`
   - Input:
     ```json
     {
         "id": 1
     }
     ```
   - Output: JSON con el mensaje de éxito o error.

## Conclusiones:

Este plan técnico detalla la arquitectura y especificación del sistema de gestión de arquitecturas de servidor, utilizando FastAPI para el backend y HTMX para la interactividad. El frontend se maneja a través de HTML/CSS/JavaScript proporcionados por FastAPI. Este enfoque asegura una interfaz amigable y eficiente para administrar diferentes arquitecturas de servidores.