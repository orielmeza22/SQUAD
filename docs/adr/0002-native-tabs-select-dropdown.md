# ADR 0002: Selector de Pestañas Secundarias Mediante Elemento Select Nativo

## Estado
Aprobado

## Contexto
Para respetar la Ley de Hick, se redujeron las 11 pestañas de consola a un máximo de 3 visibles, agrupando las 8 restantes en una pestaña "Más" desplegable. El dropdown flotante implementado inicialmente con divs absolutos era invisible debido a que el contenedor de pestañas tiene `overflow-x: auto`, lo cual provoca el recorte (clipping) de cualquier menú que exceda el límite del contenedor en el eje vertical.

## Decisión
Utilizar un elemento `<select>` HTML nativo de la biblioteca estándar para renderizar y gestionar las pestañas secundarias, estilizándolo con CSS para que se integre perfectamente con la visualización estética de las pestañas principales.

## Consecuencias
* **Positivas**:
  * Solución limpia siguiendo la filosofía YAGNI y libre de librerías externas.
  * El despliegue de opciones corre por cuenta del motor nativo del navegador, quedando a salvo de cualquier recorte por CSS `overflow` de contenedores padres.
  * Facilidad de mantenimiento al no requerir estados flotantes ni lógica de detección de clic externo.
