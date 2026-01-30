
---

# 🏦 BlockLendoX-AI 🚀
> **AI-Powered Decentralized Micro-Lending Protocol**

BlockLendoX-AI is a next-generation FinTech application that bridges the gap between traditional credit assessment and Decentralized Finance (DeFi). By leveraging **Machine Learning** for risk analysis and **Ethereum Smart Contracts** for automated fund disbursement, it creates a trustless lending ecosystem.

---

## 📺 Project Overview
Traditional lending relies on slow, centralized bureaus. BlockLendoX-AI automates this by:
1.  **AI Gatekeeping:** A Random Forest model analyzes income-to-debt ratios and historical scores to approve or deny loans in milliseconds.
2.  **Blockchain Execution:** Approved loans are instantly signed and broadcasted to a local Ethereum network (Ganache) via Web3.py.
3.  **Persistence Layer:** All transactions are indexed in a SQLite database via SQLAlchemy for high-speed retrieval and auditing.
4.  **Intelligence Dashboard:** Real-time metrics and interactive Plotly visualizations provide protocol-wide financial transparency. 
5.  **Decoupled Architecture**: Security and Scalability. By centralizing blockchain keys and AI logic within a FastAPI backend, the protocol establishes a secure "single source of truth" that ensures future-proof scalability across any frontend platform.
6.  **Tiered Onboarding Strategy**: By decoupling static Identity (income) from live Behavior (debt exposure), our Dynamic Credit Scoring generates real-time risk profiles that outperform traditional static reporting for micro-lending.

---

## 🛠️ Tech Stack
| Layer | Technology |
| :--- | :--- |
| **Frontend** | Streamlit (Python) |
| **Backend** | FastAPI (Asynchronous API) |
| **Blockchain** | Web3.py, Ganache (Ethereum Testnet), Solidity |
| **AI/ML** | Scikit-Learn (Random Forest), Pandas, Joblib |
| **Database** | SQLite, SQLAlchemy (Relational Mapping) |
| **Security** | Pydantic-Settings (.env validation), API-Key Headers |

---

## ✨ Key Features

### 🔹 Borrower Portal
*   **Identity-Linked Requests:** Users must have a registered Profile ID to apply.
*   **AI Credit Assessment:** The system automatically fetches user income from the DB to prevent application fraud.
*   **Interactive Repayment Console:** Collapsible interface to manage and repay active loans with real-time status updates.

### 🔸 Lender Dashboard
*   **Liquidity Staking:** Users can provide ETH to the protocol pool to earn interest.
*   **Real-Time Pool Metrics:** Directly fetches Account(0) balance from the blockchain to show available capital.

### 📊 Protocol Analytics
*   **Capital Allocation:** Interactive Donut charts showing "In Pool" vs "Out on Loan" ratios.
*   **Financial Leaderboards:** Horizontal bar charts identifying top Liquidity Providers and Borrowers.
*   **Master Directory:** A comprehensive audit table of every user's income, credit score, and net debt.

### 🔐 Security & Admin Portal
*   **Password Protected:** Sensitive protocol logs are locked behind an API-verified security gate.
*   **Soft-Delete Audit Trail:** Deleted transactions are "Archived" rather than erased, ensuring a permanent financial history.
*   **Data Restoration:** Admins can "Restore" archived loans back to the active ledger with one click.

---

## ⚙️ Installation & Setup

### 1. Prerequisite: Start the Blockchain
In a separate terminal, run a deterministic Ganache instance:
```bash
npx ganache --port 8545 --deterministic
```

### 2. Backend Configuration
Create a `.env` file in the `backend/` folder:
```ini
RPC_URL=http://127.0.0.1:8545
PRIVATE_KEY=0x... # Private Key from Ganache Account (0)
CHAIN_ID=1337
ADMIN_PASSWORD=******
```

### 3. Install & Run
```bash
# Install dependencies
pip install -r requirements.txt

# Run Backend
uvicorn backend.main:app --reload

# Run Frontend
streamlit run frontend/app.py
```

---

## 🧠 Design Decisions & "War Stories"
*   **BOM Character Sanitization:** Handled the "Invisible Character" bug (`\ufeff`) that often occurs when copy-pasting Ethereum addresses from terminals.
*   **The "Cold Start" Credit Logic:** Developed a "Starter Score" logic to onboard new users, combined with a "Credit Builder" engine that boosts scores by 25 points upon every successful repayment.
*   **Soft vs Hard Delete:** Implemented a non-destructive deletion system to maintain data integrity for financial reporting.
*   **Decoupled Architecture:** Used a separate FastAPI backend to ensure that private keys and ML models stay off-chain and protected from the client-side.

---

## 🎓 Author
**Mohd Ibrahim**  
*Built for Python Bootcamp JomHack C4 Capstone Project - Jan 2026*

---