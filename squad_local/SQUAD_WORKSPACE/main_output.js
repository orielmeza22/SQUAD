// main_output.js

const express = require('express');
const bodyParser = require('body-parser');
const { open } = require('sqlite');

const app = express();
app.use(bodyParser.json());

// Conectar a SQLite
open({
  filename: './database.sqlite',
  driver: require('sqlite3').verbose()
}).then(db => {
  console.log("Conectado a la base de datos");
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

// Configurar servidor
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Servidor escuchando en el puerto ${PORT}`);
});
