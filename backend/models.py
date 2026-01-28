from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from .database import Base

# --- USER TABLE ---
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    email = Column(String, unique=True, index=True)
    income = Column(Float)
    credit_score = Column(Integer, default=0)

# --- TRANSACTION TABLE (Existing) ---
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    wallet_address = Column(String)
    amount = Column(Float)
    tx_hash = Column(String)
    status = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)