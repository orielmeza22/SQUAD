from fastapi import FastAPI, Request, Form, HTTPException
import sqlite3

app = FastAPI(title="SQUAD Auto-generated App")

# Conexión a SQLite
conn = sqlite3.connect('database.db')

def get_db():
    return conn.cursor()

@app.get("/users/{user_id}", response_model=User)
async def read_user(user_id: int, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": row[0], "name": row[1], "email": row[2]}

@app.get("/products/{product_id}", response_model=Product)
async def read_product(product_id: int, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"id": row[0], "title": row[1], "description": row[2], "price": row[3]}

# Ruta para listar usuarios
@app.get("/")
async def read_users():
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id < 10")
    rows = cursor.fetchall()
    return [{"id": row[0], "name": row[1], "email": row[2]} for row in rows]

# Ruta para listar productos
@app.get("/products")
async def read_products():
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id < 5")
    rows = cursor.fetchall()
    return [{"id": row[0], "title": row[1], "description": row[2], "price": row[3]} for row in rows]

# Ruta para listar usuarios (HTML)
@app.get("/")
async def index():
    return {"html_content": "<h1>Welcome to FastAPI with HTMX!</h1>"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)