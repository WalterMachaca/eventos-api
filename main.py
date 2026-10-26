from fastapi import FastAPI, Depends, HTTPException, Query 
from pydantic import BaseModel, Field 
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey 
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship

engine = create_engine("sqlite:///eventos.db", connect_args={"check_same_thread": False}) 
SessionLocal = sessionmaker(bind=engine) 
Base = declarative_base()

class EventoDB(Base): 
    __tablename__ = "eventos" 
    id = Column(Integer, primary_key=True, index=True) 
    nombre = Column(String, nullable=False) 
    fecha = Column(String, nullable=False) 
    ciudad = Column(String, nullable=False) 
    capacidad = Column(Integer, nullable=False) 

class InscripcionDB(Base): 
    __tablename__ = "inscripciones" 
    id = Column(Integer, primary_key=True, index=True) 
    evento_id = Column(Integer, ForeignKey("eventos.id"), nullable=False) 
    participante = Column(String, nullable=False) 
    email = Column(String, nullable=False) 
    estado = Column(String, nullable=False, default="confirmado") 
    
Base.metadata.create_all(bind=engine)

class EventoCreate(BaseModel): 
    nombre: str = Field(min_length=2) 
    fecha: str 
    ciudad: str 
    capacidad: int = Field(gt=0) 
    
class EventoUpdate(BaseModel): 
    nombre: str | None = None 
    fecha: str | None = None 
    ciudad: str | None = None 
    capacidad: int | None = Field(default=None, gt=0) 
    
class EventoResponse(BaseModel): 
    id: int 
    nombre: str 
    fecha: str 
    ciudad: str 
    capacidad: int 
    model_config = {"from_attributes": True} 

class InscripcionCreate(BaseModel): 
    participante: str = Field(min_length=2) 
    email: str 

class InscripcionResponse(BaseModel): 
    id: int 
    evento_id: int 
    participante: str 
    email: str 
    estado: str 
    model_config = {"from_attributes": True}    

app = FastAPI(title="Eventos API") 

def get_db(): 
    db = SessionLocal() 
    try: 
        yield db 
    finally: 
        db.close() 

@app.post("/eventos", response_model=EventoResponse, status_code=201)
def crear_evento(evento: EventoCreate, db: Session = Depends(get_db)):
    nuevo = EventoDB(**evento.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@app.get("/eventos/{evento_id}", response_model=EventoResponse, status_code=200)
def obtener_evento(evento_id: int, db: Session = Depends(get_db)):
    evento = db.get(EventoDB, evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return evento

@app.patch("/eventos/{evento_id}", response_model=EventoResponse, status_code=200)
def actualizar_evento(evento_id: int, cambios: EventoUpdate, db: Session = Depends(get_db)):
    evento = db.get(EventoDB, evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    for campo, valor in cambios.model_dump(exclude_unset=True).items():
        setattr(evento, campo, valor)
    db.commit()
    db.refresh(evento)
    return evento

@app.delete("/eventos/{evento_id}", status_code=204)
def eliminar_evento(evento_id: int, db: Session = Depends(get_db)):
    evento = db.get(EventoDB, evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    db.delete(evento)
    db.commit()

@app.post("/eventos/{evento_id}/inscripciones", response_model=InscripcionResponse, status_code=201)
def crear_inscripcion(evento_id: int, inscripcion: InscripcionCreate, db: Session = Depends(get_db)):
    evento = db.get(EventoDB, evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    nueva = InscripcionDB(evento_id=evento_id, **inscripcion.model_dump())
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

@app.get("/eventos/{evento_id}/inscripciones", response_model=list[InscripcionResponse])
def listar_inscripciones(evento_id: int, estado: str | None = None, db: Session = Depends(get_db)):
    evento = db.get(EventoDB, evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    query = db.query(InscripcionDB).filter(InscripcionDB.evento_id == evento_id)
    if estado:
        query = query.filter(InscripcionDB.estado == estado)
    return query.all()

@app.get("/eventos", response_model=list[EventoResponse])
def listar_eventos(
    ciudad: str | None = None,
    page: int = Query(default=1, ge=1),
    limite: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(EventoDB)
    
    if ciudad:
        query = query.filter(EventoDB.ciudad == ciudad)
        
    inicio = (page - 1) * limite
    
    return query.offset(inicio).limit(limite).all()

