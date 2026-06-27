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
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
    except Exception: pass
    conn.row_factory = sqlite3.Row
    return conn

# SQUAD_INJECT_DB_SCHEMA

# SQUAD_INJECT_LOGIC

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)