import os
import re
import sys
import sqlite3
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

def get_db():
    conn = sqlite3.connect('medical_turns.sqlite')
    conn.row_factory = sqlite3.Row
    return conn

app = FastAPI(title="SQUAD Auto-generated App")

# Mount static files
app.mount("/static", StaticFiles(directory="."), name="static")

templates = Jinja2Templates(directory="templates/")

@app.on_event("startup")
def startup_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS turns (
            id INTEGER PRIMARY KEY,
            patient_id INTEGER REFERENCES patients(id),
            doctor_name TEXT NOT NULL,
            appointment_time DATETIME NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.get('/', response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get('/patients', response_class=JSONResponse)
def get_patients():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM patients')
    patients = cursor.fetchall()
    conn.close()
    return [dict(patient) for patient in patients]

@app.post('/patients', response_class=JSONResponse)
def create_patient(name: str = Form(...)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO patients (name) VALUES (?)', (name,))
    conn.commit()
    patient_id = cursor.lastrowid
    conn.close()
    return {"id": patient_id, "name": name}

@app.get('/patients/{patient_id}/turns', response_class=JSONResponse)
def get_turns(patient_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM turns WHERE patient_id = ?', (patient_id,))
    turns = cursor.fetchall()
    conn.close()
    return [dict(turn) for turn in turns]

@app.post('/patients/{patient_id}/turns', response_class=JSONResponse)
def create_turn(patient_id: int, doctor_name: str = Form(...), appointment_time: str = Form(...)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO turns (patient_id, doctor_name, appointment_time) VALUES (?, ?, ?)', (patient_id, doctor_name, appointment_time))
    conn.commit()
    turn_id = cursor.lastrowid
    conn.close()
    return {"id": turn_id, "doctor_name": doctor_name, "appointment_time": appointment_time}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)