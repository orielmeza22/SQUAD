-- Esquema SQL para el sistema de gestión del sanatorio

-- Crear tabla Pacientes
CREATE TABLE IF NOT EXISTS Pacientes (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    fecha_nacimiento DATE NOT NULL,
    genero TEXT NOT NULL,
    telefono TEXT UNIQUE
);

-- Insertar datos de prueba para la tabla Pacientes
INSERT INTO Pacientes (nombre, apellido, fecha_nacimiento, genero, telefono) VALUES
('Juan', 'Perez', '1980-05-15', 'Masculino', '123456789'),
('Maria', 'Lopez', '1975-08-20', 'Femenino', '987654321'),
('Carlos', 'Gomez', '1990-03-10', 'Masculino', '555555555');

-- Crear tabla Consultas
CREATE TABLE IF NOT EXISTS Consultas (
    id INTEGER PRIMARY KEY,
    paciente_id INTEGER REFERENCES Pacientes(id),
    fecha_consulta DATE NOT NULL,
    doctor TEXT NOT NULL,
    diagnostico TEXT
);

-- Insertar datos de prueba para la tabla Consultas
INSERT INTO Consultas (paciente_id, fecha_consulta, doctor, diagnostico) VALUES
(1, '2023-10-01', 'Dr. Smith', 'Resfriado común'),
(2, '2023-10-05', 'Dra. Johnson', 'Gripe estacional');

-- Crear tabla Medicamentos
CREATE TABLE IF NOT EXISTS Medicamentos (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    dosis TEXT NOT NULL,
    frecuencia TEXT NOT NULL
);

-- Insertar datos de prueba para la tabla Medicamentos
INSERT INTO Medicamentos (nombre, dosis, frecuencia) VALUES
('Paracetamol', '500mg', 'Cada 6 horas'),
('Ibuprofeno', '400mg', 'Cada 8 horas');

-- Crear tabla Recetas
CREATE TABLE IF NOT EXISTS Recetas (
    id INTEGER PRIMARY KEY,
    consulta_id INTEGER REFERENCES Consultas(id),
    medicamento_id INTEGER REFERENCES Medicamentos(id),
    dosis TEXT NOT NULL,
    frecuencia TEXT NOT NULL
);

-- Insertar datos de prueba para la tabla Recetas
INSERT INTO Recetas (consulta_id, medicamento_id, dosis, frecuencia) VALUES
(1, 1, '500mg', 'Cada 6 horas'),
(2, 2, '400mg', 'Cada 8 horas');