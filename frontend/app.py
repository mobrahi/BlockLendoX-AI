import streamlit as st
import requests

st.set_page_config(page_title="BlockLendoX-AI", layout="wide")

def check_backend():
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            return True
    except:
        return False

with st.sidebar:
    st.title("🏦 BlockLendoX-AI")
    
    # Connection Status Indicator
    if check_backend():
        st.success("● System Online")
    else:
        st.error("○ Backend Offline")
        st.warning("Please run: uvicorn backend.main:app")
    
    st.divider()

# Sidebar for Global Metrics
with st.sidebar:
    st.title("🏦 BlockLendoX-AI")
    st.metric(label="Total Pool Liquidity", value="15.5 ETH", delta="2.1 ETH")
    st.divider()
    st.info("Connected Wallet: 0x71C...3902")

# Create Tabs for Roles
tab_borrow, tab_lend = st.tabs(["🔹 Borrow Funds", "🔸 Provide Liquidity"])

# --- BORROWER TAB ---
with tab_borrow:
    st.header("Request an AI-Verified Loan")
    col1, col2 = st.columns(2)
    
    with col1:
        u_id = st.number_input("User ID", min_value=1, key="b_id")
        income = st.number_input("Monthly Income ($)", min_value=0)
        debt = st.number_input("Monthly Debt ($)", min_value=0)
        amount = st.slider("Loan Amount (ETH)", 0.1, 5.0, 0.5)
        
        if st.button("Submit to AI Backend"):
            with st.spinner("AI analyzing credit risk..."):
                # Call FastAPI backend
                res = requests.post("http://localhost:8000/request-loan", 
                                    json={"user_id": u_id, "income": income, "debt": debt, "requested_amount": amount})
                if res.status_code == 200:
                    st.success(f"Approved! TX: {res.json()['transaction_hash']}")
                    st.balloons()
                else:
                    st.error(f"Denied: {res.json()['detail']}")

# --- LENDER TAB ---
with tab_lend:
    st.header("Lender Dashboard")
    st.write("Deposit ETH to provide liquidity and earn 10% interest on repaid loans.")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Add Funds")
        deposit_amt = st.number_input("Amount to Deposit (ETH)", min_value=0.1)
        if st.button("Confirm Deposit"):
            st.warning("Ensure your wallet (Metamask/Ganache) is active.")
            # Logic here would call a FastAPI route that triggers depositLiquidity()
            st.success(f"Deposited {deposit_amt} ETH to the pool!")

    with c2:
        st.subheader("Your Stats")
        st.metric("Your Earnings", "0.045 ETH", "+0.002")
        if st.button("Withdraw Liquidity"):
            st.info("Processing withdrawal request...")