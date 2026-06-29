
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
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
    except Exception: pass
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
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
    except Exception: pass
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
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
    except Exception: pass
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
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
    except Exception: pass
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
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
    except Exception: pass
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

import os

import os

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get('PORT', 8000)))