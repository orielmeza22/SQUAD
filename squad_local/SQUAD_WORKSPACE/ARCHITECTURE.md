### Especificación de Software (SPEC)

#### 1. Introducción

Este documento define el diseño, arquitectura y especificaciones técnicas para desarrollar una herramienta web que genera automáticamente un currículum vitae estático para un puesto de Help Desk Junior utilizando datos ficticios.

#### 2. Objetivo General
Desarrollar una aplicación web que permite a los usuarios ingresar datos personales, experiencia laboral, estudios y habilidades relevantes, luego generar un currículum vitae en formato PDF o Word basado en estos datos.

#### 3. Estructura del Proyecto

El proyecto consta de dos componentes principales: el frontend (página web) y el backend (servicios API). Ambos se desarrollarán utilizando Node.js con Express, y SQLite para la base de datos.

#### 4. Arquitectura Backend

##### 4.1 Servicios API
Se utilizará Express para crear endpoints RESTful que permitan al frontend interactuar con los servicios del backend:

- **Crear Candidato**: POST /api/candidatos
- **Obtener Candidato por ID**: GET /api/candidatos/{id}
- **Agregar Experiencia Laboral**: POST /api/experiencia-laboral
- **Agregar Estudio**: POST /api/educacion
- **Agregar Habilidad/Certificación**: POST /api/habilidades-certificaciones
- **Generar CV**: GET /api/generar-cv/{id}

##### 4.2 Base de Datos SQLite
La base de datos se creará con las siguientes tablas y campos clave:

1. **Candidato:**
   - id (INTEGER PRIMARY KEY AUTOINCREMENT)
   - nombre (TEXT NOT NULL)
   - apellido (TEXT NOT NULL)
   - email (TEXT UNIQUE NOT NULL)
   - telefono (TEXT)
   - direccion (TEXT)
   - fecha_nacimiento (DATE)
   - ciudad_residencia (TEXT)
   - nacionalidad (TEXT)

2. **ExperienciaLaboral:**
   - id (INTEGER PRIMARY KEY AUTOINCREMENT)
   - candidato_id (INTEGER, FOREIGN KEY REFERENCES Candidato(id))
   - titulo_puesto (TEXT NOT NULL)
   - empresa (TEXT NOT NULL)
   - lugar_trabajo (TEXT)
   - fecha_inicio (DATE)
   - fecha_fin (DATE)
   - descripcion_responsabilidades (TEXT)

3. **Educacion:**
   - id (INTEGER PRIMARY KEY AUTOINCREMENT)
   - candidato_id (INTEGER, FOREIGN KEY REFERENCES Candidato(id))
   - nombre_institucion (TEXT NOT NULL)
   - titulo_obtenido (TEXT NOT NULL)
   - anio_graduacion (INTEGER)

4. **HabilidadesCertificaciones:**
   - id (INTEGER PRIMARY KEY AUTOINCREMENT)
   - candidato_id (INTEGER, FOREIGN KEY REFERENCES Candidato(id))
   - habilidad_certificacion (TEXT NOT NULL)

##### 4.3 Validaciones
Se implementarán validaciones para asegurar que los datos ingresados son correctos y cumplen con las reglas de negocio:

- **Validación de Datos del Candidato**: Nombre, Apellido, Email obligatorios; Email válido.
- **Validación de Experiencia Laboral**: Título del Puesto y Empresa obligatorios; Fecha de Inicio no puede ser posterior a la Fecha Fin.
- **Validación de Educación**: Nombre de la Institución, Título Obtenido y Año Graduación obligatorios; Año Graduación debe ser un número entero positivo.

#### 5. Arquitectura Frontend

##### 5.1 Página Principal
La página principal se implementará como una aplicación estática simple en HTML5, que incluye un formulario para ingresar los datos del candidato:

- **Nombre**
- **Apellido**
- **Email** (único)
- **Teléfono**
- **Dirección**
- **Fecha de Nacimiento**
- **Ciudad de Residencia**
- **Nacionalidad**

##### 5.2 Experiencia Laboral
Se implementará un formulario para agregar experiencias laborales:

- **Título del Puesto**
- **Empresa**
- **Lugar de Trabajo**
- **Fecha de Inicio**
- **Fecha Fin**
- **Descripción de las Responsabilidades**

##### 5.3 Educación
Un formulario para agregar estudios realizados:

- **Nombre de la Institución**
- **Título Obtenido**
- **Año Graduación**

##### 5.4 Habilidades y Certificaciones
Un formulario para agregar habilidades y certificaciones relevantes.

##### 5.5 Generar CV
Una sección donde el usuario puede presionar un botón para generar el currículum vitae en formato PDF o Word:

- **Botón "Generar CV"**
- **Opciones de Descarga: PDF o Word**

##### 5.6 Vista del CV Generado
Se mostrará una vista previa del currículum generado, que puede ser editada antes de su descarga.

#### 6. Implementación

##### 6.1 Creación del Proyecto Backend
- Instalar Node.js y Express.
- Crear carpetas para los archivos de base de datos, modelos, rutas y controladores.
- Configurar el servidor principal con las rutas necesarias.
- Implementar la lógica para crear, obtener, agregar y generar CVs.

##### 6.2 Creación del Proyecto Frontend
- Crear un archivo HTML5 estándar sin bundle (o utilizar librerías como Vue/React/Tailwind vía CDN si el entorno lo soporta).
- Implementar las vistas necesarias para la página principal, agregar experiencia laboral, educación y habilidades/certificaciones.
- Integrar el botón "Generar CV" con la lógica backend para generar y descargar el currículum.

##### 6.3 Base de Datos SQLite
- Crear las tablas en la base de datos utilizando SQL.
- Implementar los modelos de Entity-Relationship (ER) para representar las relaciones entre las tablas.
- Implementar las validaciones necesarias en las consultas a la base de datos.

#### 7. Planificación de Previsualización

Para previsualizar el frontend localmente, se utilizará una estructura estática HTML5 sin bundle. Si se requiere un entorno más avanzado (como Node.js), se implementará un servidor simple que haga uso del archivo index.html para cargar las dependencias necesarias.

#### 8. Conclusiones

Este documento proporciona una visión clara y detallada de la arquitectura, especificaciones y planificación para desarrollar la aplicación mencionada. Se aseguró de incluir todos los componentes requeridos y se mantuvo en concordancia con las restricciones del sistema anfitrión.

### Documentación Adicional

Para más detalles sobre el desarrollo, configuración y pruebas, se recomienda consultar documentaciones adicionales sobre Node.js, Express, SQLite y herramientas de desarrollo web.