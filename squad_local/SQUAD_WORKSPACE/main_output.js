// main_output.js

const express = require('express');
const bodyParser = require('body-parser');
const { open } = require('sqlite');

const app = express();
app.use(bodyParser.json());

// Conectar a SQLite
const sqlite3 = require('sqlite3').verbose();
let db;

// Conectar a SQLite
function connectToDatabase() {
  return new Promise((resolve, reject) => {
    db = new sqlite3.Database('./database.sqlite', (err) => {
      if (err) {
        console.error("Error al conectar a la base de datos:", err.message);
        reject(err);
      } else {
        console.log("Conectado a la base de datos");
        resolve();
      }
    });
  });
}

connectToDatabase().catch(console.error);

// Crear candidato
app.post('/api/candidatos', (req, res) => {
  const { nombre, apellido, email } = req.body;
  
  // Validación
  if (!nombre || !apellido || !email) {
    return res.status(400).send("Los campos 'nombre', 'apellido' y 'email' son obligatorios");
  }

  const candidate = {
    nombre,
    apellido,
    email: email.toLowerCase()
  };

  // Insertar candidato
  db.run('INSERT INTO Candidato (nombre, apellido, email) VALUES (?, ?, ?)', [candidate.nombre, candidate.apellido, candidate.email], function(err) {
    if (err) {
      return res.status(500).send("Error al insertar el candidato");
    }
    res.send({ id: this.lastID });
  });
});

// Obtener candidato por ID
app.get('/api/candidatos/:id', (req, res) => {
  const { id } = req.params;
  
  db.get(`SELECT * FROM Candidato WHERE id = ?`, [id], function(err, row) {
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

  // Insertar experiencia laboral
  db.run('INSERT INTO ExperienciaLaboral (candidato_id, titulo_puesto, empresa) VALUES (?, ?, ?)', [candidato_id, titulo_puesto, empresa], function(err) {
    if (err) {
      return res.status(500).send("Error al insertar la experiencia laboral");
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

  // Insertar estudio
  db.run('INSERT INTO Educacion (candidato_id, nombre_institucion, titulo_obtenido) VALUES (?, ?, ?)', [candidato_id, nombre_institucion, titulo_obtenido], function(err) {
    if (err) {
      return res.status(500).send("Error al insertar el estudio");
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

  // Insertar habilidad/certificación
  db.run('INSERT INTO HabilidadesCertificaciones (candidato_id, habilidad_certificacion) VALUES (?, ?)', [candidato_id, habilidad_certificacion], function(err) {
    if (err) {
      return res.status(500).send("Error al insertar la habilidad/certificación");
    }
    res.send({ id: this.lastID });
  });
});

// Generar CV
app.get('/api/generar-cv/:id', (req, res) => {
  const { id } = req.params;
  
  db.get(`SELECT * FROM Candidato WHERE id = ?`, [id], function(err, row) {
    if (err) {
      return res.status(500).send("Error al obtener el candidato");
    }
    
    if (!row) {
      return res.status(404).send("Candidato no encontrado");
    }

    // Generar currículum vitae
    res.send(row);
  });
});

// Rutas

// Crear candidato
app.post('/api/candidatos', (req, res) => {
  const { nombre, apellido, email } = req.body;
  
  // Validación
  if (!nombre || !apellido || !email) {
    return res.status(400).send("Los campos 'nombre', 'apellido' y 'email' son obligatorios");
  }

  const candidate = {
    nombre,
    apellido,
    email: email.toLowerCase()
  };

  // Insertar candidato
  app.get('/api/candidatos/{id}', (req, res) => {
    const { id } = req.params;
    
    // Verificar si el candidato existe en la base de datos
    db.get(`SELECT * FROM Candidato WHERE id = ${id}`, function(err, row) {
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

    // Insertar experiencia laboral
  });

  // Agregar estudio
  app.post('/api/educacion', (req, res) => {
    const { candidato_id, nombre_institucion, titulo_obtenido } = req.body;
    
    if (!candidato_id || !nombre_institucion || !titulo_obtenido) {
      return res.status(400).send("Los campos 'candidato_id', 'nombre_institucion' y 'titulo_obtenido' son obligatorios");
    }

    // Insertar estudio
  });

  // Agregar habilidad/certificación
  app.post('/api/habilidades-certificaciones', (req, res) => {
    const { candidato_id, habilidad_certificacion } = req.body;
    
    if (!candidato_id || !habilidad_certificacion) {
      return res.status(400).send("Los campos 'candidato_id' y 'habilidad_certificacion' son obligatorios");
    }

    // Insertar habilidad/certificación
  });

  // Generar CV
  app.get('/api/generar-cv/{id}', (req, res) => {
    const { id } = req.params;
    
    db.get(`SELECT * FROM Candidato WHERE id = ${id}`, function(err, row) {
      if (err) {
        return res.status(500).send("Error al obtener el candidato");
      }
      
      if (!row) {
        return res.status(404).send("Candidato no encontrado");
      }

      // Generar currículum vitae
    });
  });

});

// Crear candidato
app.post('/api/candidatos', (req, res) => {
  const { nombre, apellido, email } = req.body;
  
  // Validación
  if (!nombre || !apellido || !email) {
    return res.status(400).send("Los campos 'nombre', 'apellido' y 'email' son obligatorios");
  }

  const candidate = {
    nombre,
    apellido,
    email: email.toLowerCase()
  };

  // Insertar candidato
  db.run('INSERT INTO Candidato (nombre, apellido, email) VALUES (?, ?, ?)', [candidate.nombre, candidate.apellido, candidate.email], function(err) {
    if (err) {
      return res.status(500).send("Error al crear el candidato");
    }
    res.send({ id: this.lastID });
  });
});

// Obtener Candidato por ID
app.get('/api/candidatos/:id', (req, res) => {
  const { id } = req.params;
  
  // Verificar si el candidato existe en la base de datos
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

// Agregar Experiencia Laboral
app.post('/api/experiencia-laboral', (req, res) => {
  const { candidato_id, titulo_puesto, empresa } = req.body;
  
  if (!candidato_id || !titulo_puesto || !empresa) {
    return res.status(400).send("Los campos 'candidato_id', 'titulo_puesto' y 'empresa' son obligatorios");
  }

  db.run('INSERT INTO ExperienciaLaboral (candidato_id, titulo_puesto, empresa) VALUES (?, ?, ?)', [candidato_id, titulo_puesto, empresa], function(err) {
    if (err) {
      return res.status(500).send("Error al agregar la experiencia laboral");
    }
    res.send({ id: this.lastID });
  });
});

// Agregar Estudio
app.post('/api/educacion', (req, res) => {
  const { candidato_id, nombre_institucion, titulo_obtenido } = req.body;
  
  if (!candidato_id || !nombre_institucion || !titulo_obtenido) {
    return res.status(400).send("Los campos 'candidato_id', 'nombre_institucion' y 'titulo_obtenido' son obligatorios");
  }

  db.run('INSERT INTO Educacion (candidato_id, nombre_institucion, titulo_obtenido) VALUES (?, ?, ?)', [candidato_id, nombre_institucion, titulo_obtenido], function(err) {
    if (err) {
      return res.status(500).send("Error al agregar el estudio");
    }
    res.send({ id: this.lastID });
  });
});

// Agregar Habilidad/Certificación
app.post('/api/habilidades-certificaciones', (req, res) => {
  const { candidato_id, habilidad_certificacion } = req.body;
  
  if (!candidato_id || !habilidad_certificacion) {
    return res.status(400).send("Los campos 'candidato_id' y 'habilidad_certificacion' son obligatorios");
  }

  db.run('INSERT INTO HabilidadesCertificaciones (candidato_id, habilidad_certificacion) VALUES (?, ?)', [candidato_id, habilidad_certificacion], function(err) {
    if (err) {
      return res.status(500).send("Error al agregar la habilidad/certificación");
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
    res.send(row);
  });
});

// Configurar servidor
// Unificar las rutas y funciones para evitar conflictos

app.post('/api/candidatos', (req, res) => {
  const { nombre, apellido, email, telefono, direccion, fecha_nacimiento, ciudad_residencia, nacionalidad } = req.body;
  
  if (!nombre || !apellido || !email) {
    return res.status(400).send('Nombre, Apellido y Email son obligatorios');
  }

  const sql = 'INSERT INTO Candidato (nombre, apellido, email, telefono, direccion, fecha_nacimiento, ciudad_residencia, nacionalidad) VALUES (?, ?, ?, ?, ?, ?, ?, ?)';
  db.run(sql, [nombre, apellido, email, telefono, direccion, fecha_nacimiento, ciudad_residencia, nacionalidad], function(err) {
    if (err) {
      return res.status(500).send('Error al crear el candidato');
    }
    res.send({ id: this.lastID });
  });
});

app.get('/api/candidatos/:id', (req, res) => {
  const sql = 'SELECT * FROM Candidato WHERE id = ?';
  db.get(sql, [req.params.id], (err, row) => {
    if (err) {
      return res.status(500).send('Error al obtener el candidato');
    }
    if (!row) {
      return res.status(404).send('Candidato no encontrado');
    }
    res.send(row);
  });
});

app.post('/api/experiencia-laboral', (req, res) => {
  const { candidato_id, titulo_puesto, empresa, lugar_trabajo, fecha_inicio, fecha_fin, descripcion_responsabilidades } = req.body;
  
  if (!candidato_id || !titulo_puesto || !empresa) {
    return res.status(400).send('Candidato ID, Título del Puesto y Empresa son obligatorios');
  }

  const sql = 'INSERT INTO ExperienciaLaboral (candidato_id, titulo_puesto, empresa, lugar_trabajo, fecha_inicio, fecha_fin, descripcion_responsabilidades) VALUES (?, ?, ?, ?, ?, ?, ?)';
  db.run(sql, [candidato_id, titulo_puesto, empresa, lugar_trabajo, fecha_inicio, fecha_fin, descripcion_responsabilidades], function(err) {
    if (err) {
      return res.status(500).send('Error al crear la experiencia laboral');
    }
    res.send({ id: this.lastID });
  });
});

app.post('/api/educacion', (req, res) => {
  const { candidato_id, nombre_institucion, titulo_obtenido, anio_graduacion } = req.body;
  
  if (!candidato_id || !nombre_institucion || !titulo_obtenido || !anio_graduacion) {
    return res.status(400).send('Candidato ID, Nombre de la Institución, Título Obtenido y Año Graduación son obligatorios');
  }

  const sql = 'INSERT INTO Educacion (candidato_id, nombre_institucion, titulo_obtenido, anio_graduacion) VALUES (?, ?, ?, ?)';
  db.run(sql, [candidato_id, nombre_institucion, titulo_obtenido, anio_graduacion], function(err) {
    if (err) {
      return res.status(500).send('Error al crear el estudio');
    }
    res.send({ id: this.lastID });
  });
});

app.post('/api/habilidades-certificaciones', (req, res) => {
  const { candidato_id, habilidad_certificacion } = req.body;
  
  if (!candidato_id || !habilidad_certificacion) {
    return res.status(400).send('Candidato ID y Habilidad/Certificación son obligatorios');
  }

  const sql = 'INSERT INTO HabilidadesCertificaciones (candidato_id, habilidad_certificacion) VALUES (?, ?)';
  db.run(sql, [candidato_id, habilidad_certificacion], function(err) {
    if (err) {
      return res.status(500).send('Error al crear la habilidad/certificación');
    }
    res.send({ id: this.lastID });
  });
});

app.get('/api/generar-cv/:id', (req, res) => {
  const sql = 'SELECT * FROM Candidato WHERE id = ?';
  db.get(sql, [req.params.id], (err, row) => {
    if (err) {
      return res.status(500).send('Error al obtener el candidato');
    }
    if (!row) {
      return res.status(404).send('Candidato no encontrado');
    }

    // Aquí se debería implementar la lógica para generar el CV
    res.send(row);
  });
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Servidor escuchando en el puerto ${PORT}`);
});
