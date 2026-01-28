
---

# 🏦 BlockLendoX-AI
> **DeFi Micro-Lending Platform powered by Machine Learning**

BlockLendoX-AI bridges the gap between traditional credit scoring and decentralized finance. It uses an AI model to assess borrower risk off-chain and executes loan agreements on-chain via Ethereum Smart Contracts.

## 🚀 Key Features
- **AI Credit Scoring:** Random Forest model evaluates Income, Debt, and History to predict default risk.
- **Trustless Execution:** Approved loans automatically trigger ETH transfers via Web3.py.
- **Data Persistence:** SQLite database tracks all transaction history (CRUD).
- **Interactive Dashboard:** Streamlit UI with real-time metrics, caching, and repayment console.

## 🛠️ Tech Stack
- **Frontend:** Streamlit (Python)
- **Backend:** FastAPI, Pydantic, SQLAlchemy
- **Blockchain:** Web3.py, Ganache (Local Ethereum Testnet)
- **AI/ML:** Scikit-Learn, Pandas, Joblib
- **Database:** SQLite

---

## 📦 Installation & Setup

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/BlockLendoX-AI.git
cd BlockLendoX-AI

```


2. **Install Dependencies:**
```bash
pip install -r requirements.txt

```


3. **Environment Configuration:**
Create a `.env` file in the root directory:
```env
RPC_URL=http://127.0.0.1:8545
PRIVATE_KEY=your_private_key_here
CONTRACT_ADDRESS=0x...

```


4. **Run the Backend (FastAPI):**
```bash
uvicorn main:app --reload

```


5. **Run the Frontend (Streamlit):**
```bash
streamlit run app.py

```



---

## 🧠 The ML Logic

The model is trained on financial datasets to identify the probability of a "Default."

* **Input:** Income, Existing Debt, Requested Amount, Loan Duration.
* **Output:** Binary classification (Approve/Deny) and a confidence score.

---

## 📜 Smart Contract Summary

The `AILend.sol` contract ensures that:

1. Only the **Authorized AI Backend** can trigger loan approvals.
2. Funds are locked until the AI verifies creditworthiness.
3. Repayments are immutable and transparent on the ledger.

---

## 🧠 System Architecture
1. User submits loan request via Streamlit.
2. FastAPI receives data and sanitizes input.
3. AI Model (credit_model.joblib) predicts risk (0 or 1).
4. If Approved:
    * Web3.py signs a transaction to Ganache.
    * SQLAlchemy saves the record to fintech.db.
5. Frontend updates the dashboard metrics and transaction history.

---
*Built for Python Bootcamp JomHack C4 Capstone Project - Jan 2026*

### Final Tip for your Presentation:

When you present **BlockLendoX-AI**, make sure to show the "Chain of Command":

1. Show the **SQLite** record being created (**CRUD**).
2. Show the **AI Model** making a decision.
3. Show the **Blockchain Transaction** hash appearing in the UI.

This "Triple-Threat" (DB + AI + Web3) is exactly what bootcamp instructors look for.

**Is there anything else you need to refine before you start coding, like a specific list of ML features or a more complex SQL schema?**