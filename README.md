
---

# 🏦 BlockLendoX-AI

**AI-Powered Decentralized Micro-Lending Platform**

BlockLendoX-AI is a next-generation FinTech application that bridges the gap between traditional credit scoring and decentralized finance (DeFi). By leveraging **Machine Learning** for risk assessment and **Ethereum Smart Contracts** for automated fund disbursement, it provides a trustless lending ecosystem.

---

## 🚀 Features

* **AI-Driven Credit Scoring:** Uses a Random Forest model to analyze income, debt, and behavioral data to predict default risk.
* **Smart Contract Escrow:** Automated loan disbursement and repayment tracking via Solidity.
* **Off-Chain CRUD Management:** SQLite database manages user profiles and KYC data for fast retrieval and compliance.
* **Real-time Dashboard:** Streamlit interface for seamless user interaction and transaction monitoring.

## 🛠️ Tech Stack

| Component | Technology |
| --- | --- |
| **Frontend** | Streamlit |
| **Backend** | FastAPI |
| **AI/ML** | Scikit-Learn, Joblib |
| **Blockchain** | Solidity, Web3.py, Ganache (Local Testnet) |
| **Database** | SQLite, SQLAlchemy (CRUD operations) |

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
RPC_URL=http://127.0.0.1:7545
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

### Final Tip for your Presentation:

When you present **BlockLendoX-AI**, make sure to show the "Chain of Command":

1. Show the **SQLite** record being created (**CRUD**).
2. Show the **AI Model** making a decision.
3. Show the **Blockchain Transaction** hash appearing in the UI.

This "Triple-Threat" (DB + AI + Web3) is exactly what bootcamp instructors look for.

**Is there anything else you need to refine before you start coding, like a specific list of ML features or a more complex SQL schema?**