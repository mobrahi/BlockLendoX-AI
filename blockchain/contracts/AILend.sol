// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract BlockLendoX {
    address public owner;
    uint256 public totalPoolBalance;

    struct Loan {
        uint256 amount;
        uint256 repaymentAmount;
        bool isActive;
        address borrower;
    }

    mapping(address => Loan) public loans;
    mapping(address => uint256) public lenderBalances;

    event LiquidityAdded(address lender, uint256 amount);
    event LiquidityWithdrawn(address lender, uint256 amount);
    event LoanDisbursed(address borrower, uint256 amount);

    constructor() {
        owner = msg.sender;
    }

    // --- LENDER FUNCTIONS ---

    // Anyone can deposit ETH to the pool to provide liquidity
    function depositLiquidity() public payable {
        require(msg.value > 0, "Must deposit more than 0");
        lenderBalances[msg.sender] += msg.value;
        totalPoolBalance += msg.value;
        emit LiquidityAdded(msg.sender, msg.value);
    }

    // Lenders can withdraw their unused liquidity
    function withdrawLiquidity(uint256 _amount) public {
        require(lenderBalances[msg.sender] >= _amount, "Insufficient lender balance");
        require(address(this).balance >= _amount, "Not enough liquid funds in contract");

        lenderBalances[msg.sender] -= _amount;
        totalPoolBalance -= _amount;
        payable(msg.sender).transfer(_amount);
        emit LiquidityWithdrawn(msg.sender, _amount);
    }

    // --- BORROWER FUNCTIONS (Triggered by AI Backend) ---

    modifier onlyAIBackend() {
        require(msg.sender == owner, "Only the AI Backend can approve loans");
        _;
    }

    function approveLoan(address _borrower, uint256 _amount) public onlyAIBackend {
        require(!loans[_borrower].isActive, "Active loan already exists");
        require(address(this).balance >= _amount, "Insufficient pool liquidity");

        // Calculate 10% interest
        uint256 interest = (_amount * 10) / 100;

        loans[_borrower] = Loan({
            amount: _amount,
            repaymentAmount: _amount + interest,
            isActive: true,
            borrower: _borrower
        });

        totalPoolBalance -= _amount;
        payable(_borrower).transfer(_amount);
        emit LoanDisbursed(_borrower, _amount);
    }

    function repayLoan() public payable {
        Loan storage loan = loans[msg.sender];
        require(loan.isActive, "No active loan to repay");
        require(msg.value >= loan.repaymentAmount, "Incorrect repayment amount");

        loan.isActive = false;
        totalPoolBalance += msg.value; // Interest stays in the pool for lenders
    }
}