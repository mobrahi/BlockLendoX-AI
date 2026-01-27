import joblib
import os
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from web3 import Web3
from pydantic import BaseModel

# Internal Imports
from .database import get_db, engine
from . import crud
from .config import get_settings
from . import database, crud, models, schemas

# --- SETUP & MODEL LOADING ---
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR.parent / "ml_model" / "credit_model.joblib"

# This line tells SQLAlchemy to look at your models and create 
# any tables that don't exist yet in the database.
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

if MODEL_PATH.exists():
    model = joblib.load(str(MODEL_PATH))
    print(f"✅ AI Model successfully loaded from: {MODEL_PATH}")
else:
    print(f"❌ Error: Model not found at {MODEL_PATH}")
    model = None

# --- BLOCKCHAIN HELPERS ---
def trigger_blockchain_loan(
        borrower_address: str, 
        amount_eth: float, 
        settings
    ):
    """Signs and sends a transaction to the local blockchain"""
    try:

        w3 = Web3(Web3.HTTPProvider(settings.rpc_url))

        # This line is the ultimate fix: it cleans and validates the address
        target_address = Web3.to_checksum_address(borrower_address.strip().replace("\ufeff", ""))

        admin_account = w3.eth.account.from_key(settings.private_key)

        # LOG THIS: Make sure the backend is using the address you think it is!
        print(f"DEBUG: Attempting to send from {admin_account.address}")
        print(f"DEBUG: Current Balance of Sender: {w3.from_wei(w3.eth.get_balance(admin_account.address), 'ether')} ETH")

        amount_wei = w3.to_wei(amount_eth, 'ether')
        nonce = w3.eth.get_transaction_count(admin_account.address)
        
        if not w3.is_connected():
            return "0xERROR_W3_CONNECTION"

        if not settings.private_key:
            print("⚠️ No Private Key found - using Mock Hash")
            return "0xMOCK_HASH_NO_PRIVATE_KEY"

        # Setup Account
        admin_account = w3.eth.account.from_key(settings.private_key)
        amount_wei = w3.to_wei(amount_eth, 'ether')
        nonce = w3.eth.get_transaction_count(admin_account.address)

        # Build Transaction (Simple Transfer for now)
        tx = {
            'nonce': w3.eth.get_transaction_count(admin_account.address),
            'to': target_address, # Use the cleaned address hereborrower_address,
            'value': w3.to_wei(amount_eth, 'ether'),
            'gas': 210000,
            'gasPrice': w3.eth.gas_price, # Use live gas price from Ganache
            'chainId': settings.chain_id
        }

        signed_tx = w3.eth.account.sign_transaction(tx, settings.private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return w3.to_hex(tx_hash)
    
    except Exception as e:
        print(f"❌ FULL BLOCKCHAIN ERROR: {str(e)}")
        return f"0xERR_{str(e)[:10]}"

# --- ROUTES ---

@app.get("/health")
def health_check():
    return {"status": "online"}

@app.get("/blockchain-info")
def get_chain_info(settings=Depends(get_settings)):
    w3 = Web3(Web3.HTTPProvider(settings.rpc_url))
    return {
        "connected": w3.is_connected(),
        "chain_id": settings.chain_id,
        "contract": settings.contract_address
    }

@app.post("/request-loan")
async def request_loan(
    request: schemas.LoanRequest, 
    db: Session = Depends(get_db), 
    settings=Depends(get_settings)
):
    # 1. Setup variables
    clean_wallet = request.wallet.strip().replace("\ufeff", "")
    tx_hash = "0xPending"
    
    print(f"🚀 Processing loan: {clean_wallet} | Amount: {request.amount} ETH")
    
    if model is None:
        raise HTTPException(status_code=500, detail="AI Model not loaded.")

    try:
        # STEP 1: AI Prediction
        prediction = model.predict([[request.income, request.debt, 750]])[0]
        
        if prediction == 0:
            print(f"❌ AI Rejected: {clean_wallet}")
            return {"status": "Rejected", "reason": "AI flagged high financial risk"}

        # STEP 2: Blockchain Execution
        tx_hash = trigger_blockchain_loan(clean_wallet, request.amount, settings)

        # STEP 3: Save to SQL Database (The missing link!)
        if tx_hash and "ERR" not in tx_hash:
            tx_schema = schemas.TransactionCreate(
                wallet_address=clean_wallet,
                amount=request.amount,
                tx_hash=tx_hash,
                status="Approved"
            )
            crud.create_transaction(db, tx_schema)
            print(f"💾 SQL: Transaction {tx_hash} saved to fintech.db")
        
        return {
            "status": "Approved", 
            "transaction_hash": tx_hash,
            "ai_score": "High Confidence"
        }

    except Exception as e:
        print(f"🔥 Route Error: {e}")
        return {"status": "Error", "transaction_hash": f"0xERR_{str(e)[:10]}"}

# Add this new route to fetch history
@app.get("/history")
def read_history(db: Session = Depends(get_db)):
    return crud.get_transactions(db)

@app.post("/deposit")
def deposit_funds(lender_address: str, amount_eth: float):
    # Temporary mock for Lender logic
    print(f"💰 Lender {lender_address} intent: {amount_eth} ETH")
    return {"status": "success", "message": f"Deposited {amount_eth} ETH"}

# Profile/Signup Routes
@app.post("/signup")
def signup(name: str, email: str, income: float, db: Session = Depends(get_db)):
    return crud.create_user(db, name, email, income)

@app.get("/profile/{user_id}")
def view_profile(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# --- NEW: UPDATE & DELETE ROUTES ---

@app.put("/transaction/{tx_id}", response_model=schemas.TransactionResponse)
def update_loan_status(tx_id: int, update_data: schemas.TransactionUpdate, db: Session = Depends(database.get_db)):
    """Update a loan status (e.g. to 'Repaid')"""
    updated_tx = crud.update_transaction_status(db, tx_id, update_data.status)
    if not updated_tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return updated_tx

@app.delete("/transaction/{tx_id}")
def delete_loan_record(tx_id: int, db: Session = Depends(database.get_db)):
    """Delete a transaction log (Admin only)"""
    success = crud.delete_transaction(db, tx_id)
    if not success:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"status": "success", "message": f"Transaction {tx_id} deleted"}