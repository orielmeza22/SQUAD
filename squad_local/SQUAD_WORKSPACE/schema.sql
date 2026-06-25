-- Archivo: database.sql

-- Creación de la base de datos si no existe
CREATE DATABASE IF NOT EXISTS proyecto_cv_helpdesk_junior;

-- Seleccionar la base de datos recién creada
USE proyecto_cv_helpdesk_junior;

-- Creación de la tabla Usuarios
CREATE TABLE IF NOT EXISTS Usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    apellido VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    telefono VARCHAR(15),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Creación de la tabla ExperienciaLaboral
CREATE TABLE IF NOT EXISTS ExperienciaLaboral (
    id_experiencia INT AUTO_INCREMENT PRIMARY KEY,
    puesto VARCHAR(255) NOT NULL,
    empresa VARCHAR(255) NOT NULL,
    fecha_inicio DATE,
    fecha_fin DATE,
    responsabilidades TEXT,
    logros TEXT,
    id_usuario INT,
    FOREIGN KEY (id_usuario) REFERENCES Usuarios(id_usuario)
);

-- Creación de la tabla HabilidadesTecnicas
CREATE TABLE IF NOT EXISTS HabilidadesTecnicas (
    id_habilidad INT AUTO_INCREMENT PRIMARY KEY,
    habilidad VARCHAR(255) NOT NULL,
    nivel VARCHAR(10),
    id_usuario INT,
    FOREIGN KEY (id_usuario) REFERENCES Usuarios(id_usuario)
);

-- Creación de la tabla Educacion
CREATE TABLE IF NOT EXISTS Educacion (
    id_educacion INT AUTO_INCREMENT PRIMARY KEY,
    institucion VARCHAR(255) NOT NULL,
    titulo_obtenido VARCHAR(255),
    anio_graduacion YEAR,
    id_usuario INT,
    FOREIGN KEY (id_usuario) REFERENCES Usuarios(id_usuario)
);

-- Inserción de datos de prueba
INSERT INTO Usuarios (nombre, apellido, email, telefono)
VALUES ('Juan', 'Perez', 'juan.perez@example.com', '1234567890'),
       ('Maria', 'Gomez', 'maria.gomez