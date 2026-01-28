import joblib
import os
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, Security # Import Security as well
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from web3 import Web3
from pydantic import BaseModel
from fastapi.security import APIKeyHeader

# Internal Imports
from .database import get_db, engine
from . import crud, models
from .config import get_settings
from . import database, crud, schemas
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request 
from .schemas import LoanRequest, DepositRequest

# This creates the "Authorize" button in Swagger
api_key_header = APIKeyHeader(name="X-Admin-Password", auto_error=False)

def validate_admin(api_key: str = Security(api_key_header), settings=Depends(get_settings)):
    if api_key != settings.admin_password:
        raise HTTPException(
            status_code=403, 
            detail="Unauthorized: Invalid Admin Password"
        )
    return True

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
async def request_loan(request: schemas.LoanRequest, 
    db: Session = Depends(get_db), 
    settings=Depends(get_settings)
):  
    # 1. Fetch User Profile
    user = crud.get_user(db, request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 1. --- NEW: HARD GUARDRAIL (Business Logic) ---
    # Rule: Loan cannot be more than 5x the monthly income
    max_loan_limit = user.income * 5 
    if request.amount > max_loan_limit:
        print(f"🛑 Hard Guardrail: Loan {request.amount} exceeds limit {max_loan_limit}")
        return {
            "status": "Rejected", 
            "reason": f"Loan amount (${request.amount}) is too high for your income level."
        }

    # 2. Logic Shift: Use the INCOME from the Database, not the form!
    db_income = user.income
    print(f"🕵️ Verification: Using DB Income for {user.full_name}: ${db_income}")

    # 3. Sanitize input
    clean_wallet = request.wallet.strip().replace("\ufeff", "")

    try:
        # We now pass 4 values to match the new model
        prediction = ml_model.predict([[
            user.income, 
            request.debt, 
            request.amount, # Pass the requested loan amount!
            user.credit_score
        ]])[0]

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
@app.post("/signup", response_model=schemas.UserResponse) # <--- Defines the OUTPUT
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)): # <--- Defines the INPUT
    # --- NEW: Starter Score Logic ---
    # We give a base score so they aren't stuck at 0.
    # High income gets a better head start.
    # Calculate starter score
    starter_score = 610 if user.income >= 3000 else 580
    
    # Create user with the calculated starter score
    db_user = models.User(
        full_name=user.full_name,
        email=user.email,
        income=user.income,
        credit_score=starter_score # Set the starter score here
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/profile/{user_id}")
def view_profile(user_id: int, db: Session = Depends(get_db)):
    # ✅ NEW: Use the correct name defined in crud.py
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# --- NEW: UPDATE & DELETE ROUTES ---

@app.put("/transaction/{tx_id}", response_model=schemas.TransactionResponse)
def update_loan_status(tx_id: int, update_data: schemas.TransactionUpdate, db: Session = Depends(get_db)):
    # 1. Update the Transaction Status
    updated_tx = crud.update_transaction_status(db, tx_id, update_data.status)
    if not updated_tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # 2. --- NEW: Credit Builder Logic ---
    # If the loan was successfully repaid, boost the user's score!
    if update_data.status == "Repaid":
        user = crud.get_user(db, updated_tx.user_id)
        if user:
            # Increase score by 25 points, but cap it at 850 (max credit score)
            new_score = min(user.credit_score + 25, 850)
            user.credit_score = new_score
            db.commit()
            print(f"📈 Credit Boost! {user.full_name} now has a score of {new_score}")

    return updated_tx

@app.delete("/transaction/{tx_id}", dependencies=[Depends(validate_admin)])
def delete_loan_record(tx_id: int, db: Session = Depends(get_db)):
    success = crud.delete_transaction(db, tx_id)
    if not success:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"status": "success", "message": "Record archived"}

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
    clean_wallet = request.wallet.strip().replace("\ufeff", "")
    
    # 1. Verify User Exists (Optional but recommended)
    user = crud.get_user(db, request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User ID not found. Please register first.")

    mock_hash = f"0xDEPOSIT_{clean_wallet[:4]}_{request.amount}"
    
    try:
        # 2. Bundle the user_id into the schema
        deposit_tx = schemas.TransactionCreate(
            user_id=request.user_id, # <--- Link to user!
            wallet_address=clean_wallet,
            amount=request.amount,
            tx_hash=mock_hash,
            status="Liquidity Added"
        )

        # 3. Pass to CRUD
        crud.create_transaction(db, deposit_tx, user_id=request.user_id)
        
        return {"status": "Success", "message": "Liquidity recorded in ledger"}
    except Exception as e:
        print(f"🔥 Deposit Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- NEW: ANALYTICS ENDPOINT ---
@app.get("/analytics/summary")
def get_protocol_summary(db: Session = Depends(get_db)):
    # 1. CALCULATE GLOBAL METRICS
    total_staked = float(db.query(func.sum(models.Transaction.amount)).filter(models.Transaction.status == "Liquidity Added").scalar() or 0)
    total_approved = float(db.query(func.sum(models.Transaction.amount)).filter(models.Transaction.status == "Approved").scalar() or 0)
    total_repaid = float(db.query(func.sum(models.Transaction.amount)).filter(models.Transaction.status == "Repaid").scalar() or 0)
    
    # Logic: Out on Loan is what was approved but not yet repaid
    out_on_loan = max(total_approved - total_repaid, 0)
    # Logic: Current Pool is Staked minus what is currently out
    current_pool = max(total_staked - out_on_loan, 0)

    metrics_data = {
        "total_staked": total_staked,
        "total_repaid": total_repaid,
        "out_on_loan": out_on_loan,
        "current_pool": current_pool
    }

    # 2. MASTER USER TABLE (With Repayment Column)
    master_query = db.query(
        models.User.id,
        models.User.full_name,
        models.User.income,
        models.User.credit_score,
        # Total Borrowed (Historical: Approved + Repaid)
        func.sum(case((models.Transaction.status.in_(["Approved", "Repaid"]), models.Transaction.amount), else_=0)).label("total_borrowed"),
        # Total Repaid (Only Repaid)
        func.sum(case((models.Transaction.status == "Repaid", models.Transaction.amount), else_=0)).label("total_repaid"),
        # Total Lent (Liquidity Added)
        func.sum(case((models.Transaction.status == "Liquidity Added", models.Transaction.amount), else_=0)).label("total_lent")
    ).outerjoin(models.Transaction).group_by(models.User.id).all()

    user_list = []
    for r in master_query:
        user_list.append({
            "id": r.id,
            "name": r.full_name,
            "income": r.income,
            "score": r.credit_score,
            "borrowed": float(r.total_borrowed),
            "repaid": float(r.total_repaid),
            "lent": float(r.total_lent)
        })

    # 3. RETURN COMBINED DATA
    return {
        "metrics": metrics_data,
        "users": user_list
    }

@app.get("/admin/archived", dependencies=[Depends(validate_admin)])
def get_archived(db: Session = Depends(get_db)):
    return db.query(models.Transaction).filter(models.Transaction.status == "Archived").all()

@app.post("/admin/verify")
def verify_admin_password(password_data: dict, settings=Depends(get_settings)):
    """Backend-only check: Keep the secret .env keys safe on the server"""
    provided_password = password_data.get("password")
    
    if provided_password == settings.admin_password:
        return {"verified": True}
    return {"verified": False}