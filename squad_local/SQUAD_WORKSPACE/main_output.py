@app.get("/products/{product_id}", response_model=Product)
async def read_product(product_id: int, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"id": row[0], "title": row[1], "description": row[2], "price": row[3]}

# Crear tabla products si no existe
cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    price REAL NOT NULL
)
''')
db.commit()