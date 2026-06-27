-- Esquema de la base de datos para almacenar los turnos

CREATE DATABASE IF NOT EXISTS gestion_turnos;

USE gestion_turnos;

CREATE TABLE IF NOT EXISTS turnos (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO turnos (nombre, descripcion) VALUES 
('Turno 1', 'Descripción del turno 1'),
('Turno 2', 'Descripción del turno 2');

-- Reporte de seguridad

# Esquema de la base de datos para almacenar los turnos

CREATE DATABASE IF NOT EXISTS gestion_turnos;

USE gestion_turnos;

CREATE TABLE IF NOT EXISTS turnos (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO turnos (nombre, descripcion) VALUES 
('Turno 1', 'Descripción del turno 1'),
('Turno 2', 'Descripción del turno 2');

-- Reporte de seguridad

# Vulnerabilidades comunes en el esquema SQL:

## Vulnerabilidad 1: Falta de restricciones de integridad
- **Explicación**: No se han definido las claves foráneas y otras restricciones que aseguren la integridad del modelo de datos.
- **Recomendación**: Asegúrate de incluir claves foráneas y otros mecanismos para garantizar la integridad referencial.

## Vulnerabilidad 2: Falta de cifrado
- **Explicación**: No se han utilizado encriptaciones o algoritmos de seguridad para proteger los datos.
- **Recomendación**: Considera utilizar encriptación para proteger los datos sensibles y considerar el uso de contraseñas fuertes.

## Vulnerabilidad 3: Falta de control de acceso
- **Explicación**: No se han definido roles o permisos específicos para usuarios.
- **Recomendación**: Implementa un sistema de control de acceso (como roles y permisos) para proteger los datos contra accesos no autorizados.

## Vulnerabilidad 4: Falta de validación
- **Explicación**: No se han definido restricciones de tipo o longitud en las columnas.
- **Recomendación**: Asegúrate de incluir restricciones de tipo y longitud para garantizar que los datos ingresados sean válidos.

## Vulnerabilidad 5: Falta de respaldo
- **Explicación**: No se ha definido un plan de respaldo o recuperación en caso de pérdida de datos.
- **Recomendación**: Implementa un plan de respaldo regular para garantizar la recuperación de los datos en caso de pérdida.

## Vulnerabilidad 6: Falta de optimización
- **Explicación**: No se han definido índices ni otras estrategias de optimización que mejoren el rendimiento.
- **Recomendación**: Considera crear índices para mejorar la velocidad de consulta y considerar otros métodos de optimización según sea necesario.

## Vulnerabilidad 7: Falta de seguridad en consultas
- **Explicación**: No se han utilizado mecanismos de protección contra inyecciones SQL.
- **Recomendación**: Asegúrate de utilizar consultas preparadas o procedimientos almacenados para proteger contra inyecciones SQL.

## Vulnerabilidad 8: Falta de documentación
- **Explicación**: No se ha incluido documentación sobre el esquema y su uso.
- **Recomendación**: Documenta claramente el esquema, las columnas, los tipos de datos y cualquier otra información relevante para facilitar la comprensión y el mantenimiento del sistema.

Este reporte identifica vulnerabilidades comunes en el esquema SQL proporcionado. Para mitigar estas vulnerabilidades, se recomienda implementar las recomendaciones mencionadas.