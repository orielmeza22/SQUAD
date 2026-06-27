STACK: FASTAPI_HTMX

# Especificación de Software (SPEC)

## Resumen del Proyecto:
El proyecto consiste en desarrollar una aplicación web para gestionar turnos, utilizando el stack tecnológico FASTAPI_HTMX. Esta aplicación permitirá a los usuarios crear, modificar y eliminar turnos, así como consultar información sobre ellos.

## Arquitectura del Sistema:

### 1. Backend (Servidor)
El backend se implementará usando FastAPI, una biblioteca de Python para construir APIs web rápidas y eficientes. HTMX será utilizado para proporcionar interactividad en el frontend sin necesidad de recargar la página completa.

#### Archivos del Backend:
- **/backend/app.py**: Contiene las rutas y funciones principales de FastAPI.
- **/backend/models.py**: Define los modelos de datos que se utilizarán con SQLite.
- **/backend/routes.py**: Contiene las rutas específicas para CRUD (Crear, Leer, Actualizar, Eliminar) de turnos.

### 2. Frontend (Cliente)
El frontend será construido utilizando HTMX y HTML5. El diseño básico se implementará usando CSS y JavaScript minimalista para manejar la interactividad con el backend.

#### Archivos del Frontend:
- **/frontend/index.html**: Contiene el HTML básico de la página principal.
- **/frontend/styles.css**: Define los estilos CSS necesarios.
- **/frontend/scripts.js**: Contiene el código JavaScript necesario para interactuar con el backend y HTMX.

### 3. Base de Datos
La base de datos se implementará usando SQLite, que es una opción ligera y fácilmente manejable para proyectos pequeños o prototipos.

#### Archivos de la Base de Datos:
- **/database/db.py**: Contiene las funciones para interactuar con SQLite.
  
### 4. Git
Se utilizará Git para el control del código fuente, permitiendo versionar y colaborar en el desarrollo del proyecto.

## Detalles Técnicos:

### Backend (FastAPI_HTMX)
1. **Modelos de Datos**:
   - Se definirán modelos de datos usando SQLAlchemy, una biblioteca que facilita la interacción con SQLite.
   
2. **Rutas de FastAPI**:
   ```python
   from fastapi import FastAPI, HTTPException
   
   app = FastAPI()
   
   @app.post("/turnos/", response_model=Turno)
   async def crear_turno(turno: Turno):
       # Implementar lógica para guardar el turno en la base de datos.
       
   @app.get("/turnos/{id}", response_model=Turno)
   async def obtener_turno(id: int):
       # Implementar lógica para recuperar un turno específico.
       
   @app.put("/turnos/{id}", response_model=Turno)
   async def actualizar_turno(id: int, turno: Turno):
       # Implementar lógica para actualizar un turno en la base de datos.
       
   @app.delete("/turnos/{id}")
   async def eliminar_turno(id: int):
       # Implementar lógica para eliminar un turno de la base de datos.
   ```

### Frontend (HTMX)
1. **Interacción con el Backend**:
   - Se utilizará HTMX para enviar peticiones AJAX sin recargar la página completa, lo que mejora la interactividad del frontend.

2. **HTML5 y CSS**:
   ```html
   <!DOCTYPE html>
   <html lang="es">
   <head>
       <meta charset="UTF-8">
       <title>Administración de Turnos</title>
       <link rel="stylesheet" href="/frontend/styles.css">
   </head>
   <body>
       <!-- Contenido HTML básico -->
       <script src="/frontend/scripts.js"></script>
   </body>
   </html>
   ```

### Base de Datos (SQLite)
1. **Interacción con SQLite**:
   ```python
   from sqlalchemy import create_engine, Column, Integer, String
   
   engine = create_engine('sqlite:///turnos.db')
   
   class Turno(Base):
       __tablename__ = 'turnos'
       
       id = Column(Integer, primary_key=True)
       nombre = Column(String(100))
       fecha = Column(Date)
       hora = Column(Time)
       
   Base.metadata.create_all(engine)
   ```

### Git
- **Control de Versiones**:
  - Se utilizará Git para versionar el código y permitir colaboración en el desarrollo del proyecto.
  
## Conclusion

La arquitectura FASTAPI_HTMX proporciona una solución robusta y eficiente para la gestión de turnos, combinando la potencia de FastAPI para el backend con HTMX para mejorar la interactividad del frontend. Este stack es adecuado para proyectos que requieren una interfaz web dinámica y eficiente sin recargar páginas completas.