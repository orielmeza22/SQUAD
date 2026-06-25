const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const app = express();
const PORT = process.env.PORT || 3000;

// Middleware para manejar JSON en la solicitud
app.use(express.json());
app.use(express.static('public')); // Servir archivos estáticos desde la carpeta 'public'

// Conectar a la base de datos SQLite y crear la tabla si no existe
let db = new sqlite3.Database('db.sqlite3', (err) => {
db.run("PRAGMA journal_mode=WAL;");
db.run("PRAGMA busy_timeout=5000;");
  if (err) {
    return console.error(err.message);
  }
  console.log('Connected to the SQlite database.');

  // Crear la tabla turnos si no existe
  db.run(`CREATE TABLE IF NOT EXISTS turnos (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      nombreTurno TEXT NOT NULL,
      diasActividad TEXT NOT NULL
  )`, (err) => {
    if (err) {
      return console.error(err.message);
    }
    console.log('Table created successfully.');
  });
});

// Ruta para crear un nuevo turno
app.post('/turnos', async (req, res) => {
  const { nombreTurno, diasActividad } = req.body;
  
  // Implementar lógica para guardar el turno en la base de datos SQLite
  db.run(`INSERT INTO turnos (nombreTurno, diasActividad) VALUES (?, ?)`, [nombreTurno, diasActividad], function(err) {
    if (err) {
      return res.status(500).send('Error al crear el turno');
    }
    res.status(201).send('Turno creado exitosamente');
  });
});

// Ruta para obtener todos los turnos
app.get('/turnos', async (req, res) => {
  db.all('SELECT * FROM turnos', [], (err, rows) => {
    if (err) {
      return res.status(500).send('Error al obtener los turnos');
    }
    res.json(rows);
  });
});

// Ruta para obtener todos los turnos
app.get('/turnos', async (req, res) => {
  db.all('SELECT * FROM turnos', [], (err, rows) => {
    if (err) {
      return res.status(500).send('Error al obtener los turnos');
    }
    res.json(rows);
  });
});

// Iniciar el servidor
app.listen(PORT, () => {
  console.log(`Servidor escuchando en el puerto ${PORT}`);
});