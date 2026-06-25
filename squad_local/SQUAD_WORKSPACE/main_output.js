// main_output.js

const express = require('express');
const bodyParser = require('body-parser');
const { open } = require('sqlite');

const app = express();
app.use(bodyParser.json());

// Conectar a SQLite
let db;
open({
  filename: './database.sqlite',
  driver: require('sqlite3').verbose()
}).then(database => {
  console.log("Conectado a la base de datos");
  db = database;
});

// Crear candidato
app.post('/api/candidatos', (req, res) => {
  const { nombre, apellido, email } = req.body;
  
  // Validación
  if (!nombre || !apellido || !email) {
    return res.status(400).send("Los campos 'nombre', 'apellido' y 'email' son obligatorios");
  }

  db.run('INSERT INTO Candidato (nombre, apellido, email) VALUES (?, ?, ?)', [nombre, apellido, email.toLowerCase()], function(err) {
    if (err) {
      return res.status(500).send("Error al crear el candidato");
    }
    res.send({ id: this.lastID });
  });
});

// Obtener candidato por ID
app.get('/api/candidatos/:id', (req, res) => {
  const { id } = req.params;
  
  db.get('SELECT * FROM Candidato WHERE id = ?', [id], function(err, row) {
    if (err) {
      return res.status(500).send("Error al obtener el candidato");
    }
    
    if (!row) {
      return res.status(404).send("Candidato no encontrado");
    }

    res.send(row);
  });
});

// Agregar experiencia laboral
app.post('/api/experiencia-laboral', (req, res) => {
  const { candidato_id, titulo_puesto, empresa } = req.body;
  
  if (!candidato_id || !titulo_puesto || !empresa) {
    return res.status(400).send("Los campos 'candidato_id', 'titulo_puesto' y 'empresa' son obligatorios");
  }

  db.run('INSERT INTO ExperienciaLaboral (candidato_id, titulo_puesto, empresa) VALUES (?, ?, ?)', [candidato_id, titulo_puesto, empresa], function(err) {
    if (err) {
      return res.status(500).send("Error al agregar experiencia laboral");
    }
    res.send({ id: this.lastID });
  });
});

// Agregar estudio
app.post('/api/educacion', (req, res) => {
  const { candidato_id, nombre_institucion, titulo_obtenido } = req.body;
  
  if (!candidato_id || !nombre_institucion || !titulo_obtenido) {
    return res.status(400).send("Los campos 'candidato_id', 'nombre_institucion' y 'titulo_obtenido' son obligatorios");
  }

  db.run('INSERT INTO Educacion (candidato_id, nombre_institucion, titulo_obtenido) VALUES (?, ?, ?)', [candidato_id, nombre_institucion, titulo_obtenido], function(err) {
    if (err) {
      return res.status(500).send("Error al agregar estudio");
    }
    res.send({ id: this.lastID });
  });
});

// Agregar habilidad/certificación
app.post('/api/habilidades-certificaciones', (req, res) => {
  const { candidato_id, habilidad_certificacion } = req.body;
  
  if (!candidato_id || !habilidad_certificacion) {
    return res.status(400).send("Los campos 'candidato_id' y 'habilidad_certificacion' son obligatorios");
  }

  db.run('INSERT INTO HabilidadesCertificaciones (candidato_id, habilidad_certificacion) VALUES (?, ?)', [candidato_id, habilidad_certificacion], function(err) {
    if (err) {
      return res.status(500).send("Error al agregar habilidad/certificación");
    }
    res.send({ id: this.lastID });
  });
});

// Generar CV
app.get('/api/generar-cv/:id', (req, res) => {
  const { id } = req.params;
  
  db.get('SELECT * FROM Candidato WHERE id = ?', [id], function(err, row) {
    if (err) {
      return res.status(500).send("Error al obtener el candidato");
    }
    
    if (!row) {
      return res.status(404).send("Candidato no encontrado");
    }

    // Generar currículum vitae
    const cv = `
      Nombre: ${row.nombre} ${row.apellido}
      Email: ${row.email}
      Teléfono: ${row.telefono || 'No especificado'}
      Dirección: ${row.direccion || 'No especificada'}
      Fecha de Nacimiento: ${row.fecha_nacimiento || 'No especificada'}
      Ciudad de Residencia: ${row.ciudad_residencia || 'No especificada'}
      Nacionalidad: ${row.nacionalidad || 'No especificada'}
    `;
    res.send(cv);
  });
});

// Configurar servidor
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Servidor escuchando en el puerto ${PORT}`);
});

// Configurar servidor
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Servidor escuchando en el puerto ${PORT}`);
});
