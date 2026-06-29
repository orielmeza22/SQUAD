STACK: FASTAPI_HTMX

### Especificación de Software (SPEC)

#### 1. Introducción:
Este documento define el diseño, arquitectura y especificaciones técnicas para un sistema de gestión completo para un sanatorio utilizando el stack FASTAPI_HTMX.

#### 2. Objetivo del Proyecto:
El objetivo es desarrollar una aplicación web completa que permita gestionar los aspectos administrativos y operativos de un sanatorio, incluyendo la gestión de pacientes, personal médico, recursos médicos, y otros datos relevantes.

#### 3. Arquitectura del Sistema:

##### Backend:
- **Lenguaje**: Python
- **Framework**: FastAPI
- **Interacción Cliente-Servidor**: HTMX (HyperText Markup Language eXtended)
- **Base de Datos**: SQLite

##### Frontend:
- **HTML/CSS**: Servido por FastAPI
- **JavaScript**: No se requiere, ya que todo el frontend está servido por FastAPI.

#### 4. Estructura del Proyecto:

1. **Archivos y carpetas**:
   - `main_output.py`: Punto de entrada para el backend.
   - `static/`: Carpeta para archivos estáticos (CSS, JS).
   - `templates/`: Carpeta para plantillas HTML.

2. **Estructura del Backend**:
   ```plaintext
   .
   ├── main_output.py
   ├── static/
   │   └── styles.css
   │   └── scripts.js
   ├── templates/
   │   └── index.html
   ```

#### 5. Estructura de las Tablas en SQLite:

1. **Tabla `pacientes`**:
    - `id`: Integer, Primary Key, Autoincremental.
    - `nombre`: Text.
    - `apellido`: Text.
    - `fecha_nacimiento`: Date.
    - `diagnostico`: Text.

2. **Tabla `personal_medico`**:
    - `id`: Integer, Primary Key, Autoincremental.
    - `nombre`: Text.
    - `cargo`: Text.
    - `especialidad`: Text.

3. **Tabla `recursos_medicos`**:
    - `id`: Integer, Primary Key, Autoincremental.
    - `tipo`: Text.
    - `estado`: Text.
    - `ubicacion`: Text.

4. **Tabla `historias_clinicas`**:
    - `id`: Integer, Primary Key, Autoincremental.
    - `paciente_id`: Integer, Foreign Key to pacientes.id.
    - `fecha_visita`: Date.
    - `diagnostico`: Text.
    - `tratamiento`: Text.

#### 6. Endpoints y Rutas:

1. **Endpoint para Listar Pacientes**:
   ```plaintext
   GET /pacientes
   ```
   **Inputs/Outputs:**
   - **Inputs**: None
   - **Outputs**: Lista de pacientes en formato JSON, ejemplo:
     ```json
     [
         {"id": 1, "nombre": "Juan", "apellido": "Perez", "fecha_nacimiento": "2000-01-01", "diagnostico": "Covid"},
         ...
     ]
     ```

2. **Endpoint para Crear Paciente**:
   ```plaintext
   POST /pacientes
   ```
   **Inputs/Outputs:**
   - **Inputs**: JSON con los datos del paciente, ejemplo:
     ```json
     {
         "nombre": "Juan",
         "apellido": "Perez",
         "fecha_nacimiento": "2000-01-01",
         "diagnostico": "Covid"
     }
     ```
   - **Outputs**: Código de estado HTTP 201 y el ID del paciente creado.

3. **Endpoint para Listar Personal Médico**:
   ```plaintext
   GET /personal_medico
   ```
   **Inputs/Outputs:**
   - **Inputs**: None
   - **Outputs**: Lista de personal médico en formato JSON, ejemplo:
     ```json
     [
         {"id": 1, "nombre": "Juan", "cargo": "Doctor", "especialidad": "Cardiología"},
         ...
     ]
     ```

4. **Endpoint para Crear Personal Médico**:
   ```plaintext
   POST /personal_medico
   ```
   **Inputs/Outputs:**
   - **Inputs**: JSON con los datos del personal médico, ejemplo:
     ```json
     {
         "nombre": "Juan",
         "cargo": "Doctor",
         "especialidad": "Cardiología"
     }
     ```
   - **Outputs**: Código de estado HTTP 201 y el ID del personal médico creado.

5. **Endpoint para Listar Recursos Médicos**:
   ```plaintext
   GET /recursos_medicos
   ```
   **Inputs/Outputs:**
   - **Inputs**: None
   - **Outputs**: Lista de recursos médicos en formato JSON, ejemplo:
     ```json
     [
         {"id": 1, "tipo": "Máquina", "estado": "Activo", "ubicacion": "Salón A"},
         ...
     ]
     ```

6. **Endpoint para Crear Recursos Médicos**:
   ```plaintext
   POST /recursos_medicos
   ```
   **Inputs/Outputs:**
   - **Inputs**: JSON con los datos del recurso médico, ejemplo:
     ```json
     {
         "tipo": "Máquina",
         "estado": "Activo",
         "ubicacion": "Salón A"
     }
     ```
   - **Outputs**: Código de estado HTTP 201 y el ID del recurso médico creado.

7. **Endpoint para Listar Historias Clínicas**:
   ```plaintext
   GET /historias_clinicas
   ```
   **Inputs/Outputs:**
   - **Inputs**: None
   - **Outputs**: Lista de historias clínicas en formato JSON, ejemplo:
     ```json
     [
         {"id": 1, "paciente_id": 1, "fecha_visita": "2023-04-05", "diagnostico": "Covid", "tratamiento": "Hospitalización"},
         ...
     ]
     ```

8. **Endpoint para Crear Historia Clínica**:
   ```plaintext
   POST /historias_clinicas
   ```
   **Inputs/Outputs:**
   - **Inputs**: JSON con los datos de la historia clínica, ejemplo:
     ```json
     {
         "paciente_id": 1,
         "fecha_visita": "2023-04-05",
         "diagnostico": "Covid",
         "tratamiento": "Hospitalización"
     }
     ```
   - **Outputs**: Código de estado HTTP 201 y el ID de la historia clínica creada.

#### 7. Documentación del Backend:

```python
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import sqlite3

app = FastAPI()

# Conectar a SQLite
conn = sqlite3.connect('squad_checkpoints.sqlite')
cursor = conn.cursor()

class Paciente(BaseModel):
    nombre: str
    apellido: str
    fecha_nacimiento: str
    diagnostico: str

@app.get("/pacientes", response_model=list[Paciente])
def listar_pacientes():
    cursor.execute("SELECT * FROM pacientes")
    rows = cursor.fetchall()
    return [Paciente(**row) for row in rows]

class PersonalMedico(BaseModel):
    nombre: str
    cargo: str
    especialidad: str

@app.post("/personal_medico", response_model=PersonalMedico)
def crear_personal_medico(personal_medico: PersonalMedico):
    cursor.execute("INSERT INTO personal_medico (nombre, cargo, especialidad) VALUES (?, ?, ?)", 
                   (personal_medico.nombre, personal_medico.cargo, personal_medico.especialidad))
    conn.commit()
    return personal_medico

class RecursoMedico(BaseModel):
    tipo: str
    estado: str
    ubicacion: str

@app.get("/recursos_medicos", response_model=list[RecursoMedico])
def listar_recursos_medicos():
    cursor.execute("SELECT * FROM recursos_medicos")
    rows = cursor.fetchall()
    return [RecursoMedico(**row) for row in rows]

@app.post("/recursos_medicos", response_model=RecursoMedico)
def crear_recurso_medico(recurso_medico: RecursoMedico):
    cursor.execute("INSERT INTO recursos_medicos (tipo, estado, ubicacion) VALUES (?, ?, ?)", 
                   (recurso_medico.tipo, recurso_medico.estado, recurso_medico.ubicacion))
    conn.commit()
    return recurso_medico

class HistoriaClinica(BaseModel):
    paciente_id: int
    fecha_visita: str
    diagnostico: str
    tratamiento: str

@app.get("/historias_clinicas", response_model=list[HistoriaClinica])
def listar_historias_clinicas():
    cursor.execute("SELECT * FROM historias_clinicas")
    rows = cursor.fetchall()
    return [HistoriaClinica(**row) for row in rows]

@app.post("/historias_clinicas", response_model=HistoriaClinica)
def crear_historia_clinica(historia_clinica: HistoriaClinica):
    cursor.execute("INSERT INTO historias_clinicas (paciente_id, fecha_visita, diagnostico, tratamiento) VALUES (?, ?, ?, ?)", 
                   (historia_clinica.paciente_id, historia_clinica.fecha_visita, historia_clinica.diagnostico, historia_clinica.tratamiento))
    conn.commit()
    return historia_clinica

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main_output:app", host="0.0.0.0", port=8000)
```

#### 8. Documentación del Frontend:

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Sanatorio</title>
    <link rel="stylesheet" href="/static/styles.css">
</head>
<body>
    <h1>Gestión de Sanatorio</h1>
    <div id="app"></div>

    <!-- JavaScript para HTMX -->
    <script src="https://unpkg.com/htmx.org@1.5.0"></script>
    <script src="/static/scripts.js"></script>
</body>
</html>
```

#### 9. Documentación de la Interfaz del Usuario (UI):

- **Página Inicial**: Listado general de pacientes, personal médico y recursos médicos.
- **Página de Detalle Paciente**: Formulario para editar o eliminar un paciente.
- **Página de Crear Paciente**: Formulario para crear un nuevo paciente.
- **Página de Detalle Personal Médico**: Formulario para editar o eliminar un personal médico.
- **Página de Crear Personal Médico**: Formulario para crear un nuevo personal médico.
- **Página de Detalle Recurso Médico**: Formulario para editar o eliminar un recurso médico.
- **Página de Crear Recurso Médico**: Formulario para crear un nuevo recurso médico.
- **Página de Detalle Historia Clínica**: Formulario para editar o eliminar una historia clínica.
- **Página de Crear Historia Clínica**: Formulario para crear una nueva historia clínica.

#### 10. Documentación de Pruebas:

- **Pruebas unitarias**:
  - `test_pacientes.py`
  - `test_personal_medico.py`
  - `test_recursos_medicos.py`
  - `test_historias_clinicas.py`

Este documento proporciona una estructura clara y detallada para el desarrollo del sistema de gestión completo para un sanatorio utilizando el stack FASTAPI_HTMX.