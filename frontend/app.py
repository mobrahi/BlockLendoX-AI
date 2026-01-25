import streamlit as st
import requests
from web3 import Web3

# 1. Configuration & Setup
st.set_page_config(page_title="BlockLendoX-AI", layout="wide")

def check_backend():
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        return response.status_code == 200
    except:
        return False

# 2. Sidebar - Status & Metrics
with st.sidebar:
    st.title("🏦 BlockLendoX-AI")
    
    if check_backend():
        st.success("● System Online")
    else:
        st.error("○ Backend Offline")
        st.warning("Run: uvicorn backend.main:app")
    
    st.divider()
    st.metric(label="Total Pool Liquidity", value="15.5 ETH", delta="2.1 ETH")
    st.divider()
    st.info("System Version: v1.0.2 (AI-Enabled)")

# 3. Main UI Header
st.title("BlockLendoX-AI 🚀")
st.markdown("### Decentralized Lending powered by Machine Learning")

# 4. Create Single Set of Tabs
tab_borrow, tab_lend = st.tabs(["🔹 Borrow Funds", "🔸 Provide Liquidity"])

# --- BORROWER TAB ---
with tab_borrow:
    st.header("Request an AI-Verified Loan")
    
    col1, col2 = st.columns(2)
    with col1:
        u_id = st.number_input("User ID", min_value=1, value=101)
        income = st.number_input("Monthly Income ($)", min_value=0, value=5000)
        debt = st.number_input("Monthly Debt ($)", min_value=0, value=1000)
    
    with col2:
        amount = st.slider("Loan Amount (ETH)", 0.1, 5.0, 0.5)
        wallet_input = st.text_input("Your Wallet Address (0x...)", placeholder="Enter Ganache address")

    if st.button("Submit to AI Backend"):
        clean_wallet = wallet_input.strip()
        
        # Sequential Validation
        if not clean_wallet:
            st.warning("Please enter a wallet address.")
        elif not Web3.is_address(clean_wallet):
            st.error("Invalid Ethereum address format or checksum.")
        else:
            final_wallet = Web3.to_checksum_address(clean_wallet)
            
            # Prepare payload to match your FastAPI Pydantic model
            payload = {
                "income": income,
                "debt": debt,
                "wallet": final_wallet,
                "amount": amount
            }

            with st.spinner("AI evaluating creditworthiness..."):
                try:
                    res = requests.post("http://localhost:8000/request-loan", json=payload)

                    if res.text:
                        result = res.json()
                    
                    else:
                        result = {}
                    
                    # MOVED INSIDE: This only runs if the button was clicked
                    if res.status_code == 200:
                        tx_hash = result.get('transaction_hash', '0xPending...')
                        st.success(f"✅ Approved! Funds sent to {final_wallet[:10]}...")
                        st.write(f"**Transaction Hash:** `{tx_hash}`")
                        st.balloons()
                    else:
                        st.error(f"❌ Error: {result.get('detail', 'Unknown Error')}")
                
                except Exception as e:
                    st.error(f"Connection Error: {e}")

# --- LENDER TAB ---
with tab_lend:
    st.header("Lender Dashboard")
    st.write("Deposit ETH to provide liquidity and earn interest.")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Add Funds")
        deposit_amt = st.number_input("Amount to Deposit (ETH)", min_value=0.1)
        if st.button("Confirm Deposit"):
            # This is where we will eventually call /deposit
            st.info(f"Initiating deposit of {deposit_amt} ETH...")
            st.warning("Blockchain bridge for deposits coming in next update!")

    with c2:
        st.subheader("Your Stats")
        st.metric("Your Earnings", "0.045 ETH", "+0.002")
        if st.button("Withdraw Liquidity"):
            st.info("Processing withdrawal request...")

            if res.status_code == 200:
                # Use .get() to avoid KeyErrors and check if result exists
                tx_hash = result.get('transaction_hash', 'Pending...')
                st.success(f"✅ Approved! Funds sent to {final_wallet[:10]}...")
                st.write(f"**Transaction Hash:** `{tx_hash}`")
                st.balloons()