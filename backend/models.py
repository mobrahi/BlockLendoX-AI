from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship # Import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    email = Column(String, unique=True, index=True)
    income = Column(Float)
    credit_score = Column(Integer, default=0)
    
    # Enable "Back Population" (optional but good practice)
    transactions = relationship("Transaction", back_populates="owner")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    
    # --- NEW: FOREIGN KEY ---
    # This links the transaction to the 'users' table
    user_id = Column(Integer, ForeignKey("users.id")) 
    
    wallet_address = Column(String)
    amount = Column(Float)
    tx_hash = Column(String)
    status = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Link back to User
    owner = relationship("User", back_populates="transactions")