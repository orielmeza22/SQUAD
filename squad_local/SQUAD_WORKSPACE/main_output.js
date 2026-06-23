// db.js

const sqlite3 = require('sqlite3').verbose();

// Crear una conexión a la base de datos SQLite
const db = new sqlite3.Database('./db.sqlite3', (err) => {
    if (err) {
        return console.error(err.message);
    }
});

module.exports = db;
