import joblib
import os
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from web3 import Web3
from pydantic import BaseModel

# Internal Imports
from .database import get_db
from . import crud
from .config import get_settings

# --- 1. SETUP & MODEL LOADING ---
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR.parent / "ml_model" / "credit_model.joblib"

app = FastAPI()

if MODEL_PATH.exists():
    model = joblib.load(str(MODEL_PATH))
    print(f"✅ AI Model successfully loaded from: {MODEL_PATH}")
else:
    print(f"❌ Error: Model not found at {MODEL_PATH}")
    model = None

# --- 2. SCHEMAS ---
class LoanRequest(BaseModel):
    income: float
    debt: float
    wallet: str
    amount: float

# --- 3. BLOCKCHAIN HELPERS ---
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

# --- 4. ROUTES ---

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
async def request_loan(request: LoanRequest, settings=Depends(get_settings)):
    #print(f"Processing loan request for: {request.wallet}")
    # 1. Sanitize the input - Remove spaces and invisible BOM characters
    clean_wallet = request.wallet.strip().replace("\ufeff", "")
    tx_hash = trigger_blockchain_loan(clean_wallet, request.amount, settings)
    print(f"🚀 Processing loan for: {clean_wallet} | Amount: {request.amount} ETH")

    if model is None:
        raise HTTPException(status_code=500, detail="AI Model not loaded on server.")

    try:
        # STEP 1: AI Prediction (Using Income, Debt, and a dummy credit score 750)
        prediction = model.predict([[request.income, request.debt, 750]])[0]
        
        if prediction == 0:
            print(f"❌ AI Rejected: {clean_wallet}")
            return {"status": "Rejected", "reason": "AI flagged high financial risk"}

        # STEP 2: Blockchain Execution
        # Pass the CLEANED wallet here
        tx_hash = trigger_blockchain_loan(request.wallet, request.amount, settings)
        
        if not tx_hash or "ERR" in tx_hash:
             print(f"⚠️ Blockchain Warning: {tx_hash}")
             # We still return 200 so the frontend can show the specific error hash

        return {
            "status": "Approved",
            "ai_score": "High Confidence",
            "transaction_hash": tx_hash,
            "message": "Funds are being transferred via Smart Contract"
        }
    except Exception as e:
        print(f"Server Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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