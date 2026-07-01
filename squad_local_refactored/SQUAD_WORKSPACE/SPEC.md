### Especificación de Software (SPEC)
**STACK:** FASTAPI_HTMX

#### 1. **Descripción del Proyecto**
El objetivo de esta aplicación es proporcionar una interfaz sencilla para gestionar turnos médicos utilizando FastAPI como backend y HTMX para la interactividad en el frontend, todo ello integrado con SQLite como base de datos.

#### 2. **Arquitectura del Sistema**
##### 2.1 **Backend (FastAPI)**
- **Archivo:** main_output.py
  - **Responsabilidades:**
    - Definir y gestionar las rutas HTTP.
    - Interactuar con la base de datos SQLite para realizar operaciones CRUD.
    - Servir archivos estáticos del frontend.

##### 2.2 **Frontend (HTML/CSS)**
- **Archivos:**
  - `templates/index.html`: Plantilla principal que utiliza HTMX para cargar y actualizar partes dinámicas de la interfaz.
  - `static/css/style.css`: Archivo CSS para estilizar la aplicación.

#### 3. **Base de Datos (SQLite)**
- **Archivo:** medical_turns.sqlite
  - **Tablas:**
    - `patients`
      - `id` (INTEGER, PRIMARY KEY)
      - `name` (TEXT)
      - `created_at` (DATETIME)
    - `turns`
      - `id` (INTEGER, PRIMARY KEY)
      - `patient_id` (INTEGER, FOREIGN KEY REFERENCES patients(id))
      - `doctor_name` (TEXT)
      - `appointment_time` (DATETIME)

#### 4. **Endpoints y Rutas**
##### 4.1 **Ruta: /patients**
- **Método:** GET
  - **Descripción:** Retorna una lista de todos los pacientes registrados.
  - **Respuesta:**
    ```json
    [
      {
        "id": 1,
        "name": "Paciente A",
        "created_at": "2023-10-01T12:00:00Z"
      },
      {
        "id": 2,
        "name": "Paciente B",
        "created_at": "2023-10-02T12:00:00Z"
      }
    ]
    ```
##### 4.2 **Ruta: /patients**
- **Método:** POST
  - **Descripción:** Crea un nuevo paciente.
  - **Entrada:**
    ```json
    {
      "name": "Paciente Nuevo"
    }
    ```
  - **Respuesta:**
    ```json
    {
      "id": 3,
      "name": "Paciente Nuevo",
      "created_at": "2023-10-03T12:00:00Z"
    }
    ```
##### 4.3 **Ruta: /patients/{patient_id}/turns**
- **Método:** GET
  - **Descripción:** Retorna una lista de turnos registrados para un paciente específico.
  - **Respuesta:**
    ```json
    [
      {
        "id": 1,
        "doctor_name": "Doctor A",
        "appointment_time": "2023-10-01T14:00:00Z"
      },
      {
        "id": 2,
        "doctor_name": "Doctor B",
        "appointment_time": "2023-10-01T15:00:00Z"
      }
    ]
    ```
##### 4.4 **Ruta: /patients/{patient_id}/turns**
- **Método:** POST
  - **Descripción:** Crea un nuevo turno para un paciente específico.
  - **Entrada:**
    ```json
    {
      "doctor_name": "Doctor C",
      "appointment_time": "2023-10-01T16:00:00Z"
    }
    ```
  - **Respuesta:**
    ```json
    {
      "id": 3,
      "doctor_name": "Doctor C",
      "appointment_time": "2023-10-01T16:00:00Z"
    }
    ```

#### 5. **Estructura de Archivos**
```
project_root/
├── main_output.py
├── templates/
│   └── index.html
├── static/
│   ├── css/
│   │   └── style.css
└── medical_turns.sqlite
```

#### 6. **Consideraciones Finales**
- **Interactividad:** Utilizar HTMX para cargar y actualizar partes dinámicas de la interfaz sin recargar toda la página.
- **Seguridad:** Implementar validaciones y autenticación si se requiere una versión más avanzada de la aplicación.
- **Escalabilidad:** Mantener el código autocontenido en `main_output.py` para facilitar futuras actualizaciones y mantenimiento.

Este plan técnico proporciona una base sólida para desarrollar la aplicación solicitada, asegurando que todas las partes del sistema estén bien definidas y separadas según las reglas establecidas.