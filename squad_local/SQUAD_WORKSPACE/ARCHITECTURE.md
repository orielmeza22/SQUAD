### Especificación de Software (SPEC)

#### 1. Introducción

Este documento describe el diseño, desarrollo y estructura de una aplicación web para generar currículos personalizados específicamente diseñada para profesionales de Help Desk Junior. La aplicación se implementará utilizando Node.js con Express como framework backend, y HTML5/JavaScript en el frontend para una interfaz intuitiva y fácil de usar.

#### 2. Arquitectura del Sistema

La arquitectura seguirá un estilo **MVC (Model-View-Controller)**, que divide la aplicación en tres capas principales:

1. **Modelo**: Representa los datos y las reglas de negocio.
2. **Vista**: Es la interfaz gráfica para el usuario.
3. **Controlador**: Actúa como intermediario entre el modelo y la vista.

#### 3. Tecnologías Utilizadas

- **Backend**:
  - Node.js
  - Express.js
  - SQLite (para almacenamiento de datos)
  - CORS (Cross-Origin Resource Sharing) para manejo de solicitudes cruzadas

- **Frontend**:
  - HTML5/JavaScript
  - Bootstrap (opcional, para estilos y estructura básica)

#### 4. Estructura del Proyecto

La estructura del proyecto se dividirá en las siguientes carpetas:

```
proyecto-cv-helpdesk-junior/
├── backend/
│   ├── controllers/
│   │   └── usuarios.js
│   │   └── experiencia-laboral.js
│   │   └── habilidades-tecnicas.js
│   │   └── educacion.js
│   ├── models/
│   │   └── usuarios.js
│   │   └── experiencia-laboral.js
│   │   └── habilidades-tecnicas.js
│   │   └── educacion.js
│   ├── routes/
│   │   └── usuarios.js
│   │   └── experiencia-laboral.js
│   │   └── habilidades-tecnicas.js
│   │   └── educacion.js
│   ├── app.js
│   └── db.js
├── frontend/
│   ├── index.html
│   ├── styles.css (opcional)
│   ├── scripts.js
│   ├── forms/
│   │   └── experiencia-laboral-form.js
│   │   └── habilidades-tecnicas-form.js
│   │   └── educacion-form.js
├── public/
└── .gitignore
```

#### 5. Diseño de la Aplicación

##### 5.1 Página Principal (index.html)

La página principal será un formulario HTML básico que permitirá al usuario ingresar sus datos personales. La estructura básica del HTML sería:

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Generador de CV</title>
</head>
<body>
    <h1>Generador de CV para Help Desk Junior</h1>
    <form id="user-form">
        <label for="nombre">Nombre:</label><br>
        <input type="text" id="nombre" name="nombre"><br>

        <label for="apellido">Apellido:</label><br>
        <input type="text" id="apellido" name="apellido"><br>

        <label for="email">Email:</label><br>
        <input type="email" id="email" name="email"><br>

        <label for="telefono">Teléfono:</label><br>
        <input type="tel" id="telefono" name="telefono"><br>

        <button type="submit">Guardar</button>
    </form>

    <!-- JavaScript para manejar el formulario -->
    <script src="scripts.js"></script>
</body>
</html>
```

##### 5.2 Formularios de Experiencia Laboral, Habilidades Técnicas y Educación

Cada uno de estos formularios contendrá campos específicos para agregar información relevante al perfil del profesional.

#### 6. Backend (Express)

El backend se implementará utilizando Express.js y SQLite como base de datos.

##### 6.1 Modelos (models/usuarios.js, experiencia-laboral.js, habilidades-tecnicas.js, educacion.js)

Estos archivos contendrán la lógica para crear, leer, actualizar y eliminar (CRUD) los diferentes tipos de información del usuario:

```javascript
// models/usuarios.js

const sqlite3 = require('sqlite3').verbose();
let db = new sqlite3.Database('./database.db');

exports.createUsuario = async function(nombre, apellido, email, telefono){
    let sql = `INSERT INTO Usuarios (nombre, apellido, email, telefono) VALUES (?, ?, ?, ?);`;
    await db.run(sql,[nombre,apellido,email,telefono]);
};

exports.readUsuarios = async function(){
    let usuarios = [];
    const stmt = db.prepare("SELECT * FROM Usuarios");
    while(stmt.step()){
        usuarios.push({
            id_usuario: stmt.getColumn('id_usuario'),
            nombre: stmt.getColumn('nombre'),
            apellido: stmt.getColumn('apellido'),
            email: stmt.getColumn('email'),
            telefono: stmt.getColumn('telefono')
        });
    }
    stmt.finalize();
    return usuarios;
};

exports.updateUsuario = async function(id, nombre, apellido, email, telefono){
    let sql = `UPDATE Usuarios SET nombre = ?, apellido = ?, email = ?, telefono = ? WHERE id_usuario = ?;`;
    await db.run(sql,[nombre,apellido,email,telefono,id]);
};

exports.deleteUsuario = async function(id){
    let sql = "DELETE FROM Usuarios WHERE id_usuario = ?";
    await db.run(sql,[id]);
};
```

##### 6.2 Rutas (routes/usuarios.js, experiencia-laboral.js, habilidades-tecnicas.js, educacion.js)

Estas rutas manejarán las solicitudes HTTP y lógica de negocio para cada tipo de recurso.

```javascript
// routes/usuarios.js

const express = require('express');
const { createUsuario, readUsuarios } = require('../controllers/usuarios');

const router = express.Router();

router.post('/', async (req, res) => {
    const nombre = req.body.nombre;
    const apellido = req.body.apellido;
    const email = req.body.email;
    const telefono = req.body.telefono;

    await createUsuario(nombre, apellido, email, telefono);
    res.json({ message: 'Usuario creado' });
});

router.get('/', async (req, res) => {
    const usuarios = await readUsuarios();
    res.json(usuarios);
});

module.exports = router;
```

##### 6.3 Generación del CV

El endpoint `/api/generar-cv/{id_usuario}` se encargará de generar el currículo HTML basado en la información del usuario.

```javascript
// controllers/educacion.js

const { createEducacion, readEducacion } = require('../models/educacion');
const { generateCvHtml } = require('./generate-cv');

exports.createEducacion = async function(institucion, titulo_obtenido, anio_graduacion){
    let sql = `INSERT INTO Educacion (institucion, titulo_obtenido, anio_graduacion) VALUES (?, ?, ?);`;
    await db.run(sql,[institucion,titulo_obtenido,anio_graduacion]);
};

exports.readEducacion = async function(){
    const educaciones = [];
    const stmt = db.prepare("SELECT * FROM Educacion");
    while(stmt.step()){
        educaciones.push({
            id_educacion: stmt.getColumn('id_educacion'),
            institucion: stmt.getColumn('institucion'),
            titulo_obtenido: stmt.getColumn('titulo_obtenido'),
            anio_graduacion: stmt.getColumn('anio_graduacion')
        });
    }
    stmt.finalize();
    return educaciones;
};
```

#### 7. Frontend (HTML/JavaScript)

El frontend se implementará utilizando HTML5 y JavaScript para manejar la interacción con el usuario.

##### 7.1 Formularios de Experiencia Laboral, Habilidades Técnicas y Educación

Cada uno de estos formularios contendrá campos específicos para agregar información relevante al perfil del profesional.

```html
<!-- frontend/forms/experiencia-laboral-form.js -->
document.getElementById('experiencia-laboral-form').addEventListener('submit', function(event){
    event.preventDefault();
    const puesto = document.getElementById('puesto').value;
    const empresa = document.getElementById('empresa').value;
    const fechaInicio = document.getElementById('fecha-inicio').value;
    const fechaFin = document.getElementById('fecha-fin').value;
    const responsabilidades = document.getElementById('responsabilidades').value;
    const logros = document.getElementById('logros').value;

    // Lógica para enviar la información al backend
});
```

#### 8. Reglas de negocio y validaciones

Las reglas de negocio se implementarán en el backend para asegurar que los datos ingresados sean válidos.

```javascript
// models/usuarios.js (ejemplo)
exports.createUsuario = async function(nombre, apellido, email, telefono){
    if(!nombre || !apellido || !email || !telefono) {
        throw new Error('Todos los campos son obligatorios');
    }
    // Lógica para crear el usuario
};
```

#### 9. Previsualización y Manejo de Errores

Para la previsualización, se utilizará una estructura estándar HTML5 sin necesidad de un bundle como Vue o React. Los errores se mostrarán al usuario con mensajes claros en caso de problemas durante la creación o edición del CV.

#### 10. Integración y Pruebas

La integración y pruebas se realizarán utilizando herramientas como Mocha para las pruebas unitarias, Jest para las pruebas de rendimiento, y Supertest para hacer pruebas de API.

### Conclusión

Este plan detalla la arquitectura y especificaciones técnicas necesarias para desarrollar una aplicación web eficiente y fácilmente utilizable para profesionales de Help Desk Junior. La implementación seguirá un enfoque modular que facilita el desarrollo, pruebas y mantenimiento del proyecto.

Para ejecutar este proyecto localmente, asegúrate de tener instalado Node.js y SQLite3, y luego ejecuta los siguientes comandos:

```bash
# Clona el repositorio
git clone <URL_DEL_REPOSITORIO>

# Navega al directorio del proyecto
cd proyecto-cv-helpdesk-junior

# Instala las dependencias
npm install

# Inicia el servidor
node app.js
```

Este plan proporciona una base sólida para desarrollar y mantener la aplicación de manera eficiente.