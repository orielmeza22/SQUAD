-- SQL script to create tables and insert test data

-- Create patients table
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create turns table
CREATE TABLE IF NOT EXISTS turns (
    id INTEGER PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id),
    doctor_name TEXT NOT NULL,
    appointment_time DATETIME NOT NULL
);

-- Insert test data into patients table
INSERT INTO patients (name) VALUES ('Paciente A');
INSERT INTO patients (name) VALUES ('Paciente B');
INSERT INTO patients (name) VALUES ('Paciente C');

-- Insert test data into turns table
INSERT INTO turns (patient_id, doctor_name, appointment_time) VALUES (1, 'Doctor A', '2023-10-01T14:00:00Z');
INSERT INTO turns (patient_id, doctor_name, appointment_time) VALUES (1, 'Doctor B', '2023-10-01T15:00:00Z');
INSERT INTO turns (patient_id, doctor_name, appointment_time) VALUES (2, 'Doctor C', '2023-10-02T16:00:00Z');
