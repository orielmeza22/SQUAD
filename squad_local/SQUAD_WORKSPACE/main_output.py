from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DATABASE = 'turnos.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/turnos', methods=['GET'])
def get_turnos():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM turnos')
    rows = cur.fetchall()
    return jsonify(rows)

@app.route('/turnos/<int:turno_id>', methods=['PUT'])
def update_turno(turno_id):
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('UPDATE turnos SET nombre=:nombre, fecha=:fecha WHERE id=:id', data)
    conn.commit()
    return jsonify({'message': 'Turno actualizado'})

@app.route('/turnos/<int:turno_id>', methods=['DELETE'])
def delete_turno(turno_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM turnos WHERE id=:id', {'id': turno_id})
    conn.commit()
    return jsonify({'message': 'Turno eliminado'})

@app.route('/turnos', methods=['POST'])
def create_turno():
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO turnos (nombre, fecha) VALUES (:nombre, :fecha)', data)
    conn.commit()
    return jsonify({'message': 'Turno creado'})

if __name__ == '__main__':
    app.run(debug=True)
