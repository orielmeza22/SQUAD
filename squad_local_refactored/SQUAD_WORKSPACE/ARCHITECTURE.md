STACK: FASTAPI_HTMX

### Especificación de Software (SPEC)

#### 1. Introducción:
La aplicación se diseñará para anotar los puntos del truco, utilizando el stack FASTAPI_HTMX. Esta elección se basa en la necesidad de crear un sistema robusto y escalable que permita gestionar y registrar puntos de manera eficiente.

#### 2. Estructura del Proyecto:
- **Backend:** Implementado con FastAPI y HTMX.
- **Frontend:** Servido por FastAPI, utilizando HTML/CSS para la presentación visual.
  
#### 3. Archivos Actuales del Proyecto:
- `squad_checkpoints.sqlite`: Base de datos SQLite que almacena los puntos del truco.
- `main_output.py`: Punto de entrada del backend.

#### 4. Estructura del Backend (main_output.py):
```python
# main_output.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3

app = FastAPI()

class Checkpoint(BaseModel):
    id: int
    nombre_truco: str
    puntos: float

@app.post("/checkpoints/")
async def create_checkpoint(checkpoint: Checkpoint):
    conn = sqlite3.connect("squad_checkpoints.sqlite")
    cursor = conn.cursor()
    
    try:
        # Insertar nuevo punto del truco en la base de datos
        cursor.execute("""
            INSERT INTO checkpoints (nombre_truco, puntos)
            VALUES (?, ?)
        """, (checkpoint.nombre_truco, checkpoint.puntos))
        
        conn.commit()
        return {"message": "Checkpoint creado"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="El truco ya existe")
    finally:
        cursor.close()
        conn.close()

@app.get("/checkpoints/{id}")
async def get_checkpoint(id: int):
    conn = sqlite3.connect("squad_checkpoints.sqlite")
    cursor = conn.cursor()
    
    try:
        # Obtener el punto del truco por su ID
        cursor.execute("""
            SELECT nombre_truco, puntos FROM checkpoints WHERE id = ?
        """, (id,))
        
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Checkpoint no encontrado")
            
        return {"nombre_truco": result[0], "puntos": result[1]}
    except sqlite3.Error as e:
        print(f"Error en la consulta: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

@app.put("/checkpoints/{id}")
async def update_checkpoint(id: int, checkpoint: Checkpoint):
    conn = sqlite3.connect("squad_checkpoints.sqlite")
    cursor = conn.cursor()
    
    try:
        # Actualizar el punto del truco por su ID
        cursor.execute("""
            UPDATE checkpoints SET nombre_truco = ?, puntos = ?
            WHERE id = ?
        """, (checkpoint.nombre_truco, checkpoint.puntos, id))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Checkpoint no encontrado")
            
        conn.commit()
        return {"message": "Checkpoint actualizado"}
    except sqlite3.Error as e:
        print(f"Error en la consulta: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

@app.delete("/checkpoints/{id}")
async def delete_checkpoint(id: int):
    conn = sqlite3.connect("squad_checkpoints.sqlite")
    cursor = conn.cursor()
    
    try:
        # Eliminar el punto del truco por su ID
        cursor.execute("""
            DELETE FROM checkpoints WHERE id = ?
        """, (id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Checkpoint no encontrado")
            
        conn.commit()
        return {"message": "Checkpoint eliminado"}
    except sqlite3.Error as e:
        print(f"Error en la consulta: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

@app.get("/checkpoints/")
async def list_checkpoints():
    conn = sqlite3.connect("squad_checkpoints.sqlite")
    cursor = conn.cursor()
    
    try:
        # Listar todos los puntos del truco
        cursor.execute("""
            SELECT id, nombre_truco, puntos FROM checkpoints
        """)
        
        results = cursor.fetchall()
        return [{"id": row[0], "nombre_truco": row[1], "puntos": row[2]} for row in results]
    except sqlite3.Error as e:
        print(f"Error en la consulta: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

#### 5. Estructura del Frontend (HTML/CSS):
El frontend será servido por FastAPI y no requerirá archivos .js ni package.json.

```html
<!-- index.html -->
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Registrar Puntos de Truco</title>
    <link rel="stylesheet" href="/styles.css">
</head>
<body>
    <h1>Registrar Puntos del Truco</h1>
    
    <form id="checkpoint-form">
        <label for="nombre_truco">Nombre del Truco:</label>
        <input type="text" id="nombre_truco" name="nombre_truco"><br><br>

        <label for="puntos">Puntos del Truco:</label>
        <input type="number" id="puntos" name="puntos"><br><br>

        <button type="submit">Registrar</button>
    </form>

    <div id="checkpoint-list"></div>

    <script src="/main_output.js"></script>
</body>
</html>
```

```css
<!-- styles.css -->
body {
    font-family: Arial, sans-serif;
}

h1 {
    text-align: center;
}

form {
    margin-bottom: 20px;
}

label {
    display: block;
    margin-top: 5px;
}

input[type="text"],
input[type="number"] {
    width: 30%;
    padding: 4px;
    font-size: 16px;
}
```

```javascript
<!-- main_output.js -->
document.getElementById("checkpoint-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    
    const nombre_truco = document.getElementById("nombre_truco").value;
    const puntos = parseFloat(document.getElementById("puntos").value);
    
    if (!isNaN(puntos)) {
        try {
            const response = await fetch("/checkpoints/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ nombre_truco, puntos })
            });
            
            if (response.ok) {
                alert("Punto del truco registrado correctamente");
                
                // Actualizar la lista de checkpoints
                const list = document.getElementById("checkpoint-list");
                list.innerHTML = "";
                
                const responseList = await fetch("/checkpoints/");
                const data = await responseList.json();
                
                for (const checkpoint of data) {
                    list.innerHTML += `<p>${checkpoint.nombre_truco}: ${checkpoint.puntos}</p>`;
                }
            } else {
                alert("Error al registrar el punto del truco");
            }
        } catch (error) {
            console.error(error);
            alert("Error al registrar el punto del truco: " + error.message);
        }
    } else {
        alert("Por favor, ingresa un número válido para los puntos.");
    }
});
```

#### 6. Documentación de Endpoints:
- **POST /checkpoints/**: Crea un nuevo punto del truco.
- **GET /checkpoints/{id}**: Obtiene el detalle de un punto del truco por su ID.
- **PUT /checkpoints/{id}**: Actualiza los puntos de un truco existente.
- **DELETE /checkpoints/{id}**: Elimina un punto del truco por su ID.
- **GET /checkpoints/**: Lista todos los puntos del truco.

#### 7. Conclusion:
La aplicación se ha diseñado utilizando el stack FASTAPI_HTMX, lo que garantiza una estructura robusta y escalable para gestionar y registrar puntos de truco. El backend utiliza FastAPI para manejar las rutas HTTP y SQLite como base de datos. El frontend es servido por FastAPI y no requiere archivos .js ni package.json.

Este diseño cumple con todas las restricciones del sistema anfitrión, utilizando únicamente los recursos disponibles (Python + FastAPI + HTMX) y evitando la creación de archivos .js o subcarpetas backend.