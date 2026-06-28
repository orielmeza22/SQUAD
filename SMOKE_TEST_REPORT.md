# Smoke Test Report — LangGraph Orchestrator

**Resultado:** ❌ FAIL

**Fecha:** 2026-06-28 20:51:02

**Run ID:** N/A

## Pasos

- ❌ **Sin excepciones en el flujo**: GEMINI_API_KEY no configurada. Añádela a tu archivo .env o .env.local

## Traceback

```
Traceback (most recent call last):
  File "C:\Users\miapu\Downloads\untitled\squad_local_refactored\tests\smoke_test_graph.py", line 76, in main
    run_id = run_graph_pipeline(
        prompt="Hazme una app de lista de tareas (TODO) en FastAPI con SQLite. Endpoints GET y POST en /.",
        model=model
    )
  File "C:\Users\miapu\Downloads\untitled\squad_local_refactored\src\pipeline\graph_orchestrator.py", line 458, in run_graph_pipeline
    raise Exception("GEMINI_API_KEY no configurada. Añádela a tu archivo .env o .env.local")
Exception: GEMINI_API_KEY no configurada. Añádela a tu archivo .env o .env.local

```
