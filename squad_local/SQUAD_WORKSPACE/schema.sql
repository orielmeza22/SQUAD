-- Creando la base de datos si no existe
CREATE DATABASE IF NOT EXISTS server_architectures;

-- Usando la base de datos creada o existente
USE server_architectures;

-- Creando tabla de usuarios (usando tipos estándar SQL)
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertando datos de prueba en la tabla usuarios
INSERT INTO users (id, username, password_hash, email)
VALUES 
    (1, 'admin', '$2b$12$eXQZ8z5vYKu7j3R6i09Oe.UsfJ4qWnBxgGkPmLcUyVwDlFtHrMh.', 'admin@example.com'),
    (2, 'user1', '$2b$12$eXQZ8z5vYKu7j3R6i09Oe.UsfJ4qWnBxgGkPmLcUyVwDlFtHrMh.', 'user1@example.com'),
    (3, 'user2', '$2b$12$eXQZ8z5vYKu7j3R6i09Oe.UsfJ4qWnBxgGkPmLcUyVwDlFtHrMh.', 'user2@example.com');

-- Creando tabla de servidores
CREATE TABLE IF NOT EXISTS servers (
    id INT PRIMARY KEY,
    server_name VARCHAR(100) UNIQUE NOT NULL,
    ip_address VARCHAR(50),
    port INT,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertando datos de prueba en la tabla servidores
INSERT INTO servers (id, server_name, ip_address, port, status)
VALUES 
    (1, 'Server 1', '192.168.1.1', 8080, 'ONLINE'),
    (2, 'Server 2', '192.168.1.2', 8081, 'OFFLINE'),
    (3, 'Server 3', '192.168.1.3', 8082, 'ONLINE');

-- Crear tabla products si no existe
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    price REAL NOT NULL
);

-- Insertando datos de prueba en la tabla productos
INSERT INTO products (title, description, price)
VALUES 
    ('Product 1', 'Description of Product 1', 9.99),
    ('Product 2', 'Description of Product 2', 19.99),
    ('Product 3', 'Description of Product 3', 29.99);

-- Creando tabla de arquitecturas
CREATE TABLE IF NOT EXISTS architectures (
    id INT PRIMARY KEY,
    architecture_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertando datos de prueba en la tabla arquitecturas
INSERT INTO architectures (id, architecture_name, description)
VALUES 
    (1, 'Architecture A', 'This is the first architecture'),
    (2, 'Architecture B', 'This is the second architecture'),
    (3, 'Architecture C', 'This is the third architecture');