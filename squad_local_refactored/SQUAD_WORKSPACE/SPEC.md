### Especificación de Software (SPEC)

**STACK:** FASTAPI_HTMX

#### 1. **Descripción General**
El objetivo de esta API es proporcionar un CRUD básico para gestionar elementos en una base de datos SQLite utilizando FastAPI como framework backend y HTML/CSS para el frontend.

#### 2. **Estructura del Proyecto**

- **Backend (main_output.py):**
  - Contendrá toda la lógica del servidor, incluyendo las rutas de FastAPI, la conexión a la base de datos SQLite y el punto de entrada para ejecutar la aplicación con Uvicorn.

- **Frontend (HTML/CSS):**
  - Los archivos HTML y CSS se servirán directamente desde FastAPI. No se utilizará ningún archivo JavaScript en el frontend.

#### 3. **Base de Datos**

**Tabla: items**
```sql
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT
);
```

#### 4. **Endpoints y Métodos HTTP**

| Endpoint | Método | Descripción | Entrada | Salida |
|----------|--------|-------------|---------|--------|
| /items   | GET    | Obtener todos los elementos | N/A | Lista de elementos (JSON) |
| /items/{id} | GET  | Obtener un elemento por ID | id (path parameter) | Elemento (JSON) |
| /items   | POST   | Crear un nuevo elemento | JSON con name y description | ID del elemento creado (JSON) |
| /items/{id} | PUT  | Actualizar un elemento existente | id (path parameter), JSON con name y description | Mensaje de éxito (JSON) |
| /items/{id} | DELETE | Eliminar un elemento | id (path parameter) | Mensaje de éxito (JSON) |

#### 5. **Detalles de Implementación**

- **main_output.py:**
  - Incluirá la definición de las rutas FastAPI, la conexión a la base de datos SQLite y el punto de entrada para ejecutar la aplicación con Uvicorn.
  - La lógica del servidor estará completamente encapsulada en este archivo.

- **HTML/CSS:**
  - Los archivos HTML y CSS se servirán directamente desde FastAPI. No se utilizará ningún archivo JavaScript en el frontend.

#### 6. **Ejemplo de Rutas**

**GET /items**
```python
@app.get("/items")
def read_items():
    conn = sqlite3.connect("local_project.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items")
    items = cursor.fetchall()
    conn.close()
    return [{"id": item[0], "name": item[1], "description": item[2]} for item in items]
```

**POST /items**
```python
@app.post("/items")
def create_item(item: dict):
    conn = sqlite3.connect("local_project.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO items (name, description) VALUES (?, ?)", (item["name"], item["description"]))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return {"id": new_id}
```

**GET /items/{id}**
```python
@app.get("/items/{item_id}")
def read_item(item_id: int):
    conn = sqlite3.connect("local_project.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    item = cursor.fetchone()
    conn.close()
    if item:
        return {"id": item[0], "name": item[1], "description": item[2]}
    else:
        return {"error": "Item not found"}, 404
```

**PUT /items/{id}**
```python
@app.put("/items/{item_id}")
def update_item(item_id: int, item: dict):
    conn = sqlite3.connect("local_project.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE items SET name = ?, description = ? WHERE id = ?", (item["name"], item["description"], item_id))
    conn.commit()
    if cursor.rowcount == 0:
        return {"error": "Item not found"}, 404
    conn.close()
    return {"message": "Item updated successfully"}
```

**DELETE /items/{id}**
```python
@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    conn = sqlite3.connect("local_project.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    if cursor.rowcount == 0:
        return {"error": "Item not found"}, 404
    conn.close()
    return {"message": "Item deleted successfully"}
```

#### 7. **Ejecución de la Aplicación**

- Para ejecutar la aplicación, se utilizará el archivo `main_output.py` con Uvicorn:
```bash
python main_output.py
```

Este plan técnico detallado proporciona una estructura clara y separada entre frontend y backend, asegurando que todas las reglas de arquitectura y stack seleccionado sean cumplidas.