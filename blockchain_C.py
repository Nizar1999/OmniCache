import time
import json
import subprocess
import sys
import threading
import os
import logging

from pathlib import Path
from shutil import copy
from os import path, listdir
from web3 import Web3, geth
from web3.middleware import geth_poa_middleware
from logging.handlers import RotatingFileHandler

class bcNode:
    #-----------------------------------------------------------------------
    def __init__(self, ip=None):
    #-----------------------------------------------------------------------
        self.pubKey = ''
        self.enode = ''
        self.web3 = ''
        self.ip = ip
        self.contract = None
        self.exists = False
        self.passPhrase = ''
        self.proc = None

    #-----------------------------------------------------------------------
    def dataDirsExist(self):
    #-----------------------------------------------------------------------
        exists = path.exists("./ETH/node") or path.exists("./ETH/genesis.json") or path.exists("./ETH/node/keystore")
        self.exists = exists
        return exists

    #-----------------------------------------------------------------------
    def runExistingNode(self):
    #-----------------------------------------------------------------------
        print("[Script Output] Running node...")
        #Internal function to run node in a new subprocess
        def runNode(command):
            logpipe = LogPipe()
            self.proc = subprocess.Popen(command, stdout=logpipe, stderr=logpipe)
            logpipe.close()

        command = 'geth --datadir ./ETH/node --syncmode=full --networkid 15 --cache=2048 --port 30305 --nat extip:{0} --nodiscover'.format(self.ip)
        threading.Thread(target=runNode, args=[command]).start()
        subprocess.run('cls', shell=True)

    #-====================================Account Setup======================================

    #-----------------------------------------------------------------------
    def createAccount(self):
    #-----------------------------------------------------------------------
        #Create new account
        print("[Script Output] Creating account...")

        #Create tmp pass file for geth
        tmpFile = open("tmpPass", "w")
        tmpFile.write(self.passPhrase)
        tmpFile.close()

        #Command for creating new account
        command = 'geth account new --datadir ./ETH/node --password tmpPass'

        #Attempt account creation
        #Redirect creation out to logfile
        Path("./logs/blockchain").mkdir(parents=True, exist_ok=True)
        with open('./logs/blockchain/accinitLog.txt', "w") as outfile:
            init = subprocess.run(command, shell=True, stdout=outfile, stderr=outfile).returncode

        #Delete the tmp pass file
        import os
        os.remove("tmpPass")

        #If account creation failed then abort
        if(init != 0):
            sys.exit("[Script Output] Account creation failed. Aborting..")
        

    #-----------------------------------------------------------------------
    def importAccount(self, pathToKey):
    #-----------------------------------------------------------------------
        #Importing existing account
        print("[Script Output] Importing account...")
        Path("./ETH/node/keystore/").mkdir(parents=True, exist_ok=True)
        copy(pathToKey, "./ETH/node/keystore/")

        #Create tmp pass file for geth
        tmpFile = open("tmpPass", "w")
        tmpFile.write(self.passPhrase)
        tmpFile.close()

        # #Read public keys
        # keyFiles = [filename for filename in listdir('./ETH/node/keystore/') if filename.startswith("UTC")]
        # #Set PubKey
        # self.pubKey = "0x" + keyFiles[0].split("--")[2]

        # command = 'geth --unlock "{0}" --password tmpPass'.format(self.pubKey)
        # result = subprocess.run(command, shell=True).returncode
        # if(result != 0):
        #     print("[Script Output] Account import failed.")
        #     return 0
        # return 1
        
    #-----------------------------------------------------------------------
    def createGenesisJson(self, genesisPK):
    #-----------------------------------------------------------------------
        #Create genesis.json
        genesisJson = json.dumps({"config":{"chainId":15,"homesteadBlock":0,"eip150Block":0,"eip155Block":0,"eip158Block":0,"byzantiumBlock":0,"constantinopleBlock":0,"petersburgBlock":0,"clique":{"period":5,"epoch":30000}},"difficulty":"1","gasLimit":"8000000","extradata":"0x{0}{1}{2}".format(64 * '0', genesisPK[2:], 130 * '0'),"alloc":{"{0}".format(genesisPK[2:]):{"balance":"3000000000000000000000"}}}, indent=4)
        with open("./ETH/genesis.json","w") as genesisFile :
            genesisFile.write(genesisJson)

        self.preRunInit()

    #-----------------------------------------------------------------------
    def preRunInit(self):
    #-----------------------------------------------------------------------
        #Initialize data directory
        #Redirect initialization out to logfile
        print("[Script Output] Initializing Node...")
        command = 'geth init --datadir ./ETH/node ./ETH/genesis.json'
        with open('logs/blockchain/nodeinitLog.txt', "w") as outfile:
            init = subprocess.run(command, shell=True,  stdout=outfile, stderr=outfile).returncode

            #If initialization failed then abort
            if(init != 0):
                sys.exit("[Script Output] Pre-Initialization failed. Aborting..")

    #-----------------------------------------------------------------------
    def postRunInit(self):
    #-----------------------------------------------------------------------
        self.runExistingNode()
        #Read public keys
        keyFiles = [filename for filename in listdir('./ETH/node/keystore/') if filename.startswith("UTC")]

        #Set PubKey
        self.pubKey = "0x" + keyFiles[0].split("--")[2]

        #Initialize web3
        print("[Script Output] Connecting to web3..")
        while True:
            self.web3 = Web3(Web3.IPCProvider())
            self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)
            if self.web3.isConnected():
                print("[Script Output] Web3 connected.")
                break

        #Initialize Enode
        self.enode = self.web3.geth.admin.node_info()["enode"]

        #Make pubKey checksum
        self.pubKey = self.web3.toChecksumAddress(self.pubKey)

        #Initialize contract
        #Get contract address to interface with
        contractAddress = input("[Script Output] Contract Address: ")
        
        #Initialize contract Abi
        abi = json.loads('[{"inputs":[{"internalType":"uint256","name":"total","type":"uint256"}],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"accountAddress","type":"address"},{"indexed":true,"internalType":"uint256","name":"linkToOGF","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"senderGUID","type":"uint256"},{"indexed":true,"internalType":"uint256","name":"receiverGUID","type":"uint256"},{"indexed":false,"internalType":"string","name":"chunkHash","type":"string"},{"indexed":false,"internalType":"uint256","name":"chunkNb","type":"uint256"}],"name":"logChunk","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"accountAddress","type":"address"},{"indexed":true,"internalType":"uint256","name":"linkToOGF","type":"uint256"}],"name":"logDeletion","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"accountAddress","type":"address"},{"indexed":false,"internalType":"uint256","name":"linkToOGF","type":"uint256"},{"indexed":false,"internalType":"string","name":"fileName","type":"string"},{"indexed":false,"internalType":"string","name":"fileHash","type":"string"},{"indexed":false,"internalType":"uint256","name":"totalSize","type":"uint256"}],"name":"logFile","type":"event"},{"inputs":[{"internalType":"uint256","name":"linkToOGF","type":"uint256"}],"name":"deleteFile","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"enroll","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"getEnrolledStatus","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"sizeData","type":"uint256"}],"name":"giveOmnies","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"myBalance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"linkToOGF","type":"uint256"},{"internalType":"uint256","name":"senderGUID","type":"uint256"},{"internalType":"uint256","name":"receiverGUID","type":"uint256"},{"internalType":"string","name":"chunkHash","type":"string"},{"internalType":"uint256","name":"chunkNb","type":"uint256"}],"name":"uploadChunk","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"linkToOGF","type":"uint256"},{"internalType":"string","name":"fileName","type":"string"},{"internalType":"string","name":"fileHash","type":"string"},{"internalType":"uint256","name":"totalSize","type":"uint256"}],"name":"uploadFile","outputs":[],"stateMutability":"nonpayable","type":"function"}]')

        #Initialize contract object
        self.contract = self.web3.eth.contract(address=contractAddress, abi=abi)

        #Initialize Account
        self.web3.eth.defaultAccount = self.web3.eth.accounts[0]

    
    #-----------------------------------------------------------------------
    def validatePass(self):
    #-----------------------------------------------------------------------
        try:
            #Unlock Account
            self.web3.geth.personal.unlock_account(self.web3.eth.accounts[0], self.passPhrase, 0)
            #Clear PassPhrase from memory
            self.passPhrase = ''
            return True
        except:
            print("Failed to unlock account");
            #Invalidate PassPhrase
            return False

    #-----------------------------------------------------------------------
    def addToNet(self,enode):
    #-----------------------------------------------------------------------
        #Add node as peer
        while(not self.web3.geth.admin.add_peer(enode)):
        	print("[Script Output] Failed adding peer. Retrying..")

        print("[Script Output] Adding node as blockchain peer...")


    #-====================================Smart Contract Interface======================================

    #-----------------------------------------------------------------------
    def enroll(self):
    #-----------------------------------------------------------------------
        if(self.isEnrolled()):
            print("[Script Output] Already enrolled.")
            return
        
        while True:
            if self.web3.eth.getBalance(self.pubKey) != 0 :
                break

        print("[Script Output] Attempting enroll..")
        try:
            tx_hash = self.contract.functions.enroll().transact()
            tx_receipt = self.web3.eth.waitForTransactionReceipt(tx_hash)

            #Check status of enroll transaction
            if(tx_receipt['status'] == 1):
                print("[Script Output] Omnies Balance: ", self.getOmnies())
            else:
                print("[Script Output] Failed in receiving Omnies. Retrying..")
                self.enroll()
        except:
            print("[Script Output] Transaction failed. Retrying..")
            self.enroll()


    #-----------------------------------------------------------------------
    def logFileUpload(self, linkToOGF, fileName, fileHash, totalSize):
    #-----------------------------------------------------------------------
        #Transact with smart contract that File needs to be uploaded
        print("[Script Output] Logging File")

        #Call upload file
        try:
            tx_hash = self.contract.functions.uploadFile(linkToOGF, fileName, fileHash, totalSize).transact()
            tx_receipt = self.web3.eth.waitForTransactionReceipt(tx_hash)

            #Check status of enroll transaction
            if(tx_receipt['status'] == 1):
                print("[Script Output] Logged file successfully.")
                print("[Script Output] Omnies Balance: ", self.getOmnies())
            else:
                print("[Script Output] Failed in logging file.")
        except:
            print("[Script Output] Transaction failed.")

    #-----------------------------------------------------------------------
    def logChunkUpload(self, linkToOGF, senderGUID, receiverGUID, chunkHash, chunkNb):
    #-----------------------------------------------------------------------
        #Transact with smart contract that chunk has been uploaded
        print("[Script Output] Logging chunk number", chunkNb)

        #Call upload chunk
        try:
            tx_hash = self.contract.functions.uploadChunk(linkToOGF, senderGUID, receiverGUID, chunkHash, chunkNb).transact()
            tx_receipt = self.web3.eth.waitForTransactionReceipt(tx_hash)

            #Check status of enroll transaction
            if(tx_receipt['status'] == 1):
                print("[Script Output] Logged chunk successfully.")
            else:
                print("[Script Output] Failed in logging chunk.")
        except:
            print("[Script Output] Transaction failed.")

    #-----------------------------------------------------------------------
    def logDeletion(self, linkToOGF):
    #-----------------------------------------------------------------------
        #Transact with smart contract that file has been deleted
        print("[Script Output] Logging file deletion")

        #Call delete file
        try:
            tx_hash = self.contract.functions.deleteFile(linkToOGF).transact()
            tx_receipt = self.web3.eth.waitForTransactionReceipt(tx_hash)

            #Check status of enroll transaction
            if(tx_receipt['status'] == 1):
                print("[Script Output] Logged file deletion successfully.")
            else:
                print("[Script Output] Failed in logging deletion.")
        except:
            print("[Script Output] Transaction failed.")


    #-====================================Event Filtering======================================

    #-----------------------------------------------------------------------
    def filterByAddress(self):
    #-----------------------------------------------------------------------
        #Read logFile events
        validFiles=[]
        event_filter = self.contract.events.logFile.createFilter(fromBlock=0, argument_filters={'accountAddress':self.web3.eth.defaultAccount})
        for event in event_filter.get_all_entries():
            receipt = self.web3.eth.getTransactionReceipt(event['transactionHash']) #Get the transaction receipt
            result = self.contract.events.logFile().processReceipt(receipt) #Process receipt data from hex

            #Check if file is valid
            if self.isFileValid(result[0]['args']['linkToOGF']) :   
                print("Valid File: ")
                print("\tlinkToOGF:", result[0]['args']['linkToOGF'])
                print("\tfileName:", result[0]['args']['fileName'])
                print("\tfileHash:", result[0]['args']['fileHash'])
                print("\ttotalSize:", result[0]['args']['totalSize'])

                validFiles.append(result[0]['args'])
        return validFiles

    #-----------------------------------------------------------------------
    def filterByFile(self, link):
    #-----------------------------------------------------------------------
        #Read logChunk events
        chunks=[]
        event_filter = self.contract.events.logChunk.createFilter(fromBlock=0, argument_filters={'accountAddress':self.web3.eth.defaultAccount, 'linkToOGF':link})
        for event in event_filter.get_all_entries():
            receipt = self.web3.eth.getTransactionReceipt(event['transactionHash']) #Get the transaction receipt
            result = self.contract.events.logChunk().processReceipt(receipt) #Process receipt data from hex

            print("Chunk Nb:", result[0]['args']['chunkNb'])
            print("linkToOGF:", result[0]['args']['linkToOGF'])
            print("senderGUID:", result[0]['args']['senderGUID'])
            print("receiverGUID:", result[0]['args']['receiverGUID'])
            print("chunkHash:", result[0]['args']['chunkHash'])
            
            chunks.append(result[0]['args'])
        return chunks

    #-----------------------------------------------------------------------
    def filterByRGUID(self, recvGUID, chunkHashes):
    #-----------------------------------------------------------------------
        validChunksHosted = []
    	#Read logChunk events for the specific recvGUID
        event_filter = self.contract.events.logChunk.createFilter(fromBlock=0, argument_filters={'receiverGUID':recvGUID})
        for event in event_filter.get_all_entries():
            receipt = self.web3.eth.getTransactionReceipt(event['transactionHash']) #Get the transaction receipt
            result = self.contract.events.logChunk().processReceipt(receipt) #Process receipt data from hex

            #For each chunk returned, check if its currently on host's machine
            print(result[0]['args']['chunkHash'])
            if result[0]['args']['chunkHash'] in chunkHashes:
                #If yes, check if its valid
                if self.isFileValid(result[0]['args']['linkToOGF']):
                    #If valid append to list of validChunksHosted
                    if result[0]['args']['chunkHash'] not in validChunksHosted:
                        validChunksHosted.append(result[0]['args']['chunkHash'])
                else:
                    if result[0]['args']['chunkHash'] in validChunksHosted:
                        validChunksHosted.remove(result[0]['args']['chunkHash'])

        return validChunksHosted

    #-----------------------------------------------------------------------
    def isFileValid(self, link):
    #-----------------------------------------------------------------------
        #Read logDeletion events
        event_filter = self.contract.events.logDeletion.createFilter(fromBlock=0, argument_filters={'linkToOGF':link})
        if(not event_filter.get_all_entries()):
            return True

        return False

    #-----------------------------------------------------------------------    
    def requestPayment(self, dataSize):
    #-----------------------------------------------------------------------
        #Transact with smart contract that file has been deleted
        print("[Script Output] Requesting payment..")

        #Call giveOmnies
        try:
            tx_hash = self.contract.functions.giveOmnies(dataSize).transact()
            tx_receipt = self.web3.eth.waitForTransactionReceipt(tx_hash)
            #Check status of enroll transaction
            if(tx_receipt['status'] == 1):
                print("[Script Output] Payment received successfully.")
            else:
                print("[Script Output] Failed in requesting payment.")
        except:
            print("[Script Output] Transaction failed.")

    #-----------------------------------------------------------------------
    def getOmnies(self):
    #-----------------------------------------------------------------------
        return self.contract.functions.myBalance().call()

    #-----------------------------------------------------------------------
    def isEnrolled(self):
    #-----------------------------------------------------------------------
        return self.contract.functions.getEnrolledStatus().call()

    #-----------------------------------------------------------------------
    def checkSyncStatus(self):
    #-----------------------------------------------------------------------
        while True:
            print("[Script Output] Waiting for Geth..")
            print(self.web3.net.peer_count)
            if self.web3.net.peer_count != 0:
                print(self.web3.eth.syncing)
                print(self.web3.eth.block_number())
                if (not self.web3.eth.syncing) and (self.web3.eth.block_number() != 0):
                    break

class LogPipe(threading.Thread):

    def __init__(self):
        #Setup the object with a logger and a loglevel and start the thread
        threading.Thread.__init__(self)
        self.daemon = True

        handler=RotatingFileHandler('./logs/blockchain/runLog.txt', maxBytes=8192, backupCount=1)
        self.logger = logging.getLogger('my_logger')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)

        self.fdRead, self.fdWrite = os.pipe()
        self.pipeReader = os.fdopen(self.fdRead)
        self.start()

    def fileno(self):
        #Return the write file descriptor of the pipe
        return self.fdWrite

    def run(self):
        #Run the thread, logging everything.
        for line in iter(self.pipeReader.readline, ''):
            self.logger.info(line.strip('\n'))
        self.pipeReader.close()

    def close(self):
        #Close the write end of the pipe.
        os.close(self.fdWrite)
