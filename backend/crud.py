# from sqlalchemy.orm import Session
# from . import database as db_config, models
# from sqlalchemy import Column, Integer, String, Float

from sqlalchemy.orm import Session
from . import models, schemas

# --- USER CRUD ---
def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(
        full_name=user.full_name, 
        email=user.email, 
        income=user.income
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

# --- TRANSACTION CRUD ---

# CREATE
def create_transaction(db: Session, transaction: schemas.TransactionCreate):
    db_tx = models.Transaction(
        wallet_address=transaction.wallet_address,
        amount=transaction.amount,
        tx_hash=transaction.tx_hash,
        status=transaction.status
    )
    db.add(db_tx)
    db.commit()
    db.refresh(db_tx)
    return db_tx

# READ (All)
def get_transactions(db: Session, limit: int = 20):
    return db.query(models.Transaction).order_by(models.Transaction.id.desc()).limit(limit).all()

# READ (One)
def get_transaction_by_id(db: Session, tx_id: int):
    return db.query(models.Transaction).filter(models.Transaction.id == tx_id).first()

# UPDATE (e.g. Mark as "Repaid")
def update_transaction_status(db: Session, tx_id: int, new_status: str):
    db_tx = db.query(models.Transaction).filter(models.Transaction.id == tx_id).first()
    if db_tx:
        db_tx.status = new_status
        db.commit()
        db.refresh(db_tx)
    return db_tx

# DELETE
def delete_transaction(db: Session, tx_id: int):
    db_tx = db.query(models.Transaction).filter(models.Transaction.id == tx_id).first()
    if db_tx:
        db.delete(db_tx)
        db.commit()
        return True
    return False