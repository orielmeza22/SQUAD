import re
import sys
import sqlite3
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
def get_db():
    conn = sqlite3.connect('squad_checkpoints.sqlite')
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
    except Exception: pass
    conn.row_factory = sqlite3.Row
    return conn
def create_tables():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS Usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        rol TEXT NOT NULL
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Turnos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha DATE NOT NULL,
        hora_inicio TIME NOT NULL,
        hora_fin TIME NOT NULL,
        usuario_id INTEGER, FOREIGN KEY (usuario_id) REFERENCES Usuarios(id)
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Asignaciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        turno_id INTEGER, FOREIGN KEY (turno_id) REFERENCES Turnos(id),
        empleado_id INTEGER, FOREIGN KEY (empleado_id) REFERENCES Usuarios(id)
    )''')
    conn.commit()
    conn.close()
app = FastAPI(title="SQUAD Auto-generated App")
# Mount static files
app.mount("/static", StaticFiles(directory="."), name="static")
templates = Jinja2Templates(directory="templates")
def get_db_connection():
    conn = sqlite3.connect('squad_checkpoints.sqlite')
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
    except Exception: pass
    conn.row_factory = sqlite3.Row
    return conn
class Usuario(BaseModel):
    nombre: str
    email: str
    rol: str
class Turno(BaseModel):
    fecha: str
    hora_inicio: str
    hora_fin: str
    usuario_id: int
class Asignacion(BaseModel):
    turno_id: int
    empleado_id: int
@app.on_event("startup")
def startup_db():
    create_tables()
@app.get('/', response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})
@app.post('/usuarios/')
async def create_usuario(usuario: Usuario):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Usuarios (nombre, email, rol) VALUES (?, ?, ?)", 
                   (usuario.nombre, usuario.email, usuario.rol))
    conn.commit()
    conn.close()
    return {'id': cursor.lastrowid}
@app.get('/usuarios/')
def read_usuarios():
    conn = get_db_connection()
    usuarios = conn.execute("SELECT * FROM Usuarios").fetchall()
    conn.close()
    return usuarios
@app.post('/turnos/')
async def create_turno(turno: Turno):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Turnos (fecha, hora_inicio, hora_fin, usuario_id) VALUES (?, ?, ?, ?)", 
                   (turno.fecha, turno.hora_inicio, turno.hora_fin, turno.usuario_id))
    conn.commit()
    conn.close()
    return {'id': cursor.lastrowid}
@app.get('/turnos/')
def read_turnos():
    conn = get_db_connection()
    turnos = conn.execute("SELECT * FROM Turnos").fetchall()
    conn.close()
    return turnos
@app.post('/asignaciones/')
async def create_asignacion(asignacion: Asignacion):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Asignaciones (turno_id, empleado_id) VALUES (?, ?)", 
                   (asignacion.turno_id, asignacion.empleado_id))
    conn.commit()
    conn.close()
    return {'id': cursor.lastrowid}
@app.get('/asignaciones/')
def read_asignaciones():
    conn = get_db_connection()
    asignaciones = conn.execute("SELECT * FROM Asignaciones").fetchall()
    conn.close()
    return asignaciones
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get('PORT', 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)