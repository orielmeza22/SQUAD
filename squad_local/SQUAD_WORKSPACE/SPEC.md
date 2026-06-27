STACK: FASTAPI_HTMX

# Especificación de Software (SPEC)

## Resumen del Proyecto:
El proyecto consiste en desarrollar una aplicación web para gestionar turnos, utilizando el stack tecnológico FASTAPI_HTMX. Esta arquitectura se ha seleccionado debido a su versatilidad y capacidad para manejar CRUDs y sistemas de gestión de manera eficiente.

## Arquitectura del Proyecto:

### Backend:
El backend será desarrollado en Python con FastAPI, una biblioteca web moderna y rápida que permite crear APIs HTTP. El punto de entrada principal será un archivo `main_output.py` que usará Uvicorn para ejecutar el servidor.

#### Archivos del Backend:
1. **main_output.py**: Este es el punto de entrada del backend.
2. **models.py**: Contiene la definición de las entidades y sus relaciones (si se requiere).
3. **database.py**: Manejo de la base de datos SQLite, incluyendo la creación de tablas y operaciones CRUD básicas.
4. **routers.py**: Definiciones de rutas para manejar los endpoints del API.

### Frontend:
El frontend será manejado por FastAPI con HTMX (Hyper Textual Markup Exchange), que permite una interactividad fluida sin recargar la página completa, mejorando así el rendimiento y experiencia del usuario. El contenido HTML/CSS/JS se servirá directamente desde FastAPI.

#### Archivos del Frontend:
1. **templates/index.html**: La plantilla principal donde se renderizarán los componentes.
2. **static/css/style.css**: Estilos CSS para la interfaz de usuario.
3. **static/js/main.js**: Lógica JavaScript para manejar eventos y comportamientos interactivos.

### Integración:
- **FastAPI**: Usado para definir las rutas y endpoints del API, así como para servir el frontend HTML/CSS/JS.
- **HTMX**: Permite la interacción fluida con el servidor sin recargar la página completa, mejorando la experiencia de usuario.
- **SQLite**: Base de datos utilizada para almacenar los datos de los turnos.

## Archivos Detallados:

### Backend
1. **main_output.py**
   ```python
   import uvicorn
   from fastapi import FastAPI

   app = FastAPI()

   @app.get("/")
   def read_root():
       return {"message": "Bienvenido a la aplicación de gestión de turnos"}

   if __name__ == "__main__":
       uvicorn.run(app, host="0.0.0.0", port=8000)
   ```

2. **models.py**
   ```python
   from typing import List

   class TurnoModel:
       id: int
       nombre: str
       descripcion: str
       fecha_hora: str

   turnos = [
       TurnoModel(id=1, nombre="Turno 1", descripcion="Descripción del turno 1", fecha_hora="2023-10-05T14:00"),
       TurnoModel(id=2, nombre="Turno 2", descripcion="Descripción del turno 2", fecha_hora="2023-10-06T15:00")
   ]
   ```

3. **database.py**
   ```python
   import sqlite3

   def create_connection():
       conn = sqlite3.connect('turnos.db')
       return conn

   def create_table(conn):
       cursor = conn.cursor()
       cursor.execute('''CREATE TABLE IF NOT EXISTS turnos (
                           id INTEGER PRIMARY KEY,
                           nombre TEXT,
                           descripcion TEXT,
                           fecha_hora TEXT
                       )''')

   def insert_turno(conn, turno: TurnoModel):
       cursor = conn.cursor()
       cursor.execute("INSERT INTO turnos (nombre, descripcion, fecha_hora) VALUES (?, ?, ?)",
                      (turno.nombre, turno.descripcion, turno.fecha_hora))
       conn.commit()

   def get_all_turnos(conn):
       cursor = conn.cursor()
       cursor.execute("SELECT * FROM turnos")
       return cursor.fetchall()

   def close_connection(conn):
       conn.close()
   ```

4. **routers.py**
   ```python
   from fastapi import FastAPI, HTTPException, Depends
   from sqlalchemy.orm import Session

   app = FastAPI()

   # Dependencia para obtener una sesión de la base de datos
   def get_db():
       db = sqlite3.connect('turnos.db')
       yield db
       db.close()

   @app.get("/turnos", response_model=List[TurnoModel])
   async def read_turnos(db: Session = Depends(get_db)):
       turnos = []
       for turno in db.execute("SELECT * FROM turnos"):
           turnos.append(TurnoModel(id=turno[0], nombre=turno[1], descripcion=turno[2], fecha_hora=turno[3]))
       return turnos

   @app.post("/turnos", response_model=TurnoModel)
   async def create_turno(turno: TurnoModel, db: Session = Depends(get_db)):
       insert_turno(db, turno)
       return turno
   ```

### Frontend
1. **templates/index.html**
   ```html
   <!DOCTYPE html>
   <html lang="es">
   <head>
       <meta charset="UTF-8">
       <title>Aplicación de Gestión de Turnos</title>
       <link rel="stylesheet" href="/static/css/style.css">
   </head>
   <body>
       <h1>Gestión de Turnos</h1>
       <div id="turnos-list"></div>

       <!-- Script para HTMX -->
       <script src="https://unpkg.com/htmx.org@1.0.2"></script>
       <script src="/static/js/main.js"></script>
   </body>
   </html>
   ```

2. **static/css/style.css**
   ```css
   body {
       font-family: Arial, sans-serif;
   }

   #turnos-list {
       list-style-type: none;
       padding: 0;
   }

   .turno-item {
       margin-bottom: 10px;
   }
   ```

3. **static/js/main.js**
   ```javascript
   document.addEventListener("DOMContentLoaded", function() {
       const turnosList = document.getElementById('turnos-list');

       fetch('/turnos')
           .then(response => response.json())
           .then(data => {
               data.forEach(turno => {
                   const turnoItem = document.createElement('div');
                   turnoItem.className = 'turno-item';
                   turnoItem.innerHTML = `
                       <h3>${turno.nombre}</h3>
                       <p>Descripción: ${turno.descripcion}</p>
                       <p>Fecha y Hora: ${turno.fecha_hora}</p>
                   `;
                   turnosList.appendChild(turnoItem);
               });
           })
           .catch(error => console.error('Error:', error));
   });
   ```

### Integración
Para ejecutar la aplicación, asegúrate de tener instalado FastAPI y Uvicorn. Luego, ejecuta el siguiente comando en tu terminal:

```bash
uvicorn main_output:app --reload
```

Este comando iniciará el servidor FastAPI en modo desarrollo con reescritura automática.

### Pruebas
Para probar la aplicación, puedes acceder a `http://localhost:8000/turnos` y ver los turnos existentes. También puedes agregar nuevos turnos utilizando el mismo endpoint.

Este esquema garantiza una separación clara entre el backend y frontend, cumpliendo con las reglas de arquitectura establecidas.