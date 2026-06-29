STACK: FASTAPI_HTMX

### Especificación de Software (SPEC)

#### 1. Introducción:
La aplicación se diseñará para anotar los puntos del truco, utilizando el stack FASTAPI_HTMX. Esta elección se basa en la necesidad de crear un sistema robusto y escalable que permita manejar CRUDs (Crear, Leer, Actualizar, Eliminar) de manera eficiente.

#### 2. Arquitectura:
La aplicación será estructurada como sigue:

- **Backend**: Implementado con FastAPI y HTMX para interactividad.
- **Frontend**: Servido por FastAPI a través de HTML/CSS/JS.
- **Base de Datos**: SQLite para almacenamiento de datos.

#### 3. Estructura del Proyecto:
El proyecto se dividirá en dos partes: Backend y Frontend, separadas claramente según las reglas establecidas.

##### Backend (main_output.py):
```plaintext
# main_output.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3

app = FastAPI()

class Point(BaseModel):
    id: int
    name: str
    score: float

def get_db_connection():
    conn = sqlite3.connect('points.db')
    return conn.cursor()

@app.post("/add_point/")
async def add_point(point: Point):
    with get_db_connection() as cursor:
        try:
            cursor.execute("INSERT INTO points (name, score) VALUES (?, ?)", 
                           (point.name, point.score))
            conn = sqlite3.connect('points.db')
            conn.commit()
            return {"message": "Point added successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_points/")
async def get_points():
    with get_db_connection() as cursor:
        cursor.execute("SELECT * FROM points")
        rows = cursor.fetchall()
        return [{"id": row[0], "name": row[1], "score": row[2]} for row in rows]

@app.put("/update_point/{point_id}")
async def update_point(point_id: int, point: Point):
    with get_db_connection() as cursor:
        try:
            cursor.execute("UPDATE points SET name = ?, score = ? WHERE id = ?", 
                           (point.name, point.score, point_id))
            conn = sqlite3.connect('points.db')
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Point not found")
            conn.commit()
            return {"message": "Point updated successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.delete("/delete_point/{point_id}")
async def delete_point(point_id: int):
    with get_db_connection() as cursor:
        try:
            cursor.execute("DELETE FROM points WHERE id = ?", (point_id,))
            conn = sqlite3.connect('points.db')
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Point not found")
            conn.commit()
            return {"message": "Point deleted successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
```

##### Frontend (HTML/CSS/JS):
El frontend será simple y servido por FastAPI. No se incluirán archivos .js para la lógica del servidor.

```plaintext
# index.html

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Point Tracker</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <h1>Point Tracker</h1>
    <form id="add-point-form">
        <label for="name">Name:</label><br>
        <input type="text" id="name" name="name"><br>
        <label for="score">Score:</label><br>
        <input type="number" id="score" name="score"><br>
        <button type="submit">Add Point</button>
    </form>

    <div id="points-list"></div>

    <script src="/static/script.js"></script>
</body>
</html>
```

```plaintext
# static/style.css

body {
    font-family: Arial, sans-serif;
}

h1 {
    text-align: center;
}

form {
    margin-bottom: 20px;
}

input[type="text"],
input[type="number"] {
    width: 50%;
    padding: 4px;
    border-radius: 4px;
    box-sizing: border-box;
}

button {
    background-color: #4CAF50;
    color: white;
    padding: 10px 20px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 16px;
    margin: 8px 0;
    cursor: pointer;
}

button:hover {
    background-color: #45a049;
}
```

```plaintext
# static/script.js

document.getElementById('add-point-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    
    const name = document.getElementById('name').value;
    const score = parseFloat(document.getElementById('score').value);
    
    if (!isNaN(score)) {
        await fetch('/add_point/', { method: 'POST', body: JSON.stringify({ name, score }) });
        document.getElementById('points-list').innerHTML += `<div><strong>${name}</strong>: ${score}</div>`;
        document.getElementById('name').value = '';
        document.getElementById('score').value = '';
    } else {
        alert('Score must be a number');
    }
});
```

#### 4. Documentación de Endpoints:
- **POST /add_point/**: Añade un nuevo punto.
- **GET /get_points/**: Obtiene todos los puntos.
- **PUT /update_point/{point_id}**: Actualiza un punto existente.
- **DELETE /delete_point/{point_id}**: Elimina un punto.

#### 5. Conclusion:
Esta arquitectura utiliza FastAPI para manejar las rutas y SQLite para almacenar datos, asegurando una solución escalable y eficiente. El frontend es simple pero interactivo gracias a HTMX, proporcionando una experiencia de usuario fluida sin recargar la página completa.

Este diseño cumple con todas las restricciones del sistema anfitrión y el stack FASTAPI_HTMX seleccionado.