from web3 import Web3

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

def check():
    if not w3.is_connected():
        print("❌ Not connected to Ganache!")
        return

    print(f"{'Index':<6} | {'Address':<44} | {'Balance (ETH)':<15}")
    print("-" * 70)
    
    for i in range(5): # Check first 5 accounts
        addr = w3.eth.accounts[i]
        balance_wei = w3.eth.get_balance(addr)
        balance_eth = w3.from_wei(balance_wei, 'ether')
        print(f"{i:<6} | {addr:<44} | {balance_eth:<15.4f}")

if __name__ == "__main__":
    check()