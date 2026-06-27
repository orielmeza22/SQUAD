# CLAUDE.md

## Build and Test Commands
- Run all python tests: `python -m pytest squad_local_refactored/tests/` (or `pytest tests/` inside the `squad_local_refactored/` directory)
- Run frontend typecheck: `npm run lint` or `npx tsc --noEmit`
- Run backend lint: `flake8 src` (inside `squad_local_refactored/`)
- Build frontend: `npm run build`

## Development Commands
- Run backend API: `python squad_local_refactored/main.py`
- Run frontend: `npm run dev`

## Code Style and Guidelines
- **Backend**: Python 3.11+, FastAPI, Pydantic v2. Use lightweight built-in libraries (like `urllib`) for LLM/API requests instead of heavy SDK dependencies. Restrict file operations to `SysTools.WORKSPACE` to prevent path traversal.
- **Frontend**: React 19, TypeScript, Tailwind CSS v4, Vite. State is managed via `AppContext`.
- **Rules**: Keep modules highly decoupled, use strict type hints, and ensure new/modified code passes all tests and compiles cleanly without errors.
