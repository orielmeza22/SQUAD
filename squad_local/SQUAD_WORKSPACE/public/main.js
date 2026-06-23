document.addEventListener('DOMContentLoaded', () => {
    fetch('/turnos')
        .then(response => response.json())
        .then(turnos => {
            const turnosTable = document.getElementById('turnosTable');
            turnos.forEach(turno => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${turno.id}</td>
                    <td>${turno.nombreTurno}</td>
                    <td>${turno.diasActividad}</td>
                `;
                turnosTable.appendChild(row);
            });
        })
        .catch(error => console.error('Error al obtener los turnos:', error));
});