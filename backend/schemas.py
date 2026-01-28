from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# --- USER SCHEMAS ---
class UserBase(BaseModel):
    full_name: str
    email: str
    income: float

class UserCreate(UserBase):
    pass # We don't want to ask the user for their score!

class UserResponse(UserBase):
    id: int
    credit_score: int
    
    class Config:
        from_attributes = True

# --- LOAN REQUEST SCHEMA ---
# Moved here from main.py to keep things organized
class LoanRequest(BaseModel):
    user_id: int  # <--- NEW FIELD
    income: float
    debt: float
    wallet: str
    amount: float

# --- TRANSACTION SCHEMAS ---
class TransactionBase(BaseModel):
    wallet_address: str
    amount: float

class TransactionCreate(TransactionBase):
    user_id: int  # <--- NEW FIELD
    tx_hash: str
    status: str

# Used for updating a status (e.g. "Approved" -> "Repaid")
class TransactionUpdate(BaseModel):
    status: str

class TransactionResponse(TransactionBase):
    id: int
    tx_hash: str
    status: str
    timestamp: datetime

    class Config:
        from_attributes = True

# --- DEPOSIT REQUEST SCHEMA ---
class DepositRequest(BaseModel):
    user_id: int
    wallet: str
    amount: float