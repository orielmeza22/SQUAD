# Este archivo es el punto de entrada para el backend.
# Todos los endpoints, modelos y lógica del servidor deben estar aquí.

from fastapi import FastAPI, Request, Form, HTTPException
import sqlite3
from pydantic import BaseModel

app = FastAPI(title="SQUAD Auto-generated App")

# Mount static files
app.mount("/static", StaticFiles(directory="."), name="static")

# Database Helper
DB_FILE = "server_architectures.db"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# SQUAD_INJECT_DB_SCHEMA
cursor.execute("""
CREATE TABLE IF NOT EXISTS server_architectures (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    description TEXT,
    status BOOLEAN DEFAULT True
);
""")
conn.commit()

# SQUAD_INJECT_LOGIC

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
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)