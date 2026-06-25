// frontend/scripts.js

document.getElementById('user-form').addEventListener('submit', function(event){
    event.preventDefault();
    
    const nombre = document.getElementById('nombre').value;
    const apellido = document.getElementById('apellido').value;
    const email = document.getElementById('email').value;
    const telefono = document.getElementById('telefono').value;

    // Aquí puedes hacer una solicitud POST al backend para crear el usuario
    fetch('/api/usuarios', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            nombre,
            apellido,
            email,
            telefono
        })
    })
    .then(response => response.json())
    .then(data => console.log('Success:', data))
    .catch((error) => console.error('Error:', error));
});

Con estos cambios, el archivo `index.html` ahora incluye una referencia al script `scripts.js`, y este script captura el evento del formulario para enviar los datos al backend.