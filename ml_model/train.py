import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

# Setup Path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. Generate Synthetic Data
np.random.seed(42)
n_rows = 5000

# ml_model/train.py logic update
data = {
    'income': np.random.randint(2000, 15000, n_rows), # Monthly
    'debt': np.random.randint(0, 5000, n_rows),
    'loan_amount': np.random.randint(100, 20000, n_rows), # Added feature
    'credit_score': np.random.randint(300, 850, n_rows)
}
df = pd.DataFrame(data)

# Improved Logic: Deny if (Debt + Loan_Amount)/Income is too high
df['target'] = (
    ((df['debt'] + (df['loan_amount'] / 12)) / df['income'] < 0.45) & # Pro-forma DTI
    (df['credit_score'] >= 600)
).astype(int)

# 3. Train Model
# Features: Income, Debt, Credit Score
X = df[['income', 'debt', 'loan_amount', 'credit_score']]
y = df['target']

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

# 4. Save
model_path = os.path.join(BASE_DIR, 'credit_model.joblib')
joblib.dump(model, model_path)
print(f"✅ Retrained model with Credit Score feature saved to: {model_path}")