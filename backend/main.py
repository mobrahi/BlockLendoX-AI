from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import get_db
from . import crud
import joblib
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR.parent / "ml_model" / "credit_model.joblib"

if MODEL_PATH.exists():
    model = joblib.load(str(MODEL_PATH))
    print(f"✅ AI Model successfully loaded from: {MODEL_PATH}")
else:
    print(f"❌ Error: Model not found at {MODEL_PATH}")
    model = None

app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "online"}

@app.post("/signup")
def signup(name: str, email: str, income: float, db: Session = Depends(get_db)):
    return crud.create_user(db, name, email, income)

@app.get("/profile/{user_id}")
def view_profile(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

#model = joblib.load("../ml_model/credit_model.joblib")

@app.post("/request-loan")
def request_loan(income: float, debt: float, age: int):
    # AI Prediction
    prediction = model.predict([[income, debt, age]])[0]
    
    if prediction == 0:
        return {"status": "Denied", "reason": "AI flagged high financial risk"}
    
    # If prediction == 1, proceed to Blockchain logic...
    return {"status": "Approved", "next_step": "Triggering Smart Contract"}

@app.post("/deposit")
def deposit_funds(lender_address: str, amount_eth: float):
    try:
        # 1. Connect to Web3 (Ensure Ganache is running!)
        # 2. Build the transaction for 'depositLiquidity'
        # 3. For a real demo, you'd trigger a MetaMask prompt, 
        #    but for a backend test, we can log the intent:
        
        print(f"💰 Lender {lender_address} is depositing {amount_eth} ETH")
        
        # Return success to Streamlit
        return {"status": "success", "message": f"Deposited {amount_eth} ETH"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# blockchain handshake test     
# @app.get("/test-blockchain")
# def test_blockchain():
#     from web3 import Web3
#     # Use the port showing in your Ganache terminal!
#     w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545")) 
    
#     if w3.is_connected():
#         account_zero = w3.eth.accounts[0]
#         balance = w3.from_wei(w3.eth.get_balance(account_zero), 'ether')
#         return {
#             "status": "Connected",
#             "first_account": account_zero,
#             "balance_eth": balance
#         }
#     else:
#         return {"status": "Failed to connect to Ganache"}