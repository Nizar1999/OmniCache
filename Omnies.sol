pragma solidity ^0.6.6;

contract Bank {
    
    using SafeMath for uint256;
    
    uint constant waitPeriod = 20;        //The wait period for payments
    uint constant enrollPayment = 5000;   //The initial amount of Omnies to pay on enrollment
    uint constant dataRate = 10;          //The price of 1 Chunk
    uint constant fileCost = 1;           //The cost of uploading a single chunk
    uint constant chunkSize = 3704;       //The size of a single chunk
    
    
    mapping(address => uint256) balances;   //Balances of addresses
    mapping(address => bool) isEnrolled;    //Is address already enrolled
    mapping(address => uint) lastPaid;      //Last time an account was paid
    
    address public owner;   //Owner of the smart contract
    uint256 totalSupply_;   //Total supply of Omnies
    
    
    // Events
    event logFile(address indexed accountAddress, uint linkToOGF, string fileName, string fileHash, uint totalSize);
    event logChunk(address indexed accountAddress, uint indexed linkToOGF, uint senderGUID, uint indexed receiverGUID, string chunkHash, uint chunkNb);
    event logDeletion(address indexed accountAddress, uint indexed linkToOGF);
    
    // @notice Create the bank with an initial amount of Omnies
    constructor(uint256 total) public {
        totalSupply_ = total;
        balances[msg.sender] = totalSupply_;
        owner = msg.sender;
    }


    // @notice Enroll a customer with the bank, giving them an initial amount of Omnies
    // @return The balance of the user after enrolling
    function enroll() public returns (uint256) {
        require(isEnrolled[msg.sender] == false);
        balances[msg.sender] = enrollPayment;
        lastPaid[msg.sender] = now;
        isEnrolled[msg.sender] = true;
        return balances[msg.sender];
    }

    // @notice Get paid
    // @return Balance after the deposit is made
    function giveOmnies(uint sizeData) public returns (uint256) {
        //Check if enrolled
        require(isEnrolled[msg.sender] == true);
        //Check if payment timestamp is valid
        require(now.sub(lastPaid[msg.sender]) > waitPeriod);
        
        //Calculate amount to Pay
        uint amountToPay = (sizeData / chunkSize) * dataRate;
        //Pay
        balances[msg.sender] = balances[msg.sender].add(amountToPay);
        //Update payment time
        lastPaid[msg.sender] = now;

        return balances[msg.sender];
    }

    // @notice Read balance of the account
    // @return The balance of the user
    function myBalance() public view returns (uint256) {
        return balances[msg.sender];
    }

    // @notice Read total supply of Omnies
    // @return The total supply of Omnies
    function totalSupply() public view returns (uint256) {
        return totalSupply_;
    }
    
    // @notice Log file upload and deduct Omnies
    function uploadFile(uint linkToOGF, string memory fileName, string memory fileHash, uint totalSize) public {
        emit logFile(msg.sender, linkToOGF, fileName, fileHash, totalSize);
        balances[msg.sender] = balances[msg.sender].sub((totalSize / chunkSize) * fileCost);
    }
    
    // @notice Log Chunk upload
    function uploadChunk(uint linkToOGF, uint senderGUID, uint receiverGUID, string memory chunkHash, uint chunkNb) public {
        emit logChunk(msg.sender, linkToOGF, senderGUID, receiverGUID, chunkHash, chunkNb);
    }
    
    // @notice Log file deletion
    function deleteFile(uint linkToOGF) public {
        emit logDeletion(msg.sender, linkToOGF);
    }
    
    // @notice Check if enrolled
    function getEnrolledStatus() public view returns (bool) {
        return isEnrolled[msg.sender];
    }
}

library SafeMath {
    function sub(uint256 a, uint256 b) internal pure returns (uint256) {
      assert(b <= a);
      return a - b;
    }
    function add(uint256 a, uint256 b) internal pure returns (uint256) {
      uint256 c = a + b;
      assert(c >= a);
      return c;
    }
}
