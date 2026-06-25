-- Creación de las tablas candidato, experiencia-laboral, educacion y habilidades-certificaciones

CREATE TABLE IF NOT EXISTS Candidato (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL CHECK (email LIKE '%@%'),
    telefono TEXT,
    direccion TEXT,
    fecha_nacimiento DATE,
    ciudad_residencia TEXT,
    nacionalidad TEXT
);

CREATE TABLE IF NOT EXISTS ExperienciaLaboral (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidato_id INTEGER,
    FOREIGN KEY(candidato_id) REFERENCES Candidato(id),
    titulo_puesto TEXT NOT NULL,
    empresa TEXT NOT NULL,
    lugar_trabajo TEXT,
    fecha_inicio DATE,
    fecha_fin DATE,
    descripcion_responsabilidades TEXT
);

CREATE TABLE IF NOT EXISTS Educacion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidato_id INTEGER,
    FOREIGN KEY(candidato_id) REFERENCES Candidato(id),
    nombre_institucion TEXT NOT NULL,
    titulo_obtenido TEXT NOT NULL,
    anio_graduacion INTEGER CHECK (anio_graduacion > 0)
);

CREATE TABLE IF NOT EXISTS HabilidadesCertificaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidato_id INTEGER,
    FOREIGN KEY(candidato_id) REFERENCES Candidato(id),
    habilidad_certificacion TEXT NOT NULL
);
