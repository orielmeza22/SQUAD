# SQUAD Local - Refactored Infrastructure

## Visión General de la Refactorización

El archivo original `squad_server.py` (4163 líneas) ha sido refactorizado en una arquitectura modular basada en paquetes Python, mejorando:

- **Mantenibilidad**: Módulos pequeños y enfocados en una sola responsabilidad.
- **Testeabilidad**: Cada componente puede ser testeado de forma aislada.
- **Seguridad**: Las API keys se manejan exclusivamente desde variables de entorno.
- **Escalabilidad**: Fácil adición de nuevos proveedores LLM, agentes o endpoints.
- **Claridad**: Estructura de directorios intuitiva y documentación integrada.

## Estructura del Proyecto Refactorizado

```
squad_local_refactored/
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Configuración, carga de .env, settings
│   │   └── state.py           # PipelineState (estado global)
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── base.py            # Interfaz base para proveedores LLM
│   │   ├── ollama.py          # Proveedor Ollama
│   │   ├── gemini.py          # Proveedor Google Gemini
│   │   ├── openai.py          # Proveedor OpenAI
│   │   ├── openrouter.py      # Proveedor OpenRouter
│   │   └── provider.py        # AIProvider unificado con routing inteligente
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── cache.py           # OptTools: caché de respuestas LLM
│   │   ├── sys_tools.py       # SysTools: sistema de archivos, git, linter, etc.
│   │   └── validators.py      # Validadores de código (brackets, quotes, etc.)
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── orchestrator.py    # Lógica principal del orquestador
│   │   └── pipeline.py        # Ejecución de pipelines de agentes
│   ├── api/
│   │   ├── __init__.py
│   │   ├── app.py             # FastAPI app y middleware
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── files.py       # Endpoints de gestión de archivos
│   │   │   ├── settings.py    # Endpoints de configuración
│   │   │   ├── llm.py         # Endpoints de LLM y providers
│   │   │   ├── git.py         # Endpoints de Git
│   │   │   ├── system.py      # Endpoints del sistema (puertos, procesos)
│   │   │   └── agent.py       # Endpoints de ejecución de agentes
│   │   └── middleware.py      # Middleware CORS y otros
│   └── utils/
│       ├── __init__.py
│       ├── logger.py          # Logging estructurado
│       └── helpers.py         # Funciones utilitarias (sanitización, etc.)
├── tests/
│   ├── __init__.py
│   ├── test_llm_providers.py
│   ├── test_sys_tools.py
│   └── test_api_routes.py
├── .env.example
├── requirements.txt
├── pyproject.toml
├── README.md
└── main.py                    # Punto de entrada (uvicorn)
```

## Principales Mejoras de Infraestructura

### 1. Separación de Responsabilidades (Single Responsibility Principle)

**Antes:** Un único archivo de 4163 líneas con clases mezcladas (LLM, sistema, API, estado).

**Ahora:**
- `src/llm/`: Solo lógica de comunicación con modelos de lenguaje.
- `src/tools/`: Solo herramientas de sistema (archivos, git, linter).
- `src/api/`: Solo definición de rutas y endpoints FastAPI.
- `src/core/`: Configuración y estado global.
- `src/agents/`: Lógica de negocio y orquestación.

### 2. Gestión de Configuración Segura

**Antes:** Carga de `.env` dispersa y repetida en múltiples funciones.

**Ahora:** `src/core/config.py` centraliza:
- Carga única de variables de entorno al iniciar.
- Validación de configuración requerida.
- Settings persistentes en `squad_settings.json`.
- Sin hardcodeo de API keys.

```python
# src/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    workspace: str = "./SQUAD_WORKSPACE"
    ollama_host: str = "http://127.0.0.1:11434"
    default_model: str = "gemini-2.5-flash"
    temperature: float = 0.3
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

### 3. Proveedores LLM como Estrategia Intercambiable

**Antes:** Clases estáticas acopladas con lógica condicional dispersa.

**Ahora:** Patrón Strategy con interfaz común:

```python
# src/llm/base.py
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, model: str, prompt: str = None, messages: list = None, 
                 is_json: bool = False, temperature: float = 0.3) -> str:
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        pass

# src/llm/gemini.py
class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def generate(self, model, prompt=None, messages=None, is_json=False, temperature=0.3):
        # Implementación limpia y testeable
        ...
```

### 4. Routing Inteligente y Fallback Transparente

**Antes:** Lógica de fallback enterrada en `AIProvider.generate()`.

**Ahora:** `src/llm/provider.py` implementa:
- Smart routing basado en tipo de tarea (planificación vs. generación).
- Fallback automático entre proveedores (Gemini → Ollama → OpenAI).
- Caché transparente de respuestas.
- Tracking de tokens y costos.

### 5. API FastAPI Modular

**Antes:** 1500+ líneas de endpoints en un solo archivo, con duplicación de lógica.

**Ahora:** Rutas organizadas por dominio:

```python
# src/api/routes/files.py
from fastapi import APIRouter, Body, HTTPException

router = APIRouter(prefix="/api", tags=["files"])

@router.post("/create")
def create_file(data: dict = Body()):
    ...

@router.delete("/delete")
def delete_file(data: dict = Body()):
    ...

# src/api/app.py
from fastapi import FastAPI
from .routes import files, settings, llm, git, system, agent

app = FastAPI(title="SQUAD Local API", version="7.0.0-refactored")

app.include_router(files.router)
app.include_router(settings.router)
app.include_router(llm.router)
app.include_router(git.router)
app.include_router(system.router)
app.include_router(agent.router)
```

### 6. Sistema de Archivos Seguro

**Antes:** Funciones `read()` y `write()` con sanitización repetida y riesgo de path traversal.

**Ahora:** `src/tools/sys_tools.py` con:
- Validación centralizada de paths (`sanitize_path()`).
- Prevención de escritura fuera del workspace.
- Intercepción de archivos críticos configurable.
- Logging de todas las operaciones de escritura.

### 7. Testing y Calidad de Código

**Antes:** Cero tests, difícil de testear por acoplamiento.

**Ahora:**
- Tests unitarios para cada proveedor LLM (con mocks).
- Tests de integración para endpoints API.
- Tests de herramientas de sistema (archivo, git, linter).
- Posibilidad de usar `pytest` con cobertura.

```bash
# Ejecutar tests
pytest tests/ --cov=src --cov-report=html
```

### 8. Logging y Observabilidad

**Antes:** Prints dispersos y logs no estructurados.

**Ahora:** `src/utils/logger.py` con:
- Logging estructurado (JSON opcional).
- Niveles configurables (DEBUG, INFO, WARNING, ERROR).
- Contexto en cada log (request ID, usuario, etc.).
- Integración con sistemas externos (ELK, Datadog).

### 9. Documentación Automática

**Antes:** Sin documentación de API.

**Ahora:** FastAPI genera automáticamente:
- Swagger UI en `/docs`.
- ReDoc en `/redoc`.
- OpenAPI schema en `/openapi.json`.

### 10. Dependencias y Empaquetado

**Antes:** Sin gestión formal de dependencias.

**Ahora:**
- `requirements.txt` con versiones pinneadas.
- `pyproject.toml` para metadata del proyecto.
- Posibilidad de instalar como paquete: `pip install -e .`

## Migración desde la Versión Anterior

1. **Backup:** Copiar `squad_server.py` y `squad_settings.json`.
2. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configurar entorno:**
   ```bash
   cp .env.example .env
   # Editar .env con tus API keys
   ```
4. **Ejecutar:**
   ```bash
   uvicorn src.api.app:app --reload --port 8000
   ```
5. **Validar:** Acceder a `http://localhost:8000/docs` para ver la API.

## Próximos Pasos Recomendados

1. **Añadir tests de regresión** para garantizar que el comportamiento es idéntico.
2. **Implementar autenticación** en endpoints críticos.
3. **Añadir rate limiting** para prevenir abuso de la API.
4. **Containerizar con Docker** para despliegue consistente.
5. **Añadir CI/CD** con GitHub Actions para tests automáticos.
6. **Documentar cada endpoint** con ejemplos de request/response.

---

Esta refactorización transforma una aplicación monolítica difícil de mantener en una arquitectura profesional, escalable y lista para producción, manteniendo toda la funcionalidad original.
