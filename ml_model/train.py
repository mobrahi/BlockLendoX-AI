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

data = {
    'income': np.random.randint(20000, 200000, n_rows),
    'debt': np.random.randint(0, 50000, n_rows),
    'credit_score': np.random.randint(300, 850, n_rows), # Changed Age to Score
    'repayment_history': np.random.choice([0, 1], n_rows, p=[0.1, 0.9])
}

df = pd.DataFrame(data)

# 2. Logic: Who gets approved?
# Rule: Debt/Income ratio < 0.4 AND Credit Score > 600
df['target'] = (
    ((df['debt'] / df['income']) < 0.40) & 
    (df['credit_score'] >= 600)
).astype(int)

# 3. Train Model
# Features: Income, Debt, Credit Score
X = df[['income', 'debt', 'credit_score']]
y = df['target']

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

# 4. Save
model_path = os.path.join(BASE_DIR, 'credit_model.joblib')
joblib.dump(model, model_path)
print(f"✅ Retrained model with Credit Score feature saved to: {model_path}")