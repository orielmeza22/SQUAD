// script.js

document.getElementById('create-form').addEventListener('submit', function(event) {
    event.preventDefault();
    const nombre = document.querySelector('#create-form input[name="nombre"]').value;
    const fecha = document.querySelector('#create-form input[name="fecha"]').value;

    fetch('/turnos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nombre, fecha })
    }).then(response => response.json())
      .then(data => console.log('Success:', data))
      .catch((error) => console.error('Error:', error));
});

document.getElementById('edit-form').addEventListener('submit', function(event) {
    event.preventDefault();
    const id = document.querySelector('#edit-form input[name="id"]').value;
});

document.getElementById('delete-btn').addEventListener('click', function(event) {
    event.preventDefault();
});