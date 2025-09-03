import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DB_URL = os.environ.get("DB_URL", "sqlite:///./aidgent.db")

class Base(DeclarativeBase):
    pass

engine = create_engine(DB_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

def init_db():
    from server.storage.models import Message, SessionRec, SoapSummary, Citation
    Base.metadata.create_all(engine)
