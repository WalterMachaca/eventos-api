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

app = FastAPI(title="Eventos API") 

def get_db(): 
    db = SessionLocal() 
    try: 
        yield db 
    finally: 
        db.close()