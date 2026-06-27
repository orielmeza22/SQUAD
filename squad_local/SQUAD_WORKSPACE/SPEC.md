### Especificación de Software (SPEC) para una App de Gestión de Turnos

#### 1. **Introducción**
Esta especificación describe el diseño y desarrollo de una aplicación web para la gestión de turnos, utilizando únicamente las tecnologías disponibles en el entorno local: Node.js, Docker, Python y Git.

#### 2. **Objetivos del Proyecto**
- Crear una aplicación web que permita a los usuarios gestionar turnos de manera eficiente.
- Implementar funcionalidades básicas como la creación, edición y eliminación de turnos.
- Proporcionar un sistema de autenticación para asegurar el acceso a las funciones del sistema.

#### 3. **Arquitectura de la Aplicación**

**3.1. Arquitectura Frontend**
El frontend será desarrollado utilizando HTML5, CSS y JavaScript nativos (sin frameworks como Vue o React). Esto se debe a que el entorno no soporta Node/NPM para ejecutar un servidor web.

- **HTML5**: Se utilizará para la estructuración de la página principal (`index.html`).
- **CSS**: Para estilos y diseño.
- **JavaScript**: Para lógica del frontend, eventos y interacción con el backend.

**3.2. Arquitectura Backend**
El backend será desarrollado en Python utilizando Flask como framework web.

- **Flask**: Framework web de Python para manejar las peticiones HTTP y responder con JSON.
- **SQLite**: Base de datos local para almacenar los datos del sistema (turnos, usuarios).

**3.3. Arquitectura de Contenedores**
La aplicación será contenedida utilizando Docker.

- **Dockerfile**: Script que define cómo se construirá el contenedor y qué imágenes base se utilizarán.
- **docker-compose.yml**: Script para iniciar los contenedores necesarios (backend, frontend).

#### 4. **Funcionalidades del Sistema**

**4.1. Gestión de Turnos**
- Crear un turno
- Editar un turno existente
- Eliminar un turno
- Ver todos los turnos

**4.2. Autenticación y Autorización**
- Registro de usuarios
- Inicio de sesión
- Control de roles (administrador, usuario)

#### 5. **Especificaciones Técnicas**

**5.1. Especificaciones del Backend en Python con Flask**

```python
# app.py

from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DATABASE = 'turnos.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/turnos', methods=['GET'])
def get_turnos():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM turnos')
    rows = cur.fetchall()
    return jsonify(rows)

@app.route('/turnos/<int:turno_id>', methods=['PUT'])
def update_turno(turno_id):
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('UPDATE turnos SET nombre=:nombre, fecha=:fecha WHERE id=:id', data)
    conn.commit()
    return jsonify({'message': 'Turno actualizado'})

@app.route('/turnos/<int:turno_id>', methods=['DELETE'])
def delete_turno(turno_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM turnos WHERE id=:id', {'id': turno_id})
    conn.commit()
    return jsonify({'message': 'Turno eliminado'})

@app.route('/turnos', methods=['POST'])
def create_turno():
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO turnos (nombre, fecha) VALUES (:nombre, :fecha)', data)
    conn.commit()
    return jsonify({'message': 'Turno creado'})

if __name__ == '__main__':
    app.run(debug=True)
```

**5.2. Especificaciones del Frontend en HTML y JavaScript**

```html
<!-- index.html -->
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>App de Gestión de Turnos</title>
  <style>
    /* Estilos básicos */
  </style>
</head>
<body>
  <h1>Gestión de Turnos</h1>

  <!-- Formulario para crear un turno -->
  <form id="create-form">
    <input type="text" name="nombre" placeholder="Nombre del turno">
    <input type="date" name="fecha" placeholder="Fecha del turno">
    <button type="submit">Crear Turno</button>
  </form>

  <!-- Formulario para editar un turno -->
  <form id="edit-form">
    <input type="text" name="nombre" placeholder="Nombre del turno">
    <input type="date" name="fecha" placeholder="Fecha del turno">
    <button type="submit">Guardar Cambios</button>
  </form>

  <!-- Botón para eliminar un turno -->
  <button id="delete-btn">Eliminar Turno</button>

  <script src="/static/script.js"></script>
</body>
</html>
```

```javascript
// script.js
document.getElementById('create-form').addEventListener('submit', function(event) {
    event.preventDefault();
    const nombre = document.querySelector('#create-form input[name="nombre"]').value;
    const fecha = document.querySelector('#create-form input[name="fecha"]').value;

    fetch('/turnos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nombre, fecha })
    }).then(response => response.json())
      .then(data => console.log('Success:', data))
      .catch((error) => console.error('Error:', error));
});

document.getElementById('edit-form').addEventListener('submit', function(event) {
    event.preventDefault();
    const id = document.querySelector('#edit-form input[name="id"]').value;
    const nombre = document.querySelector('#edit-form input[name="nombre"]').value;
    const fecha = document.querySelector('#edit-form input[name="fecha"]').value;

    fetch(`/turnos/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nombre, fecha })
    }).then(response => response.json())
      .then(data => console.log('Success:', data))
      .catch((error) => console.error('Error:', error));
});

document.getElementById('delete-btn').addEventListener('click', function(event) {
    event.preventDefault();
    const id = document.querySelector('#edit-form input[name="id"]').value;

    fetch(`/turnos/${id}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' }
    }).then(response => response.json())
      .then(data => console.log('Success:', data))
      .catch((error) => console.error('Error:', error));
});
```

#### 6. **Especificaciones del Contenedor**

**6.1. Dockerfile**

```Dockerfile
# Usa la imagen base de Python para Flask
FROM python:3.8-slim

# Establece el directorio de trabajo como /app
WORKDIR /app

# Copia el archivo app.py y las dependencias del sistema de archivos host al contenedor
COPY . .

# Instala las dependencias necesarias
RUN pip install flask sqlite3

# Exponga la puerta 5000 para Flask
EXPOSE 5000

# Ejecuta el servidor web
CMD ["python", "app.py"]
```

**6.2. docker-compose.yml**

```yaml
version: '3'
services:
  backend:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./data:/var/www/html/turnos.db
```

#### 7. **Especificaciones de Pruebas y Documentación**

**7.1. Especificaciones de Pruebas**
- Se implementarán pruebas unitarias para cada función del backend.
- Se realizarán pruebas de integración para comprobar el funcionamiento completo del sistema.

**7.2. Documentación**
- Se documentará la arquitectura y las especificaciones técnicas en un archivo README.md.
- Se incluirá una guía de instalación y configuración detallada.

#### 8. **Especificaciones de Despliegue**

La aplicación se desplegará utilizando Docker, asegurando que el backend esté ejecutándose y accesible a través del puerto 5000 en la máquina local.

---

Este plan técnico proporciona una base sólida para desarrollar una aplicación de gestión de turnos utilizando las tecnologías disponibles. Los siguientes pasos serían seguir con el desarrollo, pruebas y despliegue según estas especificaciones.