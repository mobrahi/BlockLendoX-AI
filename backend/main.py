import joblib
import os
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from web3 import Web3
from pydantic import BaseModel

# Internal Imports
from .database import get_db, engine
from . import crud, models
from .config import get_settings
from . import database, crud, schemas
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request 
from .schemas import LoanRequest, DepositRequest

# --- SETUP & MODEL LOADING ---
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR.parent / "ml_model" / "credit_model.joblib"

# --- Load the AI ---
if MODEL_PATH.exists():
    ml_model = joblib.load(str(MODEL_PATH)) # <--- RENAME THIS to 'ml_model'
    print(f"✅ AI Model successfully loaded from: {MODEL_PATH}")
else:
    print(f"❌ Error: Model not found at {MODEL_PATH}")
    ml_model = None # <--- RENAME THIS

# This line tells SQLAlchemy to look at your models and create 
# any tables that don't exist yet in the database.
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# 1. Mount Static Files (CSS)
# We use BASE_DIR logic to be safe with paths
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# 2. Setup Templates (HTML)
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# 3. Create the Landing Page Route
@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

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
    # 1. Fetch User (The Source of Truth)
    user = crud.get_user(db, request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Logic Shift: Use the INCOME from the Database, not the form!
    db_income = user.income
    print(f"🕵️ Verification: Using DB Income for {user.full_name}: ${db_income}")

    # 3. Sanitize input
    clean_wallet = request.wallet.strip().replace("\ufeff", "")

    try:
        # STEP 1: AI Prediction (Now using db_income!)
        # We pass db_income instead of request.income
        prediction = ml_model.predict([[db_income, request.debt, 750]])[0]
        
        if prediction == 0:
            return {"status": "Rejected", "reason": "AI flagged risk based on PROFILE income."}

        # ... (rest of the blockchain/db logic) ...
# @app.post("/request-loan")
# async def request_loan(
#     request: schemas.LoanRequest, 
#     db: Session = Depends(get_db), 
#     settings=Depends(get_settings)
# ):
#     # 1. Setup variables
#     clean_wallet = request.wallet.strip().replace("\ufeff", "")
#     tx_hash = "0xPending"
    
#     print(f"🚀 Processing loan: {clean_wallet} | Amount: {request.amount} ETH")
    
#     if ml_model is None:
#         raise HTTPException(status_code=500, detail="AI Model not loaded.")

#     try:
#         # STEP 1: AI Prediction
#         # We simulate a credit score look-up based on their income history
#         # (In a real app, this would come from Equifax or the User DB)
        
#         # Logic: If they have high income, give them a good 'simulated' score for the demo
#         simulated_score = 750 if request.income > 3000 else 550
#         # Pass the matched features: [Income, Debt, Credit Score]
#         # Notice we pass 'simulated_score' (750), which is now valid because the model knows scores go up to 850.
#         prediction = ml_model.predict([[request.income, request.debt, simulated_score]])[0]

#         print(f"🤖 AI Inputs: Income={request.income}, Debt={request.debt}, Score={simulated_score}")
#         print(f"🤖 AI Result: {prediction}")
        
#         if prediction == 0:
#             print(f"❌ AI Rejected: {clean_wallet}")
#             return {"status": "Rejected", "reason": "AI flagged high financial risk"}

        # STEP 2: Blockchain Execution
        tx_hash = trigger_blockchain_loan(clean_wallet, request.amount, settings)

        # STEP 3: Save to SQL Database (The missing link!)
        if tx_hash and "ERR" not in tx_hash:
            tx_schema = schemas.TransactionCreate(
                wallet_address=clean_wallet,
                amount=request.amount,
                tx_hash=tx_hash,
                status="Approved",
                user_id=request.user_id
            )
            crud.create_transaction(db, tx_schema, user_id=request.user_id)
            print(f"💾 SQL: Transaction {tx_hash} saved to fintech.db")

        return {
            "status": "Approved", 
            "transaction_hash": tx_hash,
            "ai_score": "High Confidence"
        }

    except Exception as e:
        print(f"🔥 Route Error: {e}")
        return {"status": "Error", "transaction_hash": f"0xERR_{str(e)[:10]}"}


# @app.post("/request-loan")
# async def request_loan(
#     request: schemas.LoanRequest, 
#     db: Session = Depends(get_db), 
#     settings=Depends(get_settings)
# ):
#     # 1. Setup variables
#     clean_wallet = request.wallet.strip().replace("\ufeff", "")
#     tx_hash = "0xPending"
    
#     print(f"🚀 Processing loan: {clean_wallet} | Amount: {request.amount} ETH")
    
#     if model is None:
#         raise HTTPException(status_code=500, detail="AI Model not loaded.")

#     try:
#         # STEP 1: AI Prediction
#         prediction = model.predict([[request.income, request.debt, 750]])[0]
        
#         if prediction == 0:
#             print(f"❌ AI Rejected: {clean_wallet}")
#             return {"status": "Rejected", "reason": "AI flagged high financial risk"}

#         # STEP 2: Blockchain Execution
#         tx_hash = trigger_blockchain_loan(clean_wallet, request.amount, settings)

#         # STEP 3: Save to SQL Database (The missing link!)
#         if tx_hash and "ERR" not in tx_hash:
#             tx_schema = schemas.TransactionCreate(
#                 wallet_address=clean_wallet,
#                 amount=request.amount,
#                 tx_hash=tx_hash,
#                 status="Approved"
#             )
#             crud.create_transaction(db, tx_schema)
#             print(f"💾 SQL: Transaction {tx_hash} saved to fintech.db")
        
#         return {
#             "status": "Approved", 
#             "transaction_hash": tx_hash,
#             "ai_score": "High Confidence"
#         }

#     except Exception as e:
#         print(f"🔥 Route Error: {e}")
#         return {"status": "Error", "transaction_hash": f"0xERR_{str(e)[:10]}"}

# Add this new route to fetch history
@app.get("/history")
def read_history(db: Session = Depends(get_db)):
    return crud.get_transactions(db)

# Profile/Signup Routes
@app.post("/signup", response_model=schemas.UserResponse)
def signup(
    user: schemas.UserCreate,  # <--- Now expects JSON matching the schema
    db: Session = Depends(get_db)
):
    # Pass the SINGLE schema object to CRUD
    return crud.create_user(db=db, user=user)

@app.get("/profile/{user_id}")
def view_profile(user_id: int, db: Session = Depends(get_db)):
    # ✅ NEW: Use the correct name defined in crud.py
    user = crud.get_user(db, user_id)
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

# --- NEW: POOL BALANCE ENDPOINT ---
@app.get("/pool-balance")
def get_pool_balance(settings=Depends(get_settings)):
    try:
        w3 = Web3(Web3.HTTPProvider(settings.rpc_url))
        if not w3.is_connected():
            return {"balance": 0.0, "error": "Blockchain offline"}
        
        # Get the balance of the Admin Account (The "Pool")
        admin_account = w3.eth.account.from_key(settings.private_key).address
        balance_wei = w3.eth.get_balance(admin_account)
        balance_eth = w3.from_wei(balance_wei, 'ether')
        
        return {"balance": float(balance_eth), "admin_address": admin_account}
    except Exception as e:
        print(f"Pool Error: {e}")
        return {"balance": 0.0, "error": str(e)}

# --- NEW: DEPOSIT ENDPOINT ---

@app.post("/deposit")
def deposit_liquidity(
    request: schemas.DepositRequest, 
    db: Session = Depends(get_db)
):
    # 1. Sanitize Input
    clean_wallet = request.wallet.strip().replace("\ufeff", "")
    print(f"💰 Deposit Request: {clean_wallet} | {request.amount} ETH")
    
    # 2. Create Mock Hash (Since we don't sign deposits on backend)
    mock_hash = f"0xDEPOSIT_{clean_wallet[:4]}_{request.amount}"
    
    try:
        # 3. Create the Schema Object (The Fix!)
        # We must bundle the data into the Pydantic model expected by crud.py
        deposit_tx = schemas.TransactionCreate(
            wallet_address=clean_wallet,
            amount=request.amount,
            tx_hash=mock_hash,
            status="Liquidity Added"
        )

        # 4. Pass the SINGLE object to CRUD
        crud.create_transaction(db, deposit_tx)
        
        return {"status": "Success", "message": "Liquidity recorded in ledger"}

    except Exception as e:
        print(f"🔥 Deposit Error: {e}") # Print error to terminal for debugging
        raise HTTPException(status_code=500, detail=str(e))