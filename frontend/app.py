import streamlit as st
import requests
import pandas as pd
import time
import plotly.express as px
import matplotlib.pyplot as plt
from web3 import Web3

if 'admin_authenticated' not in st.session_state:
    st.session_state.admin_authenticated = False

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
tab_borrow, tab_lend, tab_stats, tab_admin = st.tabs(["🔹 Borrow", "🔸 Provide Liquidity", "📊 Analytics", "🔐 Admin"])

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
    with st.expander("📜 View Transaction History", expanded=False):
        if not df.empty:
            # Add a Refresh button
            if st.button("🔄 Refresh Data", key="refresh_hist"):
                st.cache_data.clear()
                st.rerun()
                
            # --- UPDATED LIST: Added 'id' at the beginning ---
            display_cols = ['id', 'timestamp', 'wallet_address', 'amount', 'status', 'tx_hash']
            valid_cols = [c for c in display_cols if c in df.columns]
            
            # Create a clean display version
            display_df = df[valid_cols].copy()
            
            # Rename for professional look
            display_df.rename(columns={'id': 'ID'}, inplace=True)
            
            # Display the table
            st.dataframe(display_df, width="stretch", hide_index=True)
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
        lender_user_id = st.number_input("Your User ID", min_value=1, value=1, key="lender_id")
        lender_wallet = st.text_input("Lender Wallet Address", placeholder="0x...", key="lend_wallet").strip()
        deposit_amount = st.number_input("Amount to Deposit (ETH)", min_value=0.1, key="lend_amount")
        
        if st.button("Confirm Deposit", type="primary"):
            if not Web3.is_address(lender_wallet):
                st.error("Invalid Wallet Address")
            else:
                payload = {
                    "user_id": lender_user_id,
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
    st.header("📊 Protocol Intelligence Dashboard")
    
    try:
        res = requests.get("http://localhost:8000/analytics/summary", timeout=5)
        if res.status_code == 200:
            data = res.json()
            m = data['metrics']
            users = data['users']
            u_df = pd.DataFrame(users)

            # --- ROW 1: METRICS ---
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            col_m1.metric("Available Pool", f"{m['current_pool']:.2f} ETH")
            col_m2.metric("Total Staked", f"{m['total_staked']:.2f} ETH")
            col_m3.metric("Out on Loan", f"{m['out_on_loan']:.2f} ETH")
            col_m4.metric("Total Repaid", f"{m['total_repaid']:.2f} ETH")

            st.divider()

            # --- ROW 2: CHARTS ---
            c1, c2 = st.columns(2)

            with c1:
                st.write("### 🏦 Capital Allocation")
                # Force chart to show even if values are small
                pie_data = pd.DataFrame({
                    'Status': ['In Pool', 'Active Loans'],
                    'Amount': [max(m['current_pool'], 0.001), max(m['out_on_loan'], 0.001)]
                })
                fig_pie = px.pie(pie_data, values='Amount', names='Status', hole=0.5,
                                color_discrete_sequence=['#00D4FF', '#FF4B4B'])
                st.plotly_chart(fig_pie, use_container_width=True)

            with c2:
                st.write("### 🏆 Borrower Activity")
                if not u_df.empty and u_df['borrowed'].sum() > 0:
                    fig_b = px.bar(u_df[u_df['borrowed'] > 0], x='borrowed', y='name', 
                                  orientation='h', color='borrowed', color_continuous_scale='Reds')
                    st.plotly_chart(fig_b, use_container_width=True)
                else:
                    st.info("No borrowing activity recorded.")

            st.divider()

            # --- ROW 3: MASTER USER TABLE ---
            st.write("### 👥 Master User Directory & Financial Summary")
            if not u_df.empty:
                # Rename columns for professional display
                display_df = u_df.rename(columns={
                    "id": "User ID",
                    "name": "Full Name",
                    "income": "Annual Income",
                    "score": "Credit Score",
                    "borrowed": "Total Borrowed (ETH)",
                    "lent": "Total Lent (ETH)"
                })
                st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.info("No users registered in the system.")

            # --- ROW 4: LENDER CHART ---
            if not u_df.empty and u_df['lent'].sum() > 0:
                st.divider()
                st.write("### 💰 Liquidity Provider Rankings")
                fig_l = px.bar(u_df[u_df['lent'] > 0], x='lent', y='name', 
                              orientation='h', color='lent', color_continuous_scale='Greens')
                st.plotly_chart(fig_l, use_container_width=True)

        else:
            st.error("Backend Error: Could not load summary.")
    except Exception as e:
        st.error(f"UI Error: {e}")

# --- ADMIN PORTAL TAB ---
with tab_admin:
    st.header("🔐 Security & Audit Portal")

    # 1. CHECK IF NOT LOGGED IN
    if not st.session_state.get('admin_authenticated', False):
        st.info("Please authenticate to view sensitive protocol logs.")
        admin_password_input = st.text_input("Enter Admin Credentials", type="password", key="admin_pass_login")
        
        if st.button("Unlock Portal"):
            try:
                verify_res = requests.post(
                    "http://127.0.0.1:8000/admin/verify", 
                    json={"password": admin_password_input}
                )
                
                if verify_res.status_code == 200 and verify_res.json().get("verified"):
                    st.session_state.admin_authenticated = True
                    # --- SAVE THE PASSWORD FOR LATER USE ---
                    st.session_state.admin_password_cache = admin_password_input
                    st.success("Access Granted!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Invalid Admin Password")
            except Exception as e:
                st.error(f"Backend Offline: {e}")

    # 2. IF LOGGED IN (Show the Dashboard)
    else:
        st.success("Admin Session Active")
        
        # Logout Button at the top
        if st.button("🔒 Lock Portal & Logout"):
            st.session_state.admin_authenticated = False
            # --- WIPE THE CACHE ---
            st.session_state.admin_password_cache = None
            st.rerun()

        st.divider()
        st.subheader("🗑️ Archived Transactions (Audit Trail)")
        st.write("Below are records marked as 'Archived'. These are excluded from standard analytics.")

        # --- DATA FETCHING (Only runs if authenticated) ---
        headers = {"X-Admin-Password": st.session_state.get('admin_password_cache')}

        try:
            archived_res = requests.get(
                "http://127.0.0.1:8000/admin/archived",
                headers=headers
            )
            
            if archived_res.status_code == 200:
                archived_data = archived_res.json()
                
                if archived_data:
                    # Convert to DataFrame
                    a_df = pd.DataFrame(archived_data)
                    
                    # Rename columns for clarity
                    a_df.rename(columns={'id': 'Loan ID', 'wallet_address': 'Wallet', 'amount': 'Amount (ETH)'}, inplace=True)
                    
                    # Display Table
                    st.dataframe(a_df[['Loan ID', 'timestamp', 'Wallet', 'Amount (ETH)', 'status']], width="stretch", hide_index=True)

                    # --- RESTORE TOOL ---
                    st.divider()
                    st.subheader("🛠️ Administrative Tools")
                    restore_id = st.number_input("Enter Loan ID to Restore", min_value=1, step=1)
                    
                    if st.button("✅ Restore Transaction to Active Ledger", type="primary"):
                        restore_res = requests.put(
                            f"http://127.0.0.1:8000/transaction/{restore_id}", 
                            json={"status": "Approved"}
                        )
                        if restore_res.status_code == 200:
                            st.success(f"Transaction #{restore_id} has been restored!")
                            st.balloons()
                            time.sleep(1)
                            st.cache_data.clear() # Clear cache so history updates
                            st.rerun()
                        else:
                            st.error("Restore failed. Verify the Loan ID.")
                else:
                    st.info("No archived records found in the database.")
        except Exception as e:
            st.error(f"Error fetching archive: {e}")