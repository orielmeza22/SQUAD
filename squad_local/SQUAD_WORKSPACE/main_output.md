from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, Column, Integer, String
import datetime

app = FastAPI()

DATABASE_URL = "sqlite:///./turnos.db"
engine = create_engine(DATABASE_URL)

class Turno(Base):
    __tablename__ = 'turnos'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100))
    fecha = Column(datetime.date)  # Asegúrate de importar datetime
    hora = Column(datetime.time)   # Asegúrate de importar datetime

Base.metadata.create_all(engine)

@app.post("/turnos/", response_model=Turno)
async def crear_turno(turno: Turno):
    with engine.connect() as connection:
        result = connection.execute(Turno.__table__.insert(), [dict(** turno.dict())])
        return {"id": result.inserted_primary_key[0]}

@app.get("/turnos/{id}", response_model=Turno)
async def obtener_turno(id: int):
    with engine.connect() as connection:
        result = connection.execute(Turno.__table__.select().where(Turno.id == id))
        return dict(result.fetchone())

@app.put("/turnos/{id}", response_model=Turno)
async def actualizar_turno(id: int, turno: Turno):
    with engine.connect() as connection:
        result = connection.execute(
            Turno.__table__.update()
            .where(Turno.id == id)
            .values(** turno.dict())
        )
        return {"id": id}

@app.delete("/turnos/{id}")
async def eliminar_turno(id: int):
    with engine.connect() as connection:
        result = connection.execute(
            Turno.__table__.delete()
            .where(Turno.id == id)
        )
        return {"deleted_rows": result.rowcount}
