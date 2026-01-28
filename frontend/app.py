import streamlit as st
import requests
import pandas as pd
import time
from web3 import Web3

# 1. Configuration & Setup
st.set_page_config(page_title="BlockLendoX-AI", layout="wide")

# 2. Caching: Fetch Data Efficiently
@st.cache_data(ttl=5)
def fetch_global_stats():
    try:
        # Use 127.0.0.1 to avoid Mac localhost timeout issues
        res = requests.get("http://127.0.0.1:8000/history", timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        return []
    return []

# 3. Sidebar - Status & Metrics
with st.sidebar:
    st.title("🏦 BlockLendoX-AI")
    
    # Simple Health Check
    try:
        if requests.get("http://127.0.0.1:8000/health", timeout=1).status_code == 200:
            st.success("● System Online")
        else:
            st.error("○ Backend Offline")
    except:
        st.error("○ Backend Offline")
        st.warning("Run: uvicorn backend.main:app")
    
    st.divider()
    st.info("System Version: v1.0.5 (Live DB)")

# 4. Main UI Header & Stats
st.title("BlockLendoX-AI 🚀")
st.markdown("### Decentralized Lending powered by Machine Learning")

# Fetch Data Globally (Runs once every 5s)
history_data = fetch_global_stats()
df = pd.DataFrame() # Initialize empty DF to prevent NameErrors later

if history_data:
    df = pd.DataFrame(history_data)
    
    # Calculate Global Metrics
    if 'amount' in df.columns:
        total_volume = df['amount'].sum()
        total_loans = len(df)
        latest_loan = df.iloc[0]['amount'] if not df.empty else 0
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Volume", f"{total_volume:.4f} ETH")
        m2.metric("Active Loans", f"{total_loans}")
        m3.metric("Latest Loan", f"{latest_loan:.2f} ETH")
else:
    st.warning("Waiting for data... (If this persists, check Backend)")
    if st.button("Retry Connection"):
        st.cache_data.clear()
        st.rerun()

st.divider()

# 5. Tabs for Roles
tab_borrow, tab_lend = st.tabs(["🔹 Borrow Funds", "🔸 Provide Liquidity"])

# --- BORROWER TAB ---
with tab_borrow:
    st.header("Request an AI-Verified Loan")
    
    col1, col2 = st.columns(2)
    with col1:
        # Default values help speed up testing
        income = st.number_input("Monthly Income ($)", min_value=0, value=5000)
        debt = st.number_input("Monthly Debt ($)", min_value=0, value=1000)
    
    with col2:
        amount = st.slider("Loan Amount (ETH)", 0.1, 5.0, 0.5)
        wallet_input = st.text_input("Your Wallet Address (0x...)", placeholder="Enter Ganache address")

    # --- SUBMIT BUTTON LOGIC ---
    if st.button("Submit to AI Backend"):
        clean_wallet = wallet_input.strip()
        
        # Validation
        if not clean_wallet:
            st.warning("Please enter a wallet address.")
        elif not Web3.is_address(clean_wallet):
            st.error("Invalid Ethereum address format.")
        else:
            final_wallet = Web3.to_checksum_address(clean_wallet)
            
            payload = {
                "income": income,
                "debt": debt,
                "wallet": final_wallet,
                "amount": amount
            }

            # ... inside the submit button block ...
            with st.spinner("AI evaluating creditworthiness..."):
                try:
                    res = requests.post("http://127.0.0.1:8000/request-loan", json=payload)
                    
                    if res.status_code == 200:
                        result = res.json()
                        
                        # --- THE FIX IS HERE ---
                        # Check the actual logical status, not just HTTP 200
                        if result.get("status") == "Approved":
                            st.success(f"✅ Approved! Funds sent to {final_wallet[:10]}...")
                            st.write(f"**Transaction Hash:** `{result.get('transaction_hash')}`")
                            st.balloons()
                            st.cache_data.clear()
                        else:
                            # Handle "Rejected" gracefully
                            reason = result.get("reason", "Risk profile too high.")
                            st.error(f"❌ Loan Denied: {reason}")
                            st.info("Tip: Try increasing income or reducing current debt.")
                        # -----------------------

                    else:
                        st.error(f"Server Error: {res.status_code}")
                        
                except Exception as e:
                    st.error(f"Connection Error: {e}")

    # --- HISTORY & REPAYMENT SECTION ---
    st.divider()
    st.subheader("📜 Transaction History")
    
    if not df.empty:
        # 1. Display Table (Visual Copy only)
        display_cols = ['timestamp', 'wallet_address', 'amount', 'status', 'tx_hash']
        valid_cols = [c for c in display_cols if c in df.columns]
        st.dataframe(df[valid_cols], width="stretch", hide_index=True)
        
        # 2. Repayment Console
        st.divider()
        st.subheader("💸 Repayment Console")
        
        # Check if we have the necessary columns for logic
        if 'status' in df.columns and 'id' in df.columns:
            # Filter for active loans
            active_loans = df[df['status'] == "Approved"]
            
            if not active_loans.empty:
                # Create dropdown string
                loan_options = active_loans.apply(
                    lambda x: f"ID: {x['id']} | {x['amount']} ETH | {x['timestamp']}", axis=1
                )
                selected_loan_str = st.selectbox("Select Loan to Repay", loan_options)
                
                if st.button("Mark as Repaid"):
                    # Extract ID safely
                    loan_id = int(selected_loan_str.split("|")[0].replace("ID:", "").strip())
                    
                    try:
                        res = requests.put(f"http://127.0.0.1:8000/transaction/{loan_id}", json={"status": "Repaid"})
                        if res.status_code == 200:
                            st.success("Repayment Successful!")
                            st.balloons()
                            time.sleep(1.5)
                            st.cache_data.clear() # Clear cache to update UI
                            st.rerun()
                        else:
                            st.error("Update failed.")
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.info("No active loans to repay. You are debt-free! 🎉")
        else:
            st.warning("Data missing required columns.")
    else:
        st.info("No transactions found yet.")

# --- LENDER TAB ---
with tab_lend:
    st.header("Lender Dashboard")
    st.write("Deposit ETH to provide liquidity and earn interest.")
    st.info("Coming soon in Phase 2!")