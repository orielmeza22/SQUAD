const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const bodyParser = require('body-parser');
const path = require('path');

const app = express();
app.use(bodyParser.json());

// Servir archivos estáticos (index.html, styles.css, scripts.js)
app.use(express.static(path.join(__dirname)));

// Conectar a la base de datos SQLite
const db = new sqlite3.Database(path.join(__dirname, 'database.sqlite'), (err) => {
  if (err) {
    return console.error(err.message);
  }
  db.run("PRAGMA journal_mode=WAL;");
  db.run("PRAGMA busy_timeout=5000;");
  console.log('Connected to the SQLite database.');
});

// Ruta para crear un candidato
app.post('/api/candidatos', (req, res) => {
  const { nombre, apellido, email, telefono, direccion, fecha_nacimiento, ciudad_residencia, nacionalidad } = req.body;
  db.run(`INSERT INTO Candidato (nombre, apellido, email, telefono, direccion, fecha_nacimiento, ciudad_residencia, nacionalidad) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`, 
    [nombre, apellido, email, telefono, direccion, fecha_nacimiento, ciudad_residencia, nacionalidad], 
    function(err) {
      if (err) {
        return res.status(500).json({ error: err.message });
      }
      res.json({ id: this.lastID });
    });
});

// Ruta para obtener un candidato por ID
app.get('/api/candidatos/:id', (req, res) => {
  const { id } = req.params;
  db.get(`SELECT * FROM Candidato WHERE id = ?`, [id], (err, row) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    res.json(row);
  });
});

// Ruta para agregar experiencia laboral
app.post('/api/experiencia-laboral', (req, res) => {
  const { candidato_id, titulo_puesto, empresa, lugar_trabajo, fecha_inicio, fecha_fin, descripcion_responsabilidades } = req.body;
  db.run(`INSERT INTO ExperienciaLaboral (candidato_id, titulo_puesto, empresa, lugar_trabajo, fecha_inicio, fecha_fin, descripcion_responsabilidades) VALUES (?, ?, ?, ?, ?, ?, ?)`, 
    [candidato_id, titulo_puesto, empresa, lugar_trabajo, fecha_inicio, fecha_fin, descripcion_responsabilidades], 
    function(err) {
      if (err) {
        return res.status(500).json({ error: err.message });
      }
      res.json({ id: this.lastID });
    });
});

// Ruta para agregar estudios
app.post('/api/educacion', (req, res) => {
  const { candidato_id, nombre_institucion, titulo_obtenido, anio_graduacion } = req.body;
  db.run(`INSERT INTO Educacion (candidato_id, nombre_institucion, titulo_obtenido, anio_graduacion) VALUES (?, ?, ?, ?)`, 
    [candidato_id, nombre_institucion, titulo_obtenido, anio_graduacion], 
    function(err) {
      if (err) {
        return res.status(500).json({ error: err.message });
      }
      res.json({ id: this.lastID });
    });
});

// Ruta para agregar habilidades/certificaciones
app.post('/api/habilidades-certificaciones', (req, res) => {
  const { candidato_id, habilidad_certificacion } = req.body;
  db.run(`INSERT INTO HabilidadesCertificaciones (candidato_id, habilidad_certificacion) VALUES (?, ?)`, 
    [candidato_id, habilidad_certificacion], 
    function(err) {
      if (err) {
        return res.status(500).json({ error: err.message });
      }
      res.json({ id: this.lastID });
    });
});

// Ruta para generar CV
app.get('/api/generar-cv/:id', (req, res) => {
  const { id } = req.params;
  // Lógica para generar el CV en PDF o Word
  res.send(`Generando CV para candidato con ID ${id}`);
});

// Escuchar en el puerto definido por la variable de entorno PORT
const port = process.env.PORT || 3000;
app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});