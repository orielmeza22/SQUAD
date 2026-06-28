from fastapi import FastAPI, HTTPException
import sqlite3
import os

app = FastAPI()

# Conexión a SQLite
conn = sqlite3.connect('kioscos.db')
try:
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
except Exception: pass
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

# Asegurarse de que el servidor escuche en el puerto definido por la variable de entorno PORT
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get('PORT', 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)