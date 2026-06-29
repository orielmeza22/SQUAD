STACK: FASTAPI_HTMX

### Especificación de Software (SPEC)

#### Resumen del Proyecto:
El proyecto se trata de desarrollar un sistema web para gestionar turnos, similar a uno comercial pero adaptado a una escala más pequeña. El sistema debe ser capaz de manejar la creación, modificación y eliminación de turnos, así como permitir el acceso a los mismos por parte del personal.

#### Arquitectura del Sistema:
La arquitectura elegida es FASTAPI_HTMX debido a su capacidad para crear un CRUD básico y eficiente. Además, HTMX proporcionará interactividad en tiempo real sin recargar la página completa, lo que mejorará la experiencia del usuario.

### Estructura de Archivos:

1. **main_output.py** - Punto de entrada principal del backend.
2. **templates/turnos.html** - Plantilla HTML para el frontend.
3. **static/css/style.css** - Archivo CSS para estilos.
4. **static/js/main.js** - Archivo JS para lógica del cliente.

### Estructura de carpetas:
```
sistema_turnos/
├── main_output.py
├── templates/
│   ├── turnos.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
└── spec.md  # Especificación de Software
```

### Estructura de las Tablas en SQLite:

1. **Tabla `turnos`**:
    - `id`: Integer, Primary Key, Autoincremental.
    - `nombre`: Text (Nombre del turno).
    - `descripcion`: Text (Descripción del turno).
    - `activo`: Boolean (Indica si el turno está activo o no).

### Endpoints y Rutas:

1. **Crear un nuevo turno**:
   - Método: POST
   - Ruta: `/turnos`
   - Input: JSON con los campos `nombre`, `descripcion` y `activo`.
   - Output: JSON con el ID del nuevo turno.

2. **Obtener todos los turnos**:
   - Método: GET
   - Ruta: `/turnos`
   - Input: Ninguno.
   - Output: JSON con una lista de todos los turnos.

3. **Actualizar un turno**:
   - Método: PUT
   - Ruta: `/turnos/<id>`
   - Input: JSON con los campos `nombre`, `descripcion` y `activo`.
   - Output: JSON con el ID del turno actualizado.

4. **Eliminar un turno**:
   - Método: DELETE
   - Ruta: `/turnos/<id>`
   - Input: Ninguno.
   - Output: JSON con un mensaje de éxito o error según la eliminación.

### Documentación Detallada:

1. **main_output.py**
```python
from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel
import sqlite3

app = FastAPI()

# Conexión a SQLite
conn = sqlite3.connect('squad_checkpoints.sqlite')
cursor = conn.cursor()

class Turno(BaseModel):
    id: int
    nombre: str
    descripcion: str
    activo: bool

@app.post("/turnos")
async def crear_turno(turno: Turno):
    cursor.execute("INSERT INTO turnos (nombre, descripcion, activo) VALUES (?, ?, ?)", 
                   (turno.nombre, turno.descripcion, turno.activo))
    conn.commit()
    return {"id": turno.id}

@app.get("/turnos", response_model=list[Turno])
async def obtener_turnos():
    cursor.execute("SELECT * FROM turnos")
    rows = cursor.fetchall()
    return [Turno(id=row[0], nombre=row[1], descripcion=row[2], activo=row[3]) for row in rows]

@app.put("/turnos/{id}")
async def actualizar_turno(id: int, turno: Turno):
    cursor.execute("UPDATE turnos SET nombre=?, descripcion=?, activo=? WHERE id=?", 
                   (turno.nombre, turno.descripcion, turno.activo, id))
    conn.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    return {"id": id}

@app.delete("/turnos/{id}")
async def eliminar_turno(id: int):
    cursor.execute("DELETE FROM turnos WHERE id=?", (id,))
    conn.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    return {"message": "Turno eliminado"}
```

2. **templates/turnos.html**
```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Administrar Turnos</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <h1>Administración de Turnos</h1>

    <form hx-post="/turnos" hx-target="#resultado" hx-swap="innerHTML">
        <label for="nombre">Nombre del turno:</label>
        <input type="text" id="nombre" name="nombre"><br><br>
        
        <label for="descripcion">Descripción del turno:</label>
        <textarea id="descripcion" name="descripcion"></textarea><br><br>

        <label for="activo">Activo:</label>
        <input type="checkbox" id="activo" name="activo"><br><br>

        <button type="submit">Crear Turno</button>
    </form>

    <div id="resultado"></div>

    <h2>Lista de Turnos</h2>
    <ul id="lista-turnos">
        {% for turno in turnos %}
            <li>{{ turno.nombre }} - {{ turno.descripcion }} ({{ turno.activo ? "Activo" : "Inactivo" }})</li>
        {% endfor %}
    </ul>

    <script src="/static/js/main.js"></script>
</body>
</html>
```

3. **static/css/style.css**
```css
body {
    font-family: Arial, sans-serif;
}

h1, h2 {
    text-align: center;
}

form {
    margin-bottom: 20px;
}

label {
    display: block;
    margin-bottom: 5px;
}

input[type="text"], textarea {
    width: 30%;
    padding: 4px;
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

4. **static/js/main.js**
```javascript
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    const resultado = document.getElementById('resultado');

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const nombre = document.getElementById('nombre').value;
        const descripcion = document.getElementById('descripcion').value;
        const activo = document.getElementById('activo').checked;

        try {
            const response = await fetch('/turnos', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nombre, descripcion, activo })
            });

            if (response.ok) {
                const turno = await response.json();
                resultado.innerHTML = `<p>Turno creado con éxito. ID: ${turno.id}</p>`;
            } else {
                throw new Error('Error al crear el turno');
            }
        } catch (error) {
            console.error(error);
            alert('Ha ocurrido un error al crear el turno.');
        }
    });
});
```

### Documentación de Rutas y Endpoints:

1. **Crear Turno**:
   - Método: POST
   - Ruta: `/turnos`
   - Input: JSON con `nombre`, `descripcion` y `activo`.
   - Output: JSON con el ID del turno creado.

2. **Obtener Todos los Turnos**:
   - Método: GET
   - Ruta: `/turnos`
   - Input: Ninguno.
   - Output: JSON con una lista de todos los turnos.

3. **Actualizar Turno**:
   - Método: PUT
   - Ruta: `/turnos/{id}`
   - Input: JSON con `nombre`, `descripcion` y `activo`.
   - Output: JSON con el ID del turno actualizado.

4. **Eliminar Turno**:
   - Método: DELETE
   - Ruta: `/turnos/{id}`
   - Input: Ninguno.
   - Output: JSON con un mensaje de éxito o error según la eliminación.

### Documentación Adicional:

1. **Plantilla HTML (`templates/turnos.html`)**:
   - Formulario para crear nuevos turnos.
   - Listado dinámico de todos los turnos existentes.

2. **Estilos CSS (`static/css/style.css`)**:
   - Estilos básicos para el frontend.

3. **Lógica del Cliente (`static/js/main.js`)**:
   - Interacción con el servidor mediante hx-post.
   - Actualización dinámica de la lista de turnos.

### Documentación Final:

Este documento proporciona una estructura clara y detallada para desarrollar un sistema web de gestión de turnos utilizando FastAPI, HTMX y SQLite. La arquitectura se centra en el backend con FastAPI, mientras que el frontend utiliza HTMX para mejorar la interactividad sin recargar páginas completas.

Para ejecutar este proyecto localmente:

1. Clona el repositorio.
2. Ejecuta `pip install -r requirements.txt` para instalar las dependencias necesarias.
3. Ejecuta `uvicorn main_output:app --reload` para iniciar el servidor FastAPI en modo de desarrollo.

Este esquema garantiza una implementación robusta y fácilmente escalable, adaptada a la escala más pequeña del proyecto.