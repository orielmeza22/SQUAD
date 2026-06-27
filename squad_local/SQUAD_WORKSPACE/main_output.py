from fastapi import FastAPI, HTTPException
from models import ServerModel  # Importa el modelo de servidor
import sqlalchemy.orm as orm
import sqlalchemy.exc as excs

app = FastAPI()

def get_db():
    db = orm.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/servers/", response_model=ServerModel)
async def create_server(server: ServerModel, db: orm.Session = Depends(get_db)):
    db_server = db.query(ServerModel).filter(ServerModel.name == server.name).first()
    if db_server:
        raise HTTPException(status_code=400, detail="Server already exists")
    
    new_server = ServerModel(name=server.name, description=server.description)
    db.add(new_server)
    db.commit()
    db.refresh(new_server)
    return new_server

@app.get("/servers/{server_id}", response_model=ServerModel)
async def read_server(server_id: int, db: orm.Session = Depends(get_db)):
    server = db.query(ServerModel).filter(ServerModel.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    return server

@app.put("/servers/{server_id}", response_model=ServerModel)
async def update_server(server_id: int, updated_server: ServerModel, db: orm.Session = Depends(get_db)):
    db_server = db.query(ServerModel).filter(ServerModel.id == server_id).first()
    if not db_server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    db_server.name = updated_server.name
    db_server.description = updated_server.description
    db.commit()
    return db_server

@app.delete("/servers/{server_id}", response_model=dict)
async def delete_server(server_id: int, db: orm.Session = Depends(get_db)):
    deleted_server = db.query(ServerModel).filter(ServerModel.id == server_id).first()
    if not deleted_server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    db.delete(deleted_server)
    db.commit()
    return {"message": "Server deleted"}
