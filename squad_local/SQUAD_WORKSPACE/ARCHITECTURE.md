STACK: FASTAPI_HTMX

# Especificación de Software (SPEC)

## Resumen del Proyecto:
El objetivo es desarrollar un sistema de gestión de puntos de ventas para kioscos utilizando Python, FastAPI y HTMX para una interfaz interactiva. El sistema se basará en SQLite como base de datos.

## Estructura del Sistema:

### Backend
- **Punto de Entrada:** main_output.py
- **Lenguaje:** Python
- **Framework:** FastAPI
- **Interacción Cliente:** HTMX (hx-get/hx-post)
- **Base de Datos:** SQLite

### Frontend
- **HTML/CSS/JS:** Servido por FastAPI
- **Interacción Cliente:** HTMX (hx-get/hx-post)

## Estructura del Proyecto:

```
proyecto/
├── main_output.py
├── spec.md  # Este archivo
└── templates/
    ├── index.html
    └── styles.css
```

### Backend (main_output.py)
```plaintext
# Esta es la estructura de archivos y carpetas para el backend.
# Todos los componentes del backend deben estar en este único archivo.

from fastapi import FastAPI, HTTPException
import sqlite3

app = FastAPI()

# Conexión a SQLite
conn = sqlite3.connect('kioscos.db')
cursor = conn.cursor()

# Crear tabla de ventas si no existe
cursor.execute("""
    CREATE TABLE IF NOT EXISTS ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha DATE,
        producto TEXT,
        cantidad INT,
        precio REAL
    )
""")
conn.commit()

@app.post("/crear_venta/")
async def crear_venta(fecha: str, producto: str, cantidad: int, precio: float):
    cursor.execute("""
        INSERT INTO ventas (fecha, producto, cantidad, precio)
        VALUES (?, ?, ?, ?)
    """, (fecha, producto, cantidad, precio))
    conn.commit()
    return {"message": "Venta creada"}

@app.get("/obtener_ventas/")
async def obtener_ventas():
    cursor.execute("SELECT * FROM ventas")
    rows = cursor.fetchall()
    return [{"id": row[0], "fecha": row[1], "producto": row[2], "cantidad": row[3], "precio": row[4]} for row in rows]

@app.delete("/eliminar_venta/{venta_id}")
async def eliminar_venta(venta_id: int):
    cursor.execute("DELETE FROM ventas WHERE id = ?", (venta_id,))
    conn.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return {"message": "Venta eliminada"}
```

### Frontend
El frontend se servirá a través de FastAPI y HTMX. Los archivos HTML/CSS/JS estarán en la carpeta `templates`.

#### index.html
```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Administración de Ventas</title>
    <link rel="stylesheet" href="/styles.css">
</head>
<body>
    <h1>Administrador de Ventas</h1>

    <!-- Formulario para crear una venta -->
    <form hx-post="/crear_venta/" hx-target="#resultado" hx-swap="innerHTML">
        <label for="fecha">Fecha:</label>
        <input type="date" id="fecha" name="fecha"><br><br>
        
        <label for="producto">Producto:</label>
        <input type="text" id="producto" name="producto"><br><br>

        <label for="cantidad">Cantidad:</label>
        <input type="number" id="cantidad" name="cantidad"><br><br>

        <label for="precio">Precio:</label>
        <input type="number" id="precio" name="precio"><br><br>

        <button type="submit">Crear Venta</button>
    </form>

    <!-- Resultado de la creación de una venta -->
    <div id="resultado"></div>

    <!-- Botón para eliminar una venta -->
    <button hx-get="/obtener_ventas/" hx-target="#lista_ventas" hx-swap="innerHTML">Ver Ventas</button>

    <!-- Lista de ventas -->
    <div id="lista_ventas"></div>
    
    <script src="https://unpkg.com/htmx.org@1.0.2"></script>
</body>
</html>
```

#### styles.css
```css
/* Estilos básicos para el frontend */
body {
    font-family: Arial, sans-serif;
}

h1 {
    text-align: center;
}

form {
    margin-bottom: 20px;
}

button {
    padding: 5px 10px;
}
```

### Documentación de Endpoints

- **Crear Venta**
  - Método HTTP: POST
  - Ruta: `/crear_venta/`
  - Inputs:
    - `fecha`: Fecha en formato YYYY-MM-DD (string)
    - `producto`: Nombre del producto (string)
    - `cantidad`: Cantidad de unidades (int)
    - `precio`: Precio unitario (float)
  - Output: JSON con mensaje de éxito

- **Obtener Ventas**
  - Método HTTP: GET
  - Ruta: `/obtener_ventas/`
  - Inputs: Ninguno
  - Output: JSON con lista de ventas en formato:
    ```json
    [
        {"id": int, "fecha": str, "producto": str, "cantidad": int, "precio": float}
    ]
    ```

- **Eliminar Venta**
  - Método HTTP: DELETE
  - Ruta: `/eliminar_venta/{venta_id}`
  - Inputs:
    - `venta_id`: Identificador de la venta a eliminar (int)
  - Output: JSON con mensaje de éxito si la venta se eliminó, o error 404 si no existe.

## Conclusiones
Este esquema proporciona una estructura clara y organizada para el desarrollo del sistema. El backend está diseñado para ser autocontenido en `main_output.py`, mientras que el frontend utiliza HTMX para interacción con el servidor. La base de datos SQLite se maneja directamente desde FastAPI, lo cual simplifica la implementación y mejora la fiabilidad del sistema.

Este plan técnico detallado garantiza una arquitectura sólida y fácilmente escalable para el sistema de gestión de puntos de ventas para kioscos.