from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from .database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    wallet_address = Column(String)
    amount = Column(Float)
    tx_hash = Column(String)
    status = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)