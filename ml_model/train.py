import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

# Get the directory where train.py actually lives
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. Generate 1000 rows of fake financial data
np.random.seed(42)
n_rows = 1000

data = {
    'income': np.random.randint(20000, 150000, n_rows),
    'debt': np.random.randint(0, 50000, n_rows),
    'age': np.random.randint(18, 70, n_rows),
    'repayment_history': np.random.choice([0, 1], n_rows, p=[0.2, 0.8]) # 1 = good history
}

df = pd.DataFrame(data)

# 2. Logic: Default if Debt is > 40% of Income OR bad history
# 1 = Approved (Safe), 0 = Denied (Risky)
df['target'] = ((df['debt'] / df['income'] < 0.4) & (df['repayment_history'] == 1)).astype(int)

# 3. Train a quick Random Forest
X = df[['income', 'debt', 'age']]
y = df['target']

model = RandomForestClassifier(n_estimators=100)
model.fit(X, y)

# 4. Save the model for FastAPI to use
joblib.dump(model, 'credit_model.joblib')
df.to_csv('dataset.csv', index=False)

print("✅ Model trained and dataset.csv created in ml_model/ folder!")

# Define the exact paths inside the ml_model folder
model_path = os.path.join(BASE_DIR, 'credit_model.joblib')
dataset_path = os.path.join(BASE_DIR, 'dataset.csv')

# Save them using absolute paths
joblib.dump(model, model_path)
df.to_csv(dataset_path, index=False)

print(f"✅ Success! Files saved in: {BASE_DIR}")