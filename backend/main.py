from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import get_db
from . import crud
import joblib

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

model = joblib.load("../ml_model/credit_model.joblib")

@app.post("/request-loan")
def request_loan(income: float, debt: float, age: int):
    # AI Prediction
    prediction = model.predict([[income, debt, age]])[0]
    
    if prediction == 0:
        return {"status": "Denied", "reason": "AI flagged high financial risk"}
    
    # If prediction == 1, proceed to Blockchain logic...
    return {"status": "Approved", "next_step": "Triggering Smart Contract"}