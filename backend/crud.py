from sqlalchemy.orm import Session
from . import database as db_config, models
from sqlalchemy import Column, Integer, String, Float

# Define the User Model
class User(db_config.Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    email = Column(String, unique=True, index=True)
    income = Column(Float)
    credit_score = Column(Integer, default=0)

# Create the table in the database
db_config.Base.metadata.create_all(bind=db_config.engine)

# --- CRUD FUNCTIONS ---

def create_user(db: Session, name: str, email: str, income: float):
    db_user = User(full_name=name, email=email, income=income)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def update_user_credit_score(db: Session, user_id: int, score: int):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db_user.credit_score = score
        db.commit()
        db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    return False

def create_transaction(db: Session, wallet: str, amount: float, tx_hash: str, status: str):
    db_tx = models.Transaction(
        wallet_address=wallet, 
        amount=amount, 
        tx_hash=tx_hash, 
        status=status
    )
    db.add(db_tx)
    db.commit()
    db.refresh(db_tx)
    return db_tx

def get_transactions(db: Session, limit: int = 10):
    return db.query(models.Transaction).order_by(models.Transaction.id.desc()).limit(limit).all()