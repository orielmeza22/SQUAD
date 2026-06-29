STACK: NODE_EJS

### Especificación de Software (SPEC)

#### 1. Introducción:
Este documento define el diseño y arquitectura para una aplicación web simple que cumple con la petición del usuario, utilizando el stack tecnológico `NODE_EJS`. La aplicación consistirá en un servidor Express con una única ruta GET `/hello` que devolverá el mensaje JSON: `{ 'message': 'Hola Mundo' }`.

#### 2. Estructura de carpetas:
- **/public**: Contiene archivos estáticos como HTML, CSS y JavaScript del cliente.
- **/server.js**: Contiene la lógica del servidor Express.

#### 3. Archivos necesarios:

1. **server.js**
   - Este archivo contendrá toda la lógica del servidor Express.
   
2. **public/index.html**
   - Este archivo HTML servirá como punto de entrada para el cliente y mostrará un mensaje simple.

3. **public/style.css**
   - Este archivo CSS proporcionará estilos básicos al HTML.

4. **public/script.js**
   - Este archivo JavaScript puede ser utilizado para agregar funcionalidades adicionales, aunque no es necesario en este caso.

#### 4. Estructura de la base de datos:
- No se utilizará una base de datos SQLite ya que el usuario solo requiere una ruta GET simple y no hay necesidad de almacenamiento persistente.

#### 5. Endpoints y Rutas:

| Endpoint | Método HTTP | Descripción |
|----------|-------------|--------------|
| /hello   | GET         | Devuelve un mensaje JSON: `{ 'message': 'Hola Mundo' }` |

#### 6. Implementación del servidor Express (server.js):

```javascript
// server.js

const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

app.get('/hello', (req, res) => {
    const message = { 'message': 'Hola Mundo' };
    res.json(message);
});

app.listen(PORT, () => {
    console.log(`Servidor escuchando en el puerto ${PORT}`);
});
```

#### 7. Implementación del frontend (public/index.html):

```html
<!-- public/index.html -->

<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Hola Mundo</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <h1>¡Hola Mundo!</h1>
    
    <script src="script.js"></script>
</body>
</html>
```

#### 8. Implementación del frontend (public/style.css):

```css
/* public/style.css */

body {
    font-family: Arial, sans-serif;
}

h1 {
    color: blue;
}
```

#### 9. Implementación del frontend (public/script.js) (opcional):

```javascript
// public/script.js

console.log('Este archivo JavaScript es opcional y no se utiliza en este caso.');
```

### Resumen:
- **Stack**: `NODE_EJS`
- **Estructura de carpetas**:
  - /public: HTML, CSS y JS del cliente.
  - /server.js: Lógica del servidor Express.
- **Endpoints**:
  - GET `/hello`: Devuelve `{ 'message': 'Hola Mundo' }`.

Este diseño cumple con las restricciones del sistema anfitrión y el stack tecnológico seleccionado, proporcionando una solución simple y eficiente para la petición del usuario.