STACK: FASTAPI_HTMX

# Especificación de Software (SPEC)

## Resumen del Proyecto:
El objetivo principal es crear un sistema de gestión de arquitecturas de servidor, como un alojamiento, utilizando las tecnologías disponibles en el entorno local. Este proyecto se desarrollará utilizando el stack FASTAPI_HTMX debido a su versatilidad y capacidad para manejar CRUDs y herramientas de administración.

## Arquitectura del Sistema:

### 1. **Punto de Entrada:**
   - El punto de entrada será `main_output.py` que usará `uvicorn` como servidor web.
   
```python
# main_output.py

from fastapi import FastAPI, HTTPException
import sqlite3
from pydantic import BaseModel
from typing import List

app = FastAPI()

class ServerArchitecture(BaseModel):
    id: int
    name: str
    description: str
    status: bool

@app.post("/servers/")
async def create_server(server: ServerArchitecture):
    conn = sqlite3.connect("server_architectures.db")
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO server_architectures (name, description, status)
            VALUES (?, ?, ?)
        """, (server.name, server.description, server.status))
        
        conn.commit()
        return {"message": "Server created successfully"}
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.get("/servers/", response_model=List[ServerArchitecture])
async def read_servers():
    conn = sqlite3.connect("server_architectures.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, description, status FROM server_architectures
    """)
    
    rows = cursor.fetchall()
    return [ServerArchitecture(id=row[0], name=row[1], description=row[2], status=row[3]) for row in rows]

@app.get("/servers/{server_id}", response_model=ServerArchitecture)
async def read_server(server_id: int):
    conn = sqlite3.connect("server_architectures.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, description, status FROM server_architectures
        WHERE id = ?
    """, (server_id,))
    
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Server not found")
        
    return ServerArchitecture(id=row[0], name=row[1], description=row[2], status=row[3])

@app.put("/servers/{server_id}")
async def update_server(server_id: int, server: ServerArchitecture):
    conn = sqlite3.connect("server_architectures.db")
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE server_architectures
            SET name = ?, description = ?, status = ?
            WHERE id = ?
        """, (server.name, server.description, server.status, server_id))
        
        rows_affected = cursor.rowcount
        
        if rows_affected == 0:
            raise HTTPException(status_code=404, detail="Server not found")
            
        conn.commit()
        return {"message": "Server updated successfully"}
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/servers/{server_id}")
async def delete_server(server_id: int):
    conn = sqlite3.connect("server_architectures.db")
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            DELETE FROM server_architectures
            WHERE id = ?
        """, (server_id,))
        
        rows_affected = cursor.rowcount
        
        if rows_affected == 0:
            raise HTTPException(status_code=404, detail="Server not found")
            
        conn.commit()
        return {"message": "Server deleted successfully"}
```

### 2. **Frontend:**
   - El frontend será manejado por FastAPI y no requerirá archivos .js ni package.json.

```python
# main_output.py (continuación)

from fastapi import FastAPI, Request, Response

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Server Architecture Management System"}

@app.post("/servers/")
async def create_server(request: Request):
    data = await request.json()
    
    server_id = data['id']
    name = data['name']
    description = data['description']
    status = data['status']
    
    conn = sqlite3.connect("server_architectures.db")
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO server_architectures (name, description, status)
            VALUES (?, ?, ?)
        """, (name, description, status))
        
        conn.commit()
        return {"message": "Server created successfully"}
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/servers/", response_model=List[ServerArchitecture])
async def read_servers(request: Request):
    conn = sqlite3.connect("server_architectures.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, description, status FROM server_architectures
    """)
    
    rows = cursor.fetchall()
    return [ServerArchitecture(id=row[0], name=row[1], description=row[2], status=row[3]) for row in rows]

@app.get("/servers/{server_id}", response_model=ServerArchitecture)
async def read_server(request: Request, server_id: int):
    conn = sqlite3.connect("server_architectures.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, description, status FROM server_architectures
        WHERE id = ?
    """, (server_id,))
    
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Server not found")
        
    return ServerArchitecture(id=row[0], name=row[1], description=row[2], status=row[3])

@app.put("/servers/{server_id}")
async def update_server(request: Request, server_id: int):
    data = await request.json()
    
    conn = sqlite3.connect("server_architectures.db")
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE server_architectures
            SET name = ?, description = ?, status = ?
            WHERE id = ?
        """, (data['name'], data['description'], data['status'], server_id))
        
        rows_affected = cursor.rowcount
        
        if rows_affected == 0:
            raise HTTPException(status_code=404, detail="Server not found")
            
        conn.commit()
        return {"message": "Server updated successfully"}
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/servers/{server_id}")
async def delete_server(request: Request, server_id: int):
    data = await request.json()
    
    conn = sqlite3.connect("server_architectures.db")
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            DELETE FROM server_architectures
            WHERE id = ?
        """, (server_id,))
        
        rows_affected = cursor.rowcount
        
        if rows_affected == 0:
            raise HTTPException(status_code=404, detail="Server not found")
            
        conn.commit()
        return {"message": "Server deleted successfully"}
```

### 3. **Estructura de carpetas:**
   - No se utilizarán subcarpetas para el backend.
   
```plaintext
server_architectures/
├── main_output.py
└── server_architectures.db
```

## Conclusion:
La arquitectura FASTAPI_HTMX proporciona una solución robusta y escalable para gestionar arquitecturas de servidor. El uso exclusivo de Python, FastAPI y SQLite garantiza la simplicidad y eficiencia del sistema. Este enfoque cumple con todas las restricciones y reglas establecidas, asegurando una implementación segura y fácilmente manejable.

Este plan técnico detallado proporciona una base sólida para el desarrollo de un sistema de gestión de arquitecturas de servidor que cumple con los requisitos del proyecto.