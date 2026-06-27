"""Boilerplate templates for SQUAD 2.0.

Provides immutable chasis structures for FastAPI, Express, and Streamlit.
"""

FASTAPI_HTMX_TEMPLATE = '''import os
import re
import sys
import sqlite3
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="SQUAD Auto-generated App")

# Mount static files
app.mount("/static", StaticFiles(directory="."), name="static")

# Database Helper
DB_FILE = "app_database.db"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# SQUAD_INJECT_DB_SCHEMA

# SQUAD_INJECT_LOGIC

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)
'''

NODE_EJS_TEMPLATE = '''const express = require('express');
const path = require('path');
const Database = require('better-sqlite3');

const app = express();
const db = new Database('app_database.db');

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));
app.use(express.urlencoded({ extended: true }));
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// SQUAD_INJECT_DB_SCHEMA

// SQUAD_INJECT_LOGIC

const port = process.env.PORT || 5000;
app.listen(port, () => {
    console.log(`Server listening on port ${port}`);
});
'''

PYTHON_STREAMLIT_TEMPLATE = '''import os
import sqlite3
import streamlit as st

st.set_page_config(page_title="SQUAD Streamlit App", layout="wide")

DB_FILE = "app_database.db"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# SQUAD_INJECT_DB_SCHEMA

# SQUAD_INJECT_LOGIC
'''
