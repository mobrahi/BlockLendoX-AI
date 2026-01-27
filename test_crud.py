import requests
import time

BASE_URL = "http://127.0.0.1:8000"

# Use one of your Ganache addresses here
TEST_WALLET = "0x860122c813aCC08faf4b41F9774378c92F98e56C"

def run_tests():
    print("🚀 Starting CRUD System Check...\n")

    # --- 1. READ (Initial Count) ---
    print("🔹 Testing READ (History)...")
    res = requests.get(f"{BASE_URL}/history")
    initial_count = len(res.json())
    print(f"   Current Record Count: {initial_count}")

    # --- 2. CREATE (Request Loan) ---
    print("\n🔹 Testing CREATE (Request Loan)...")
    payload = {
        "income": 128000,
        "debt": 5000,
        "wallet": TEST_WALLET,
        "amount": 0.3
    }
    res = requests.post(f"{BASE_URL}/request-loan", json=payload)
    if res.status_code == 200:
        print("   ✅ Loan Approved & Created")
    else:
        print(f"   ❌ Failed: {res.text}")
        return # Stop test if create fails

    # Verify it was added to DB
    res = requests.get(f"{BASE_URL}/history")
    new_data = res.json()
    if len(new_data) > initial_count:
        new_tx = new_data[0] # Assuming ordered by Descending
        tx_id = new_tx['id']
        print(f"   ✅ Verified in DB (ID: {tx_id})")
    else:
        print("   ❌ Error: Record not found in history")
        return

    # --- 3. UPDATE (Repay Loan) ---
    print(f"\n🔹 Testing UPDATE (Mark ID {tx_id} as Repaid)...")
    res = requests.put(f"{BASE_URL}/transaction/{tx_id}", json={"status": "Repaid"})
    if res.status_code == 200 and res.json()['status'] == "Repaid":
        print("   ✅ Status Updated to 'Repaid'")
    else:
        print(f"   ❌ Update Failed: {res.text}")

    # --- 4. DELETE (Clean up) ---
    print(f"\n🔹 Testing DELETE (Remove ID {tx_id})...")
    res = requests.delete(f"{BASE_URL}/transaction/{tx_id}")
    if res.status_code == 200:
        print("   ✅ Record Deleted")
    else:
        print(f"   ❌ Delete Failed: {res.text}")

    # --- FINAL CHECK ---
    print("\n🔹 Final Verification...")
    res = requests.get(f"{BASE_URL}/history")
    final_count = len(res.json())
    
    if final_count == initial_count:
        print("🎉 TEST PASSED: Database cleanly returned to original state.")
    else:
        print("⚠️ TEST FINISHED: But record count mismatch.")

if __name__ == "__main__":
    try:
        run_tests()
    except Exception as e:
        print(f"❌ Connection Error: Is FastAPI running? ({e})") 