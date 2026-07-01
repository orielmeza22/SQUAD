# ADR 0001: Bifurcación de Layouts (Layout Switch) en Estado de Reposo

## Estado
Aprobado

## Contexto
El frontend de SQUAD cargaba previamente todos los paneles (editor, visor de grafo, logs, formulario de nuevo proyecto, barra superior de estadísticas, etc.) en un único layout sobrecargado, independientemente de si la aplicación estaba en reposo (idle) o ejecutando un enjambre de agentes. Esto causaba fatiga visual y violaba el principio de Progressive Disclosure.

## Decisión
Implementar un switch estructural en `App.tsx` que retorne temprano un lienzo inactivo (`IdleScreen`) centrado si y solo si la ejecución de la tubería no está activa (`!isPipelineRunning`).

Una vez iniciado el enjambre de agentes, la UI conmuta de manera estructural a la pantalla activa, mostrando el grafo y los paneles interactivos de desarrollo.

## Consecuencias
* **Positivas**:
  * Experiencia visual premium al iniciar la aplicación (lienzo limpio con input centrado al estilo buscador).
  * Reducción absoluta de la sobrecarga cognitiva inicial.
  * Mayor facilidad para realizar pruebas automáticas de layout al desacoplar ambos estados en el árbol DOM.
