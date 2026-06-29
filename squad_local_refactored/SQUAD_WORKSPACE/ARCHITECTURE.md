### Especificación de Software (SPEC)

**STACK:** FASTAPI_HTMX

---

#### **1. Descripción del Proyecto**

El sistema de gestión para el sanatorio se desarrollará utilizando el stack tecnológico **FASTAPI_HTMX**, que incluye Python, FastAPI, HTMX y SQLite. Este stack es ideal para crear sistemas de gestión interactivos y eficientes.

---

#### **2. Estructura del Proyecto**

El proyecto estará estructurado en un único archivo `main_output.py`, que contendrá toda la lógica del backend (modelos, rutas, base de datos y servidor). No se utilizarán subcarpetas ni archivos secundarios para mantener la simplicidad y cohesión del código.

---

#### **3. Base de Datos**

La base de datos utilizada será SQLite, gestionada a través de SQLAlchemy en FastAPI. Los archivos actuales del proyecto son:

- `squad_checkpoints.sqlite`: La base de datos principal.
- `squad_checkpoints.sqlite-shm` y `squad_checkpoints.sqlite-wal`: Archivos auxiliares de SQLite.

**Tablas:**

1. **Pacientes**
   - `id` (INTEGER, PRIMARY KEY)
   - `nombre` (TEXT, NOT NULL)
   - `apellido` (TEXT, NOT NULL)
   - `fecha_nacimiento` (DATE, NOT NULL)
   - `genero` (TEXT, NOT NULL)
   - `telefono` (TEXT, UNIQUE)

2. **Consultas**
   - `id` (INTEGER, PRIMARY KEY)
   - `paciente_id` (INTEGER, FOREIGN KEY REFERENCES Pacientes(id))
   - `fecha_consulta` (DATE, NOT NULL)
   - `doctor` (TEXT, NOT NULL)
   - `diagnostico` (TEXT)

3. **Medicamentos**
   - `id` (INTEGER, PRIMARY KEY)
   - `nombre` (TEXT, NOT NULL)
   - `dosis` (TEXT, NOT NULL)
   - `frecuencia` (TEXT, NOT NULL)

4. **Recetas**
   - `id` (INTEGER, PRIMARY KEY)
   - `consulta_id` (INTEGER, FOREIGN KEY REFERENCES Consultas(id))
   - `medicamento_id` (INTEGER, FOREIGN KEY REFERENCES Medicamentos(id))
   - `dosis` (TEXT, NOT NULL)
   - `frecuencia` (TEXT, NOT NULL)

---

#### **4. Endpoints y Rutas**

**Pacientes:**

- **GET /pacientes**: Listar todos los pacientes.
  - **Inputs:** N/A
  - **Outputs:** Lista de objetos JSON con la información de cada paciente.

- **POST /pacientes**: Crear un nuevo paciente.
  - **Inputs:** Objeto JSON con campos `nombre`, `apellido`, `fecha_nacimiento`, `genero` y `telefono`.
  - **Outputs:** ID del paciente creado.

- **GET /pacientes/{id}**: Obtener información de un paciente específico.
  - **Inputs:** ID del paciente.
  - **Outputs:** Objeto JSON con la información del paciente.

- **PUT /pacientes/{id}**: Actualizar información de un paciente.
  - **Inputs:** ID del paciente y objeto JSON con campos a actualizar (`nombre`, `apellido`, `fecha_nacimiento`, `genero` o `telefono`).
  - **Outputs:** Mensaje de éxito.

- **DELETE /pacientes/{id}**: Eliminar un paciente.
  - **Inputs:** ID del paciente.
  - **Outputs:** Mensaje de éxito.

**Consultas:**

- **GET /consultas**: Listar todas las consultas.
  - **Inputs:** N/A
  - **Outputs:** Lista de objetos JSON con la información de cada consulta.

- **POST /consultas**: Crear una nueva consulta.
  - **Inputs:** Objeto JSON con campos `paciente_id`, `fecha_consulta`, `doctor` y `diagnostico`.
  - **Outputs:** ID de la consulta creada.

- **GET /consultas/{id}**: Obtener información de una consulta específica.
  - **Inputs:** ID de la consulta.
  - **Outputs:** Objeto JSON con la información de la consulta.

- **PUT /consultas/{id}**: Actualizar información de una consulta.
  - **Inputs:** ID de la consulta y objeto JSON con campos a actualizar (`paciente_id`, `fecha_consulta`, `doctor` o `diagnostico`).
  - **Outputs:** Mensaje de éxito.

- **DELETE /consultas/{id}**: Eliminar una consulta.
  - **Inputs:** ID de la consulta.
  - **Outputs:** Mensaje de éxito.

**Medicamentos:**

- **GET /medicamentos**: Listar todos los medicamentos.
  - **Inputs:** N/A
  - **Outputs:** Lista de objetos JSON con la información de cada medicamento.

- **POST /medicamentos**: Crear un nuevo medicamento.
  - **Inputs:** Objeto JSON con campos `nombre`, `dosis` y `frecuencia`.
  - **Outputs:** ID del medicamento creado.

- **GET /medicamentos/{id}**: Obtener información de un medicamento específico.
  - **Inputs:** ID del medicamento.
  - **Outputs:** Objeto JSON con la información del medicamento.

- **PUT /medicamentos/{id}**: Actualizar información de un medicamento.
  - **Inputs:** ID del medicamento y objeto JSON con campos a actualizar (`nombre`, `dosis` o `frecuencia`).
  - **Outputs:** Mensaje de éxito.

- **DELETE /medicamentos/{id}**: Eliminar un medicamento.
  - **Inputs:** ID del medicamento.
  - **Outputs:** Mensaje de éxito.

**Recetas:**

- **GET /recetas**: Listar todas las recetas.
  - **Inputs:** N/A
  - **Outputs:** Lista de objetos JSON con la información de cada receta.

- **POST /recetas**: Crear una nueva receta.
  - **Inputs:** Objeto JSON con campos `consulta_id`, `medicamento_id`, `dosis` y `frecuencia`.
  - **Outputs:** ID de la receta creada.

- **GET /recetas/{id}**: Obtener información de una receta específica.
  - **Inputs:** ID de la receta.
  - **Outputs:** Objeto JSON con la información de la receta.

- **PUT /recetas/{id}**: Actualizar información de una receta.
  - **Inputs:** ID de la receta y objeto JSON con campos a actualizar (`consulta_id`, `medicamento_id`, `dosis` o `frecuencia`).
  - **Outputs:** Mensaje de éxito.

- **DELETE /recetas/{id}**: Eliminar una receta.
  - **Inputs:** ID de la receta.
  - **Outputs:** Mensaje de éxito.

---

#### **5. Frontend**

El frontend será desarrollado utilizando HTML, CSS y HTMX para añadir interactividad sin necesidad de JavaScript del lado del cliente. Los archivos estarán ubicados en una carpeta `templates` dentro del mismo directorio que `main_output.py`.

**Archivos Frontend:**

- **index.html**: Página principal con enlaces a las diferentes secciones (Pacientes, Consultas, Medicamentos, Recetas).
- **pacientes.html**: Formulario para listar y gestionar pacientes.
- **consultas.html**: Formulario para listar y gestionar consultas.
- **medicamentos.html**: Formulario para listar y gestionar medicamentos.
- **recetas.html**: Formulario para listar y gestionar recetas.

**Interactividad con HTMX:**

- Utilizar `hx-get` y `hx-post` para cargar dinámicamente contenido sin recargar la página.
- Ejemplo de uso en `pacientes.html`:
  ```html
  <div hx-get="/pacientes" hx-target="#paciente-list"></div>
  ```

---

#### **6. Punto de Entrada**

El punto de entrada del servidor será el archivo `main_output.py`, que se ejecutará utilizando uvicorn.

**Comando para iniciar el servidor:**
```bash
uvicorn main_output:app --reload
```

---

#### **7. Consideraciones Finales**

- **Seguridad:** Implementar autenticación y autorización para acceder a las funcionalidades del sistema.
- **Escalabilidad:** Mantener la estructura simple pero modular para facilitar futuras actualizaciones o adiciones de nuevas funcionalidades.
- **Documentación:** Documentar cada endpoint y su uso para facilitar el mantenimiento y la colaboración.

---

Este SPEC proporciona una base sólida para desarrollar un sistema de gestión eficiente y fácil de mantener utilizando el stack FASTAPI_HTMX.