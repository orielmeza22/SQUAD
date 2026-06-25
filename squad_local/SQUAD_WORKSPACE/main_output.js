// main_output.js

const express = require('express');
const bodyParser = require('body-parser');
const sqlite3 = require('sqlite3').verbose();

const app = express();
app.use(bodyParser.json());

let db;

async function connectToDatabase() {
  try {
    db = await new Promise((resolve, reject) => {
      const database = new sqlite3.Database('./database.sqlite', (err) => {
        if (err) {
          console.error("Error al conectar a la base de datos:", err.message);
          reject(err);
        } else {
          console.log("Conectado a la base de datos");
          resolve(database);
        }
      });
    });
  } catch (error) {
    console.error(error);
  }
}

connectToDatabase();

function validateFields(requiredFields, body) {
  for (const field of requiredFields) {
    if (!body[field]) {
      return false;
    }
  }
  return true;
}

app.post('/api/candidatos', async (req, res) => {
  const { nombre, apellido, email } = req.body;

  if (!validateFields(['nombre', 'apellido', 'email'], req.body)) {
    return res.status(400).send("Los campos 'nombre', 'apellido' y 'email' son obligatorios");
  }

  try {
    const result = await new Promise((resolve, reject) => {
      db.run('INSERT INTO Candidato (nombre, apellido, email) VALUES (?, ?, ?)', [nombre, apellido, email.toLowerCase()], function(err) {
        if (err) {
          reject(err);
        } else {
          resolve({ id: this.lastID });
        }
      });
    });
    res.send(result);
  } catch (error) {
    res.status(500).send("Error al insertar el candidato");
  }
});

app.get('/api/candidatos/:id', async (req, res) => {
  const { id } = req.params;

  try {
    const row = await new Promise((resolve, reject) => {
      db.get('SELECT * FROM Candidato WHERE id = ?', [id], function(err, row) {
        if (err) {
          reject(err);
        } else {
          resolve(row);
        }
      });
    });

    if (!row) {
      return res.status(404).send("Candidato no encontrado");
    }

    res.send(row);
  } catch (error) {
    res.status(500).send("Error al obtener el candidato");
  }
});

app.post('/api/experiencia-laboral', async (req, res) => {
  const { candidato_id, titulo_puesto, empresa } = req.body;

  if (!validateFields(['candidato_id', 'titulo_puesto', 'empresa'], req.body)) {
    return res.status(400).send("Los campos 'candidato_id', 'titulo_puesto' y 'empresa' son obligatorios");
  }

  try {
    const result = await new Promise((resolve, reject) => {
      db.run('INSERT INTO ExperienciaLaboral (candidato_id, titulo_puesto, empresa) VALUES (?, ?, ?)', [candidato_id, titulo_puesto, empresa], function(err) {
        if (err) {
          reject(err);
        } else {
          resolve({ id: this.lastID });
        }
      });
    });
    res.send(result);
  } catch (error) {
    res.status(500).send("Error al insertar la experiencia laboral");
  }
});

app.post('/api/educacion', async (req, res) => {
  const { candidato_id, nombre_institucion, titulo_obtenido } = req.body;

  if (!validateFields(['candidato_id', 'nombre_institucion', 'titulo_obtenido'], req.body)) {
    return res.status(400).send("Los campos 'candidato_id', 'nombre_institucion' y 'titulo_obtenido' son obligatorios");
  }

  try {
    const result = await new Promise((resolve, reject) => {
      db.run('INSERT INTO Educacion (candidato_id, nombre_institucion, titulo_obtenido) VALUES (?, ?, ?)', [candidato_id, nombre_institucion, titulo_obtenido], function(err) {
        if (err) {
          reject(err);
        } else {
          resolve({ id: this.lastID });
        }
      });
    });
    res.send(result);
  } catch (error) {
    res.status(500).send("Error al insertar el estudio");
  }
});

app.post('/api/habilidades-certificaciones', async (req, res) => {
  const { candidato_id, habilidad_certificacion } = req.body;

  if (!validateFields(['candidato_id', 'habilidad_certificacion'], req.body)) {
    return res.status(400).send("Los campos 'candidato_id' y 'habilidad_certificacion' son obligatorios");
  }

  try {
    const result = await new Promise((resolve, reject) => {
      db.run('INSERT INTO HabilidadesCertificaciones (candidato_id, habilidad_certificacion) VALUES (?, ?)', [candidato_id, habilidad_certificacion], function(err) {
        if (err) {
          reject(err);
        } else {
          resolve({ id: this.lastID });
        }
      });
    });
    res.send(result);
  } catch (error) {
    res.status(500).send("Error al insertar la habilidad/certificación");
  }
});

app.get('/api/generar-cv/:id', async (req, res) => {
  const { id } = req.params;

  try {
    const row = await new Promise((resolve, reject) => {
      db.get('SELECT * FROM Candidato WHERE id = ?', [id], function(err, row) {
        if (err) {
          reject(err);
        } else {
          resolve(row);
        }
      });
    });

    if (!row) {
      return res.status(404).send("Candidato no encontrado");
    }

    res.send(row);
  } catch (error) {
    res.status(500).send("Error al obtener el candidato");
  }
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Servidor escuchando en el puerto ${PORT}`);
});