# 🗺️ Roadmap Estratégico SQUAD App Builder V5

## Feedback del Problema Actual
El error `docker-compose no se reconoce` expuso una falla en el diseño actual: 
1. El Agente Arquitecto genera infraestructuras ideales (como Docker) sin contexto.
2. El script `Lanzar Sistema` ejecuta ciegamente los comandos asumiendo que el host (tu PC) tiene instaladas todas las herramientas.
3. Al fallar, lanza una consola CMD que crashea inmediatamente, ocultando los logs.

## Hoja de Ruta de Nuevas Funcionalidades (V5)

### 1. Pre-Flight Check (Conciencia de Entorno)
- **Descripción**: El servidor Python escaneará los ejecutables del sistema operativo (`node`, `docker`, `python`, `git`) antes de empezar.
- **Objetivo**: Limitar y obligar al Agente Arquitecto a diseñar la solución *únicamente* empleando tecnologías instaladas en la computadora del usuario.

### 2. Terminal Embebida (Visor de Logs en UI)
- **Descripción**: Eliminar los Pop-ups de CMD de Windows. Integrar una terminal HTML/JS en la parte inferior del `index.html`.
- **Objetivo**: Poder ver los resultados de `npm install` o los errores de compilación directamente en la interfaz del constructor.

### 3. Editor de Código Interactivo
- **Descripción**: Transformar la ventana de código actual (solo lectura con `<pre>`) en un editor funcional (Live Editor).
- **Objetivo**: Permitir al usuario realizar correcciones manuales rápidas a `app.py` o dependencias antes de presionar "Lanzar Sistema".

### 4. Ciclo de Iteración (Chat sobre Código Existente)
- **Descripción**: Habilidad de no re-generar todo desde cero cada vez. Implementar un pipeline secundario donde el promt diga "Modifica el frontend para ser oscuro" y los agentes alteren inteligentemente solo los archivos requeridos.

### 5. Agente Dev-Ops (Auto-Resolución de Crash)
- **Descripción**: Si un comando de "Lanzar Sistema" tira error y falla, capturar el log de error de la nueva terminal embebida y pasárselo a un Agente Linter de emergencia, que sobrescriba el código dañado y reinicie el ciclo de manera autónoma.

### 6. Abstracción de Base de Datos (ORM / DB Agnostic)
- **Descripción**: Transicionar de sentencias SQL directas con `sqlite3` a un ORM multiplataforma (como SQLAlchemy/SQLModel para Python o Prisma/Drizzle para Node.js).
- **Objetivo**: Permitir usar SQLite sin configuración para desarrollo local y escalar a PostgreSQL en producción mediante variables de entorno `.env`, eliminando dependencias locales de Docker propensas a errores.

