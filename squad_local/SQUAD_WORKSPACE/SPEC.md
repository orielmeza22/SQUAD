### Especificación de Software (SPEC) para el Sistema de Gestión de Turnos

#### Resumen del Proyecto:
El objetivo es desarrollar un sistema de gestión de turnos completamente funcional utilizando únicamente las tecnologías disponibles en el entorno anfitrión local. El sistema debe ser capaz de gestionar la asignación y rotación de turnos, permitiendo a los usuarios crear, editar y eliminar turnos. Además, se espera que el sistema sea accesible directamente desde un navegador web sin necesidad de herramientas de compilación adicionales.

#### Restricciones:
- **Host Local**: Node.js, Docker, Python y Git están habilitados.
- **Restricción del Sistema Anfitrión**:
  - **Node.js**: Habilitado
  - **Docker**: Habilitado
  - **Python**: Habilitado
  - **Git**: Habilitado

#### Objetivo del Proyecto:
Crear un sistema de gestión de turnos que incluya las siguientes funcionalidades:
- Creación, edición y eliminación de turnos.
- Gestión de usuarios con roles específicos (administrador, supervisor, operario).
- Visualización de los turnos asignados en una interfaz intuitiva.

#### Arquitectura del Sistema:

##### Capa de Aplicación (API):
La capa de aplicación será construida utilizando Node.js. Se utilizará Express.js para el framework y se implementará un servidor RESTful que permitirá acceder a las funcionalidades CRUD (Crear, Leer, Actualizar, Eliminar) de los turnos.

##### Capa de Datos:
Se utilizará una base de datos SQLite local ya que es compatible con Node.js. La base de datos será utilizada para almacenar información sobre los usuarios y los turnos asignados.

##### Capa de Presentación (Frontend):
- **HTML5**: Se creará un archivo index.html estándar que se puede ejecutar directamente en el navegador local sin necesidad de herramientas de compilación.
- **CSS**: Se utilizará CSS básico para la presentación del contenido y estilos simples.

#### Implementación Detallada:

##### 1. Capa de Aplicación (API):

**1.1 Crear el Proyecto y Configurar Node.js:**
```bash
mkdir gestion-turnos && cd gestion-turnos
npm init -y
```

**1.2 Instalar Express.js:**
```bash
npm install express
```

**1.3 Crear el Archivo de Servidor (server.js):**

```javascript
const express = require('express');
const app = express();
const PORT = 3000;

// Middleware para manejar JSON en la solicitud
app.use(express.json());

// Ruta para crear un nuevo turno
app.post('/turnos', async (req, res) => {
    const { nombreTurno, diasActividad } = req.body;
    // Implementar lógica para guardar el turno en la base de datos SQLite
});

// Rutas para leer, actualizar y eliminar turnos
// ...

// Iniciar el servidor
app.listen(PORT, () => {
    console.log(`Servidor escuchando en el puerto ${PORT}`);
});
```

##### 2. Capa de Datos:

**2.1 Crear la Base de Datos SQLite:**
```bash
touch db.sqlite3 && sqlite3 db.sqlite3
```

**2.2 Crear la Tabla para los Turnos:**

```sql
CREATE TABLE IF NOT EXISTS turnos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombreTurno TEXT NOT NULL,
    diasActividad TEXT NOT NULL
);
```

##### 3. Capa de Presentación (Frontend):

**3.1 Crear el Archivo index.html:**
Este archivo será un HTML5 estándar que no requiere herramientas de compilación adicionales para ser ejecutado directamente en el navegador.

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Gestión de Turnos</title>
    <style>
        /* Estilos básicos */
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
        }
        h1 {
            text-align: center;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
    </style>
</head>
<body>
    <h1>Gestión de Turnos</h1>

    <!-- Tabla para mostrar los turnos -->
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Nombre del Turno</th>
                <th>Días de Actividad</th>
            </tr>
        </thead>
        <tbody id="turnosTable">
            <!-- Los datos se mostrarán aquí -->
        </tbody>
    </table>

    <!-- Formulario para agregar un nuevo turno -->
    <form action="/turnos" method="post">
        <label for="nombreTurno">Nombre del Turno:</label>
        <input type="text" id="nombreTurno" name="nombreTurno"><br><br>
        <label for="diasActividad">Días de Actividad (separados por comas):</label>
        <input type="text" id="diasActividad" name="diasActividad"><br><br>
        <button type="submit">Agregar Turno</button>
    </form>

    <!-- Script para manejar la interacción con el servidor -->
    <script src="/server.js"></script>
</body>
</html>
```

##### 4. Implementación de las Funcionalidades:

**4.1 Manejo de los Datos en Express:**

```javascript
// server.js

const express = require('express');
const app = express();
const PORT = 3000;

app.use(express.json());

// Ruta para crear un nuevo turno
app.post('/turnos', async (req, res) => {
    const { nombreTurno, diasActividad } = req.body;
    
    // Implementar lógica para guardar el turno en la base de datos SQLite
    // Ejemplo: 
    // await db.run(`INSERT INTO turnos (nombreTurno, diasActividad) VALUES (?, ?)`, [nombreTurno, diasActividad]);

    res.status(201).send('Turno creado exitosamente');
});

app.listen(PORT, () => {
    console.log(`Servidor escuchando en el puerto ${PORT}`);
});
```

**4.2 Manejo de la Interacción con el Frontend:**

```javascript
// server.js

// Implementar más rutas para leer, actualizar y eliminar turnos
// Ejemplo:
app.get('/turnos', (req, res) => {
    // Implementar lógica para obtener los turnos de la base de datos SQLite
    // Ejemplo:
    // const turnos = await db.all('SELECT * FROM turnos');
    // res.json(turnos);
    
    res.status(200).send('Turnos listos');
});
```

#### Conclusión:

El plan técnico detallado proporciona una arquitectura clara y funcional para el sistema de gestión de turnos. Se utiliza Node.js para la capa de aplicación, SQLite como base de datos local y HTML5 para la presentación del contenido. Este enfoque cumple con todas las restricciones del entorno anfitrión y garantiza una implementación sencilla y funcional sin necesidad de herramientas adicionales de compilación.

Para completar el sistema, se deben implementar las rutas restantes para manejar la lectura, actualización y eliminación de turnos. Además, se debe implementar la lógica específica para cada una de estas operaciones en la base de datos SQLite.