import streamlit as st
import requests
import pandas as pd
import time
import plotly.express as px
import matplotlib.pyplot as plt
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
tab_borrow, tab_lend, tab_stats = st.tabs(["🔹 Borrow Funds", "🔸 Provide Liquidity", "📈 Analytics"])

# --- BORROWER TAB ---
with tab_borrow:
    st.header("Request an AI-Verified Loan")
    
    col1, col2 = st.columns(2)
    with col1:
        user_id_input = st.number_input("Enter Your User ID", min_value=1, value=1)
        # 💡 PRO TIP: You can remove the income input entirely!
        # The backend will look it up automatically.
        debt = st.number_input("Current Monthly Debt ($)", min_value=0, value=1000)
    
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
                "user_id": user_id_input, # Send the ID
                "income": 0, # We can send 0 because the backend will ignore it!
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

    # --- IMPROVED HISTORY & REPAYMENT UI ---
    st.divider()
    
    # 1. Transaction History (Collapsible)
    # expanded=False means it starts closed (cleaner look)
    with st.expander("📜 View Transaction History", expanded=False):
        if not df.empty:
            # Add a Refresh button inside the dropdown
            if st.button("🔄 Refresh Data", key="refresh_hist"):
                st.cache_data.clear()
                st.rerun()
                
            display_cols = ['timestamp', 'wallet_address', 'amount', 'status', 'tx_hash']
            valid_cols = [c for c in display_cols if c in df.columns]
            
            # Use the new width parameter
            st.dataframe(df[valid_cols], width="stretch", hide_index=True)
        else:
            st.info("No transactions found yet.")

    # 2. Repayment Console (Collapsible)
    with st.expander("💸 Open Repayment Console", expanded=False):
        if not df.empty and 'status' in df.columns and 'id' in df.columns:
            # Filter for active loans
            active_loans = df[df['status'] == "Approved"]
            
            if not active_loans.empty:
                st.write("Select a loan to pay back:")
                
                # Create dropdown string
                loan_options = active_loans.apply(
                    lambda x: f"ID: {x['id']} | {x['amount']} ETH | {x['timestamp']}", axis=1
                )
                selected_loan_str = st.selectbox("Active Loans", loan_options, label_visibility="collapsed")
                
                # Extract ID safely
                if selected_loan_str:
                    loan_id = int(selected_loan_str.split("|")[0].replace("ID:", "").strip())
                    
                    # 'type="primary"' turns the button RED/THEME COLOR (makes it pop!)
                    if st.button(f"Mark Loan #{loan_id} as Repaid", type="primary"):
                        try:
                            res = requests.put(f"http://127.0.0.1:8000/transaction/{loan_id}", json={"status": "Repaid"})
                            if res.status_code == 200:
                                st.success("Repayment Successful!")
                                st.balloons()
                                time.sleep(1.5) # Wait for animation
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error("Update failed.")
                        except Exception as e:
                            st.error(f"Error: {e}")
            else:
                st.success("🎉 You have no active loans to repay!")
        else:
            st.warning("Data missing required columns.")

# --- LENDER TAB ---
with tab_lend:
    st.header("Lender Dashboard")
    st.markdown("Provide liquidity to the protocol and earn passive APY.")
    
    # 1. FETCH REAL POOL DATA
    pool_balance = 0.0
    pool_address = "Loading..."
    
    try:
        # Call the new endpoint
        pool_res = requests.get("http://127.0.0.1:8000/pool-balance", timeout=2)
        if pool_res.status_code == 200:
            pool_data = pool_res.json()
            pool_balance = pool_data.get("balance", 0.0)
            pool_address = pool_data.get("admin_address", "Unknown")
    except:
        pass

    # 2. METRICS ROW
    l_col1, l_col2, l_col3 = st.columns(3)
    l_col1.metric("Total Pool Liquidity", f"{pool_balance:.4f} ETH")
    l_col2.metric("Current APY", "12.5%", "+0.5%")
    l_col3.metric("Total Lenders", "4") # Mock or fetch from DB count

    st.divider()

    # 3. DEPOSIT INTERFACE
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("💰 Add Liquidity")
        lender_wallet = st.text_input("Lender Wallet Address", placeholder="0x...", key="lend_wallet").strip()
        deposit_amount = st.number_input("Amount to Deposit (ETH)", min_value=0.1, key="lend_amount")
        
        if st.button("Confirm Deposit", type="primary"):
            if not Web3.is_address(lender_wallet):
                st.error("Invalid Wallet Address")
            else:
                payload = {
                    "wallet": Web3.to_checksum_address(lender_wallet),
                    "amount": deposit_amount
                }
                
                try:
                    res = requests.post("http://127.0.0.1:8000/deposit", json=payload)
                    if res.status_code == 200:
                        st.success(f"Successfully staked {deposit_amount} ETH!")
                        st.balloons()
                        time.sleep(1)
                        st.cache_data.clear() # Refresh stats
                        st.rerun()
                    else:
                        st.error("Deposit failed.")
                except Exception as e:
                    st.error(f"Error: {e}")

    with c2:
        st.subheader("📊 Your Staking History")
        # Filter dataframe for "Liquidity Added" status
        if not df.empty and 'status' in df.columns:
            deposits = df[df['status'] == "Liquidity Added"]
            if not deposits.empty:
                st.dataframe(deposits[['timestamp', 'amount', 'wallet_address']], width="stretch", hide_index=True)
            else:
                st.info("No active deposits found.")
        else:
            st.info("Connect wallet to view history.")

# --- ANALYTICS TAB (UPGRADED WITH PLOTLY) ---
with tab_stats:
    st.header("Protocol Analytics Dashboard")
    
    res = requests.get("http://localhost:8000/analytics/summary")
    if res.status_code == 200:
        data = res.json()
        
        # --- 1. Top Level Metrics ---
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Loaned", f"{data['protocol_total_loaned']:.2f} ETH")
        m2.metric("Total Repaid", f"{data['protocol_total_repaid']:.2f} ETH")
        
        # Calculate "Money in Flight"
        outstanding = data['protocol_total_loaned'] - data['protocol_total_repaid']
        m3.metric("Outstanding Debt", f"{outstanding:.2f} ETH", delta_color="inverse")

        st.divider()

        col1, col2 = st.columns(2)

        # --- 2. Chart: Loan vs Repayment (Interactive Pie Chart) ---
        with col1:
            st.write("### 🍰 Capital Distribution")
            pie_df = pd.DataFrame({
                'Status': ['Loaned (Out)', 'Repaid (In)'],
                'Amount': [data['protocol_total_loaned'], data['protocol_total_repaid']]
            })
            
            # Using Plotly Express for a clean donut chart
            fig_pie = px.pie(
                pie_df, 
                values='Amount', 
                names='Status', 
                hole=0.4,
                color_discrete_sequence=['#FF4B4B', '#00D4FF'] # Red for out, Blue for in
            )
            fig_pie.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_pie, use_container_width=True)

        # --- 3. Chart: User Borrowing (Horizontal Bar Chart) ---
        with col2:
            st.write("### 🏆 Top Borrowers")
            if data['user_breakdown']:
                user_df = pd.DataFrame(data['user_breakdown'])
                
                # Plotly Horizontal Bar
                fig_bar = px.bar(
                    user_df, 
                    x='borrowed', 
                    y='name', 
                    orientation='h',
                    labels={'borrowed': 'Total Borrowed (ETH)', 'name': 'Borrower Name'},
                    color='borrowed',
                    color_continuous_scale='Blues'
                )
                fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(t=0, b=0, l=0, r=0))
                st.plotly_chart(fig_bar, use_container_width=True)

        st.divider()

        # --- 4. User Summary Table (The "Leaderboard") ---
        st.write("### 👥 Borrower Detailed Leaderboard")
        if data['user_breakdown']:
            summary_df = pd.DataFrame(data['user_breakdown'])
            summary_df.columns = ["Borrower Name", "User ID", "Total Borrowed (ETH)", "No. of Loans"]
            
            # Style the table to highlight high borrowers
            st.dataframe(
                summary_df.style.background_gradient(subset=["Total Borrowed (ETH)"], cmap="Blues"),
                use_container_width=True
            )
        else:
            st.info("No active loan data to display.")
    else:
        st.error("Could not fetch analytics.")