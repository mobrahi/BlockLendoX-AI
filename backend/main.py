from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import get_db
from . import crud

app = FastAPI()

@app.post("/signup")
def signup(name: str, email: str, income: float, db: Session = Depends(get_db)):
    return crud.create_user(db, name, email, income)

@app.get("/profile/{user_id}")
def view_profile(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user