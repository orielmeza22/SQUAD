from fastapi import FastAPI, HTTPException
import sqlite3

app = FastAPI()

# Conexión a SQLite
cursor = sqlite3.connect('db.sqlite3').cursor()
try:
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
except Exception: pass

@app.post("/api/crear")
def crear_registro(nombre: str, edad: int, email: str):
    cursor.execute("INSERT INTO registros (nombre, edad, email) VALUES (?, ?, ?)", (nombre, edad, email))
    conn.commit()
    return {"id": 1, "mensaje": "Registro creado con éxito."}

@app.get("/api/listar")
def listar_registros():
    cursor.execute("SELECT * FROM registros")
    rows = cursor.fetchall()
    return [{"id": row[0], "nombre": row[1], "edad": row[2], "email": row[3]} for row in rows]

@app.get("/api/obtener/{id}")
def obtener_registro(id: int):
    cursor.execute("SELECT * FROM registros WHERE id = ?", (id,))
    row = cursor.fetchone()
    if row:
        return {"id": row[0], "nombre": row[1], "edad": row[2], "email": row[3]}
    else:
        raise HTTPException(status_code=404, detail="No se encontró el registro con ese ID.")

@app.put("/api/actualizar/{id}")
def actualizar_registro(id: int, nombre: str = None, edad: int = None, email: str = None):
    if nombre is not None:
        cursor.execute("UPDATE registros SET nombre = ? WHERE id = ?", (nombre, id))
    if edad is not None:
        cursor.execute("UPDATE registros SET edad = ? WHERE id = ?", (edad, id))
    if email is not None:
        cursor.execute("UPDATE registros SET email = ? WHERE id = ?", (email, id))
    conn.commit()
    return {"mensaje": "Registro actualizado con éxito."}

@app.delete("/api/eliminar/{id}")
def eliminar_registro(id: int):
    cursor.execute("DELETE FROM registros WHERE id = ?", (id,))
    conn.commit()
    if cursor.rowcount > 0:
        return {"mensaje": "Registro eliminado con éxito."}
    else:
        raise HTTPException(status_code=404, detail="No se encontró el registro con ese ID.")