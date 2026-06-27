-- Esquema de la tabla 'turnos' en SQLite y PostgreSQL

CREATE TABLE IF NOT EXISTS turnos (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    fecha DATE NOT NULL,
    hora TIME NOT NULL
);

-- Insertar datos de prueba (funciona tanto en SQLite como en PostgreSQL)

INSERT INTO turnos (nombre, fecha, hora) VALUES 
('Turno 1', '2023-10-05', '14:00'),
('Turno 2', '2023-10-06', '15:30'),
('Turno 3', '2023-10-07', '16:00');
