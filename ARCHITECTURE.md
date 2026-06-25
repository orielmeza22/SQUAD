# SQUAD Architecture

## Overview

SQUAD (Software Engineering Autonomous Development) is a multi-agent system that generates full-stack web applications from natural language prompts.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React 19)                     │
│  ┌─────────────┐ ┌──────────────┐ ┌─────────────────────┐   │
│  | AgentConsole| |FileTree      | | MonacoEditorPanel   |   │
│  └─────────────┘ └──────────────┘ └─────────────────────┘   │
│  ┌─────────────┐ ┌──────────────┐ ┌─────────────────────┐   │
│  | DatabaseVis | |Telemetry     | | AppContext          |   │
│  └─────────────┘ └──────────────┘ └─────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/WebSocket
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                       │
│  ┌─────────────────────────────────────────────────────┐     │
│  │ REST Endpoints + WebSocket Server                   │     │
│  └─────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Agent Orchestration                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │Architect │→ │   DBA    │→ │ Backend  │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
│       ↓              ↓              ↓                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ Frontend │← │   QA     │← │ DevOps   │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      LLM Providers                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Gemini   │  │ OpenAI   │  │ Ollama   │  │OpenRouter│    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Tools & Utilities                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │  Cache   │  │ SysTools │  │Validators│                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

## Components

### Frontend (React + TypeScript + Vite)

- **AgentConsole**: Displays agent activity and logs
- **FileTree**: Visualizes generated project structure
- **MonacoEditorPanel**: Code editor with syntax highlighting
- **DatabaseVisualizer**: Shows database schema and data
- **TelemetryMonitor**: Real-time system metrics
- **AppContext**: Global state management

### Backend (FastAPI)

#### Core Modules
- `config.py`: Configuration management
- `state.py`: Application state tracking

#### LLM Providers
- `provider.py`: Abstract base class for LLM providers
- `gemini.py`: Google Gemini integration
- `openai.py`: OpenAI API integration
- `ollama.py`: Local Ollama models
- `openrouter.py`: OpenRouter multi-model access

#### Agents
- `base.py`: Abstract agent base class
- `architect.py`: System architecture design
- `dba.py`: Database schema generation
- `backend.py`: Backend code generation
- `frontend.py`: Frontend component generation
- `qa.py`: Code quality validation
- `devops.py`: Deployment configuration

#### Tools
- `cache.py`: LLM response caching
- `sys_tools.py`: System operations (file I/O, execution)
- `validators.py`: Code and input validation

### Data Flow

1. **User Input** → Frontend sends prompt to API
2. **Orchestration** → Architect agent designs system
3. **Parallel Generation**:
   - DBA creates database schema
   - Backend generates API code
   - Frontend creates UI components
4. **Quality Assurance** → QA validates all generated code
5. **Deployment** → DevOps creates deployment configs
6. **Output** → Complete application delivered to user

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, Vite, TailwindCSS |
| Backend | Python 3.11, FastAPI, Pydantic |
| Database | SQLite (default), PostgreSQL (optional) |
| LLM | Gemini, OpenAI, Ollama, OpenRouter |
| Container | Docker, Docker Compose |
| CI/CD | GitHub Actions |

## Directory Structure

```
/workspace
├── src/                    # Frontend source code
│   ├── components/         # React components
│   ├── context/            # React contexts
│   └── App.tsx             # Main application
├── squad_local_refactored/ # Refactored backend
│   └── src/
│       ├── agents/         # Agent implementations
│       ├── api/            # FastAPI server
│       ├── core/           # Core modules
│       ├── llm/            # LLM providers
│       ├── tools/          # Utility tools
│       └── utils/          # Helper functions
├── squad_local/            # Legacy monolithic backend
├── .github/workflows/      # CI/CD pipelines
├── docker-compose.yml      # Docker orchestration
└── Dockerfile.*            # Container definitions
```

## Extension Points

### Adding New LLM Providers
1. Create new class in `src/llm/` extending `LLMProvider`
2. Implement required methods: `generate()`, `stream()`
3. Register in provider factory

### Adding New Agents
1. Create new class in `src/agents/` extending `BaseAgent`
2. Implement `execute()` method
3. Add to orchestration pipeline

### Custom Tools
1. Add tool functions in `src/tools/`
2. Expose to agents via tool registry
3. Document in agent prompts
