### Especificación de Software (SPEC)

**STACK:** FASTAPI_HTMX

---

#### **1. Descripción General**

El sistema web de gestión de turnos es una aplicación diseñada para gestionar eficientemente los horarios y asignaciones de personal en un entorno empresarial a escala pequeña. Utilizando el stack tecnológico **FASTAPI_HTMX**, la aplicación se basará en Python, FastAPI para el backend, HTMX para la interactividad del frontend, y SQLite como base de datos.

---

#### **2. Base de Datos**

**Archivo:** squad_checkpoints.sqlite

La base de datos SQLite `squad_checkpoints.sqlite` contendrá las siguientes tablas:

1. **Usuarios**
   - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
   - `nombre`: TEXT NOT NULL
   - `email`: TEXT UNIQUE NOT NULL
   - `rol`: TEXT NOT NULL (e.g., 'admin', 'empleado')

2. **Turnos**
   - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
   - `fecha`: DATE NOT NULL
   - `hora_inicio`: TIME NOT NULL
   - `hora_fin`: TIME NOT NULL
   - `usuario_id`: INTEGER, FOREIGN KEY (usuario_id) REFERENCES Usuarios(id)

3. **Asignaciones**
   - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
   - `turno_id`: INTEGER, FOREIGN KEY (turno_id) REFERENCES Turnos(id)
   - `empleado_id`: INTEGER, FOREIGN KEY (empleado_id) REFERENCES Usuarios(id)

---

#### **3. Estructura del Proyecto**

**Backend:**
- **main_output.py**: Contendrá toda la lógica de FastAPI, incluyendo modelos, rutas y la configuración de SQLite.

**Frontend:**
- **templates/**: Carpeta que contendrá los archivos HTML servidos por FastAPI.
  - `index.html`: Página principal con el formulario para gestionar turnos.
  - `turnos.html`: Lista de turnos y asignaciones.
  - `asignacion.html`: Formulario para crear o editar asignaciones.

---

#### **4. Endpoints**

**1. Usuarios**
- **GET /usuarios**: Retorna una lista de todos los usuarios.
- **POST /usuarios**: Crea un nuevo usuario.
  - **Inputs:**
    - `nombre` (string)
    - `email` (string)
    - `rol` (string)
  - **Outputs:**
    - JSON con el ID del usuario creado.

**2. Turnos**
- **GET /turnos**: Retorna una lista de todos los turnos.
- **POST /turnos**: Crea un nuevo turno.
  - **Inputs:**
    - `fecha` (date)
    - `hora_inicio` (time)
    - `hora_fin` (time)
    - `usuario_id` (integer)
  - **Outputs:**
    - JSON con el ID del turno creado.

**3. Asignaciones**
- **GET /asignaciones**: Retorna una lista de todas las asignaciones.
- **POST /asignaciones**: Crea una nueva asignación.
  - **Inputs:**
    - `turno_id` (integer)
    - `empleado_id` (integer)
  - **Outputs:**
    - JSON con el ID de la asignación creada.

---

#### **5. Interactividad Frontend**

**1. Index.html**
- Formulario para crear un nuevo usuario.
- Botón que envía una solicitud POST a `/usuarios`.

**2. Turnos.html**
- Tabla que muestra todos los turnos y permite agregar nuevas asignaciones.
- Botón que envía una solicitud POST a `/turnos` para crear un turno.

**3. Asignacion.html**
- Formulario para crear o editar asignaciones.
- Botones que envían solicitudes POST a `/asignaciones` para crear o actualizar asignaciones.

---

#### **6. Configuración de FastAPI**

**main_output.py**
```python
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import sqlite3

app = FastAPI()

# Conexión a la base de datos SQLite
def get_db_connection():
    conn = sqlite3.connect('squad_checkpoints.sqlite')
    conn.row_factory = sqlite3.Row
    return conn

# Modelos Pydantic
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

# Rutas FastAPI
@app.get("/")
async def read_root():
    return {"message": "Bienvenido a la gestión de turnos"}

@app.post("/usuarios/")
async def create_usuario(usuario: Usuario):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Usuarios (nombre, email, rol) VALUES (?, ?, ?)", 
                   (usuario.nombre, usuario.email, usuario.rol))
    conn.commit()
    conn.close()
    return {"id": cursor.lastrowid}

@app.get("/usuarios/")
async def read_usuarios():
    conn = get_db_connection()
    usuarios = conn.execute("SELECT * FROM Usuarios").fetchall()
    conn.close()
    return usuarios

# ... (agregar rutas para turnos y asignaciones de manera similar)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

#### **7. Ejecución del Proyecto**

1. **Backend:**
   - Asegúrate de tener Python instalado.
   - Instala FastAPI y Uvicorn:
     ```bash
     pip install fastapi uvicorn
     ```
   - Ejecuta el servidor:
     ```bash
     python main_output.py
     ```

2. **Frontend:**
   - Los archivos HTML se servirán directamente desde la carpeta `templates/` de FastAPI.

---

Este plan técnico detallado proporciona una estructura clara y separada para el backend y frontend, asegurando que la aplicación cumpla con las reglas establecidas y maximice su fiabilidad.