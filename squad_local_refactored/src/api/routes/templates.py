"""Project templates apply endpoints.

Migrated 1:1 from the legacy monolith.
"""

import os
import shutil
from fastapi import APIRouter, Body

from ...tools.sys_tools import SysTools

router = APIRouter()

TEMPLATES_GALLERY = {
    "fastapi": {
        "app.py": """from fastapi import FastAPI
import sqlite3

app = FastAPI()

def init_db():
    conn = sqlite3.connect("local_project.db")
    cursor = conn.cursor()
    cursor.execute(\"\"\"
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT
        )
    \"\"\")
    conn.commit()
    conn.close()

init_db()

@app.get("/")
def read_root():
    return {"message": "Welcome to FastAPI + SQLite Starter App!"}

@app.get("/items")
def get_items():
    conn = sqlite3.connect("local_project.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "description": r[2]} for r in rows]
""",
        "requirements.txt": "fastapi\nuvicorn",
        "schema.sql": """CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT
);""",
        "main_output.py": """import uvicorn
import app

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=True)
"""
    },
    "express": {
        "package.json": """{
  "name": "express-starter",
  "version": "1.0.0",
  "main": "server.js",
  "dependencies": {
    "express": "^4.18.2"
  },
  "scripts": {
    "start": "node server.js"
  }
}""",
        "server.js": """const express = require('express');
const app = express();
const PORT = 3001;

app.use(express.static('.'));

app.get('/api/info', (req, res) => {
    res.json({ message: "Hello from Express.js Backend!" });
});

app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});""",
        "index.html": """<!DOCTYPE html>
<html>
<head>
    <title>Express Starter</title>
    <style>
        body { font-family: sans-serif; background: #111; color: #eee; text-align: center; padding-top: 100px; }
        h1 { color: #f59e0b; }
        button { background: #3b82f6; border: none; color: white; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
    </style>
</head>
<body>
    <h1>Express.js Starter Page</h1>
    <button onclick="fetchInfo()">Fetch API Info</button>
    <p id="res"></p>
    <script>
        function fetchInfo() {
            fetch('/api/info')
                .then(r => r.json())
                .then(d => document.getElementById('res').innerText = d.message);
        }
    </script>
</body>
</html>""",
        "main_output.js": """const { exec } = require('child_process');
console.log('Iniciando Express app...');
console.log("npm install && npm start");
"""
    },
    "go": {
        "main.go": """package main

import (
	"fmt"
	"net/http"
)

func main() {
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		fmt.Fprintf(w, "<h1>Go Web Server Starter</h1><p>Running on port 8080</p>")
	})
	fmt.Println("Server starting on http://localhost:8080")
	http.ListenAndServe(":8080", nil)
}
""",
        "go.mod": "module go-starter\n\ngo 1.18",
        "main_output.py": """import subprocess
import os

if __name__ == "__main__":
    print("Corriendo Go App...")
    subprocess.run("go run main.go", shell=True)
"""
    },
    "rust": {
        "Cargo.toml": """[package]
name = "rust-starter"
version = "0.1.0"
edition = "2021"

[dependencies]
tokio = { version = "1", features = ["full"] }
axum = "0.6"
""",
        "src/main.rs": """use axum::{routing::get, Router};

#[tokio::main]
async fn main() {
    let app = Router::new().route("/", get(|| async { "Hello from Rust (Axum) Web Server!" }));

    let addr = std::net::SocketAddr::from(([0, 0, 0, 0], 8080));
    println!("listening on http://{}", addr);
    axum::Server::bind(&addr)
        .serve(app.into_make_service())
        .await
        .unwrap();
}
""",
        "main_output.py": """import subprocess
if __name__ == "__main__":
    print("Compilando y corriendo Rust...")
    subprocess.run("cargo run", shell=True)
"""
    }
}


@router.post("/api/templates/apply")
def api_templates_apply(data: dict = Body(default={})):
    """Wipe workspace and apply a starter template from gallery."""
    template_name = data.get('template', '')
    try:
        if template_name not in TEMPLATES_GALLERY:
            raise Exception(f"Plantilla '{template_name}' no soportada.")

        if os.path.exists(SysTools.WORKSPACE):
            for item in os.listdir(SysTools.WORKSPACE):
                path = os.path.join(SysTools.WORKSPACE, item)
                if item == ".git":
                    continue
                if os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    os.remove(path)

        tpl_files = TEMPLATES_GALLERY[template_name]
        for fname, content in tpl_files.items():
            SysTools.write(fname, content)

        SysTools.git_init_and_commit(f"Applied template: {template_name}")
        return {"success": True, "message": f"Plantilla {template_name} aplicada exitosamente."}
    except Exception as e:
        return {"success": False, "message": str(e)}
