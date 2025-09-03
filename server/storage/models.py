from sqlalchemy import Column, String, Integer, Text
from server.storage.db import Base

class SessionRec(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True)
    created_at = Column(String)
    age_bucket = Column(String)
    consent_flags = Column(Text)

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, index=True)
    role = Column(String)  # "user" | "assistant"
    text = Column(Text)
    state_json = Column(Text)
    created_at = Column(String)

class SoapSummary(Base):
    __tablename__ = "soap_summaries"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, index=True)
    soap_json = Column(Text)
    created_at = Column(String)

class Citation(Base):
    __tablename__ = "citations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, index=True)
    turn_id = Column(Integer)
    doc_id = Column(String)
    snippet_ids = Column(String)
