# main_output.py

from fastapi import FastAPI, HTTPException
import uvicorn
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import date, time

app = FastAPI()

# Conexión a SQLite
DATABASE_URL = "sqlite:///turnos.db"
engine = create_engine(DATABASE_URL)
Base = declarative_base(bind=engine)

class Turno(Base):
    __tablename__ = 'turnos'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100))
    fecha = Column(Date)
    hora = Column(Time)

# Crear las tablas si no existen
Base.metadata.create_all(bind=engine)

# Rutas de FastAPI
@app.post("/turnos/", response_model=Turno)
async def crear_turno(turno: Turno):
    session = sessionmaker(bind=engine)()
    try:
        turno_dict = turno.dict()
        turno_dict['fecha'] = date.fromisoformat(turno_dict['fecha'])
        turno_dict['hora'] = time.fromisoformat(turno_dict['hora'])
        nuevo_turno = Turno(**turno_dict)
        session.add(nuevo_turno)
        session.commit()
        return nuevo_turno
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()

@app.get("/turnos/{id}", response_model=Turno)
async def obtener_turno(id: int):
    session = sessionmaker(bind=engine)()
    try:
        turno = session.query(Turno).filter_by(id=id).first()
        if not turno:
            raise HTTPException(status_code=404, detail="Turno no encontrado")
        return turno
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()

@app.put("/turnos/{id}", response_model=Turno)
async def actualizar_turno(id: int, turno: Turno):
    session = sessionmaker(bind=engine)()
    try:
        turno_dict = turno.dict()
        turno_dict['fecha'] = date.fromisoformat(turno_dict['fecha'])
        turno_dict['hora'] = time.fromisoformat(turno_dict['hora'])
        turno_actualizado = session.query(Turno).filter_by(id=id).first()
        if not turno_actualizado:
            raise HTTPException(status_code=404, detail="Turno no encontrado")
        for key, value in turno_dict.items():
            setattr(turno_actualizado, key, value)
        session.commit()
        return turno_actualizado
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()

@app.delete("/turnos/{id}")
async def eliminar_turno(id: int):
    session = sessionmaker(bind=engine)()
    try:
        turno = session.query(Turno).filter_by(id=id).first()
        if not turno:
            raise HTTPException(status_code=404, detail="Turno no encontrado")
        session.delete(turno)
        session.commit()
        return {"message": "Turno eliminado"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()

# Montar el directorio estático
app.mount('/', StaticFiles(directory='.', html=True), name='static')

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT") or 5000))
