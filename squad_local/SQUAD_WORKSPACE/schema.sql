-- Esquema de la base de datos para gestionar arquitecturas de servidor

CREATE TABLE IF NOT EXISTS server_architectures (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    status BOOLEAN DEFAULT FALSE
);

INSERT INTO server_architectures (name, description, status) VALUES 
('Server1', 'A simple server architecture for testing', TRUE),
('Server2', 'Another server architecture with more features', FALSE),
('Server3', 'A third server architecture', TRUE);