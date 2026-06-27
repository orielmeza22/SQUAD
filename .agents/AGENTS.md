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
10. **Autocomprobación Obligatoria (Closed-Loop)**: Antes de dar un cambio por finalizado, debes ejecutar los comandos necesarios (`run_command`) para verificar que el archivo modificado compila, no tiene errores de sintaxis y los tests pasan.
11. **Formato Estructurado en el Chat**: Limita tus respuestas en el chat a una tabla en Markdown que indique `[Archivo modificado]`, `[Acción]` y `[Estado del Test/Compilación (OK/Error)]`, seguida de la explicación en una o dos líneas como máximo.
12. **Alineación de Diseño Interactiva**: Para cualquier cambio de arquitectura o decisión compleja, propón opciones de forma clara y simplificada para que el usuario pueda decidir con facilidad.
13. **Seguir CLAUDE.md**: Lee y respeta las instrucciones de `CLAUDE.md` en la raíz del repositorio para levantar la app, correr tests y seguir la arquitectura, evitando análisis redundantes del código.

# Filosofía de Trabajo y Reglas de Desarrollo (Julien's Mindset)

## 🧠 Mentalidad de Alto Nivel
- **Completitud y Excelencia**: El costo marginal de la completitud con IA es casi cero. Haz el trabajo completo, hazlo bien, con tests y con documentación. No dejes cabos sueltos ni propongas soluciones temporales si la solución permanente está al alcance.
- **Espacio Latente vs. Determinista**:
  - *Espacio Latente (LLM)*: Juicio, patrones, creatividad, análisis difusos.
  - *Espacio Determinista (Código/Scripts)*: Precisión, velocidad, costo cero, reproducible.
  - *Regla*: Si la misma pregunta dos veces produce el mismo resultado por definición, es determinista. No lo hagas en el LLM. Escribe un script (aritmética, zonas horarias, regex, JSON transforms, regex, etc.). El modelo escribe el script, y el script restringe al modelo para siempre.
- **Ventana de Contexto**: Es tu único control sobre el modelo. Mantenla limpia y relevante. Sin basura.

## 🚫 Reglas No Negociables
- **Tests y Evals en cada Commit**: Todo cambio o bugfix debe incluir su test correspondiente y su suite de evals. "Agregaré tests después" está prohibido.
  - *Gate tests*: Locales, rápidos (<2s), deterministas.
  - *Periodic evals*: Más lentos, miden calidad real.
- **Resultados Medibles**: Cada feature debe indicar la métrica, paso del flujo o comportamiento de usuario que mejora.
- **Acceso LLM**: No uses APIs LLM externas directamente a menos que se indique. Usa el servicio local de Claude Code.
- **Elección Tecnológica**: Vanilla por defecto. Sin frameworks de moda innecesarios. Busca librerías establecidas primero.

## 🏛️ Arquitectura: Servicios Primero
- Independencia total por carpetas: `services/<service-name>/`.
- Comunicación estricta por contratos limpios (`contracts/` o `schemas/`).
- Sin estado mutable compartido de forma directa.
- release/deploy independiente.

## 💬 Comunicación y Estado de Completitud
- Directa, corta, concreta, sin preámbulos. Usa nombres de archivo y líneas exactas.
- Sin palabras de IA (*delve, crucial, robust, comprehensive, nuanced, multifaceted, pivotal, landscape, etc.*).
- Al final de cada tarea reportar exactamente uno de: `DONE`, `DONE_WITH_CONCERNS`, `BLOCKED`, `NEEDS_CONTEXT`.
- Confirmar commit/push y reportar comandos exactos para reiniciar servicios tras finalizar.
- Los trabajos en segundo plano deben reportar progreso cada 5 minutos en consola y a `/tmp/<job-name>/progress.log`.

## 🛡️ Seguridad
- Nunca subir secretos/claves. Verificar `.gitignore` si se edita `.env`.
- Confirmación explícita antes de comandos destructivos (`rm -rf`, `git reset --hard`, `DROP TABLE`, etc.).
- Nunca saltar hooks con `--no-verify`.
# Reglas de Estilo "Ponytail" (YAGNI)

Para evitar la sobre-ingeniería y mantener el código simple y eficiente en tokens:

1. **Filtrado Lazy-Senior (YAGNI)**: Antes de escribir una sola línea de código, hazte estas preguntas en orden:
   * ¿Esta funcionalidad es estrictamente necesaria para cumplir la tarea del usuario? Si no, descártala.
   * ¿Se puede solucionar reutilizando código o funciones que ya existen en el repositorio?
   * ¿Se puede resolver usando la biblioteca estándar o APIs nativas del lenguaje/plataforma en lugar de agregar nuevas dependencias externas?
2. **Código Compacto**: Mantén el código al mínimo absoluto necesario. Evita envoltorios abstractos redundantes, patrones de diseño sobre-ingenieriles (como fábricas o interfaces complejas innecesarias) y mantén la lógica lo más plana y legible posible.
3. **No Agregar Dependencias**: Está prohibido sugerir o instalar nuevas librerías externas a menos que sea técnicamente imposible resolver el requerimiento con lo ya existente en el stack.
