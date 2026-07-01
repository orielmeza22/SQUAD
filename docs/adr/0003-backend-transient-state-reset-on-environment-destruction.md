# ADR 0003: Limpieza de Estado en Memoria durante la Destrucción del Entorno

## Estado
Aprobado

## Contexto
Al invocar la acción "Destruir Workspace", el backend eliminaba correctamente los archivos en el disco, pero mantenía intacto el estado transitorio del proceso en ejecución (logs, historial de chat, diagnósticos activos). Debido a esto, la conexión de logs por EventSource (SSE) del frontend seguía recibiendo el log histórico, volviendo a pintar la información y dando la falsa impresión de que la destrucción había fallado.

## Decisión
Ampliar el endpoint de backend `/api/infra/destroy` para que realice un vaciado explícito de las variables en memoria:
```python
state.pending_writes = {}
state.chat_history = []
state.logs = []
state.launcher_logs = []
state.active_diagnostic = None
```
Complementariamente, se expusieron los setters de estado en la API del frontend de `AppContext` para reiniciar y vaciar las logs y diagnósticos del lado de React.

## Consecuencias
* **Positivas**:
  * Limpieza absoluta del workspace y retorno garantizado del frontend al lienzo inactivo.
  * Consistencia total entre el estado físico de los archivos y los registros visualizados.
  * Mayor robustez y confiabilidad percibida en la herramienta.
