STACK: FASTAPI_HTMX

# Especificación de Software (SPEC)

## Resumen del Proyecto:
El objetivo principal es crear un sistema de gestión de arquitecturas de servidor, como un alojamiento, utilizando las tecnologías disponibles en el entorno anfitrión local. El stack elegido para este proyecto es FASTAPI_HTMX debido a su versatilidad y capacidad para manejar CRUDs, dashboards y herramientas de administración.

## Arquitectura del Sistema:

### Backend:
1. **Punto de Entrada:**
   - El punto de entrada será `main_output.py` que usará `uvicorn` para ejecutar el servidor FastAPI.
   
2. **Lógica del Servidor:**
   - Todos los archivos relacionados con la lógica del servidor se ubicarán en una carpeta separada, como `backend/`.
   - No se generarán ni planificarán archivos .js para la lógica del servidor.

3. **Base de Datos:**
   - La base de datos será SQLite y se utilizará directamente desde FastAPI.
   
4. **Archivos Importantes en el Backend:**
   ```plaintext
   ├── backend/
   │   ├── __init__.py
   │   ├── crud.py  # Contiene las funciones CRUD para la gestión de servidores
   │   ├── main_output.py  # Punto de entrada del servidor FastAPI
   │   └── models.py    # Definición de modelos para SQLite
   ├── frontend/
   ├── static/
   ├── templates/
   ├── requirements.txt
   └── spec.md
   ```

### Frontend:
1. **HTML/CSS:**
   - Todos los archivos HTML y CSS del frontend se ubicarán en la carpeta `frontend/`.
   
2. **Interactividad:**
   - La interactividad será proporcionada a través de HTMX, que es compatible con FastAPI.
   
3. **Archivos Importantes en el Frontend:**
   ```plaintext
   ├── backend/
   │   └── main_output.py  # Punto de entrada del servidor FastAPI
   ├── frontend/
   │   ├── index.html      # Archivo principal del frontend
   │   ├── styles.css      # Estilos CSS
   │   └── scripts.js      # Lógica JS para HTMX (no se generará)
   ├── static/
   ├── templates/
   ├── requirements.txt
   └── spec.md
   ```

### Archivos Importantes:
1. **`main_output.py`:**
   ```python
   import uvicorn
   from backend.crud import app

   if __name__ == "__main__":
       uvicorn.run(app, host="0.0.0.0", port=8000)
   ```

2. **`crud.py`:**
   ```python
   from fastapi import FastAPI
   from models import ServerModel  # Importa el modelo de servidor

   app = FastAPI()

   @app.post("/servers/")
   def create_server(server: ServerModel):
       # Lógica para crear un nuevo servidor en la base de datos SQLite
       return {"message": "Server created"}

   @app.get("/servers/{server_id}")
   def read_server(server_id: int):
       # Lógica para leer un servidor específico por su ID
       return {"message": f"Server {server_id} retrieved"}

   # Implementa las otras operaciones CRUD según sea necesario.
   ```

3. **`models.py`:**
   ```python
   from sqlalchemy import Column, Integer, String, create_engine
   from sqlalchemy.ext.declarative import declarative_base

   Base = declarative_base()

   class ServerModel(Base):
       __tablename__ = "servers"
       
       id = Column(Integer, primary_key=True)
       name = Column(String(50))
       description = Column(String(250))

       def __repr__(self):
           return f"Server(id={self.id}, name='{self.name}', description='{self.description}')"

   engine = create_engine("sqlite:///servers.db")
   Base.metadata.create_all(engine)
   ```

4. **`index.html`:**
   ```html
   <!DOCTYPE html>
   <html lang="en">
   <head>
       <meta charset="UTF-8">
       <title>Server Management</title>
       <link rel="stylesheet" href="/static/styles.css">
   </head>
   <body>
       <h1>Server Management Dashboard</h1>
       <div id="server-list"></div>

       <script src="/static/scripts.js"></script>
   </body>
   </html>
   ```

5. **`styles.css`:**
   ```css
   body {
       font-family: Arial, sans-serif;
   }

   #server-list {
       list-style-type: none;
       padding-left: 0;
   }
   ```

6. **`scripts.js`:**
   ```javascript
   document.addEventListener("DOMContentLoaded", function() {
       const serverList = document.getElementById('server-list');
       
       // Implementa la lógica HTMX para cargar y actualizar la lista de servidores.
   });
   ```

### Dependencias:
1. **FastAPI:**
   - `pip install fastapi uvicorn`
   
2. **SQLAlchemy:**
   - `pip install sqlalchemy`

3. **HTMX:**
   - Asegúrate de que el entorno local soporte HTMX para la interactividad.

### Ejecución del Servidor:
1. Instala las dependencias necesarias.
```bash
pip install fastapi uvicorn
```
2. Ejecuta el servidor FastAPI.
```bash
uvicorn backend.main_output:app --reload
```

Este plan técnico detallado proporciona una estructura clara y separada para la arquitectura del sistema, asegurando que tanto el frontend como el backend estén bien definidos y separados.