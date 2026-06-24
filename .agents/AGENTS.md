# Reglas de Optimización de Tokens (Token Saving Rules)

Para ahorrar la mayor cantidad de tokens posible y evitar alcanzar los límites del modelo, debes seguir estrictamente estas reglas de comportamiento:

1. **Edición Directa con Herramientas**: Modifica los archivos del código utilizando las herramientas `replace_file_content` o `multi_replace_file_content` directamente. **NUNCA** imprimas bloques de código grandes o archivos completos en tu respuesta de chat.
2. **Explicación Ultra-Concisa**: En el chat, limita tu respuesta a explicar en una o dos líneas qué archivos se cambiaron y por qué. No re-expliques la lógica del código ni des explicaciones redundantes.
3. **Muestra Solo Diffs**: Si es estrictamente necesario mostrar código en el chat (por ejemplo, para explicar una alternativa), muestra únicamente un fragmento de diff pequeño (máximo 10 líneas), nunca el código completo.
4. **Sin Respuestas de Cortesía ni Disculpas**: Evita textos de relleno como "Entendido", "Lo siento", o explicaciones introductorias largas. Ve directo al grano.
5. **No Actualizar Walkthroughs en Detalle en el Chat**: Los walkthroughs deben escribirse en su respectivo archivo Markdown. No resumas el contenido del walkthrough en tu mensaje de chat; solo pon el enlace al archivo.
6. **Búsquedas Selectivas (Contexto Reducido)**: Al explorar o depurar, nunca busques ni leas archivos en `node_modules`, `dist`, `.git` o `.pycache`. Usa glob patterns precisos en `grep_search` e `Includes`.
7. **Sin Búsquedas Web Redundantes**: Si la solución técnica es estándar (FastAPI, React, Python), no busques en la web; usa tu base de conocimiento directamente.
8. **Edición Enfocada**: Modifica únicamente las líneas estrictamente necesarias utilizando rangos mínimos en `replace_file_content` para reducir el tamaño del diff de entrada y salida.
9. **Detener Bucles**: Si una tarea o error se repite más de 2 veces, detente e informa en vez de continuar ejecutando herramientas de manera recursiva.
