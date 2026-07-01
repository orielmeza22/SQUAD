### Especificación de Software (SPEC)
**STACK:** FASTAPI_HTMX

#### 1. **Descripción del Proyecto**
El objetivo de esta aplicación es proporcionar una interfaz sencilla para anotar los puntos de juegos de mesa. La aplicación utilizará FastAPI como backend y HTMX para la interactividad en el frontend, todo ello integrado con SQLite como base de datos.

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
- **Archivo:** squad_checkpoints.sqlite
  - **Tablas:**
    - `games`
      - `id` (INTEGER, PRIMARY KEY)
      - `name` (TEXT)
      - `created_at` (DATETIME)
    - `checkpoints`
      - `id` (INTEGER, PRIMARY KEY)
      - `game_id` (INTEGER, FOREIGN KEY REFERENCES games(id))
      - `player_name` (TEXT)
      - `score` (INTEGER)
      - `timestamp` (DATETIME)

#### 4. **Endpoints y Rutas**
##### 4.1 **Ruta: /games**
- **Método:** GET
  - **Descripción:** Retorna una lista de todos los juegos registrados.
  - **Respuesta:**
    ```json
    [
      {
        "id": 1,
        "name": "Juego 1",
        "created_at": "2023-10-01T12:00:00Z"
      },
      {
        "id": 2,
        "name": "Juego 2",
        "created_at": "2023-10-02T12:00:00Z"
      }
    ]
    ```

##### 4.2 **Ruta: /games**
- **Método:** POST
  - **Descripción:** Crea un nuevo juego.
  - **Entrada:**
    ```json
    {
      "name": "Juego Nuevo"
    }
    ```
  - **Respuesta:**
    ```json
    {
      "id": 3,
      "name": "Juego Nuevo",
      "created_at": "2023-10-03T12:00:00Z"
    }
    ```

##### 4.3 **Ruta: /games/{game_id}/checkpoints**
- **Método:** GET
  - **Descripción:** Retorna una lista de puntos anotados para un juego específico.
  - **Respuesta:**
    ```json
    [
      {
        "id": 1,
        "player_name": "Jugador A",
        "score": 50,
        "timestamp": "2023-10-01T12:00:00Z"
      },
      {
        "id": 2,
        "player_name": "Jugador B",
        "score": 75,
        "timestamp": "2023-10-01T12:05:00Z"
      }
    ]
    ```

##### 4.4 **Ruta: /games/{game_id}/checkpoints**
- **Método:** POST
  - **Descripción:** Anota un nuevo punto para un juego específico.
  - **Entrada:**
    ```json
    {
      "player_name": "Jugador C",
      "score": 100
    }
    ```
  - **Respuesta:**
    ```json
    {
      "id": 3,
      "player_name": "Jugador C",
      "score": 100,
      "timestamp": "2023-10-01T12:10:00Z"
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
└── squad_checkpoints.sqlite
```

#### 6. **Consideraciones Finales**
- **Interactividad:** Utilizar HTMX para cargar y actualizar partes dinámicas de la interfaz sin recargar toda la página.
- **Seguridad:** Implementar validaciones y autenticación si se requiere una versión más avanzada de la aplicación.
- **Escalabilidad:** Mantener el código autocontenido en `main_output.py` para facilitar futuras actualizaciones y mantenimiento.

Este plan técnico proporciona una base sólida para desarrollar la aplicación solicitada, asegurando que todas las partes del sistema estén bien definidas y separadas según las reglas establecidas.