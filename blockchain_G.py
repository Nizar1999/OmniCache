import time
import json
import subprocess
import sys
import threading
import os
import logging

from os import path, listdir
from web3 import Web3, geth
from web3.middleware import geth_poa_middleware
from pathlib import Path
from logging.handlers import RotatingFileHandler

class bcNode:
    #-----------------------------------------------------------------------
    def __init__(self, ip):
    #-----------------------------------------------------------------------
        self.pubKey = ''
        self.web3 = ''
        self.ip = ip
        self.txNonceCount = 0
        self.initBlockchainNode()

    #-====================================Joining the Blockchain======================================

    #-----------------------------------------------------------------------
    def initBlockchainNode(self, genesisPK=None):
    #-----------------------------------------------------------------------
        Path("./logs/blockchain").mkdir(parents=True, exist_ok=True)

        #Internal function to run node in a new subprocess
        def runNode(command):
            logpipe = LogPipe()
            with subprocess.run(command, shell=True, stdout=logpipe, stderr=logpipe) as s:
                logpipe.close()

        #Run initialization script
        subprocess.run('cls', shell=True)
        print("Blockchain Node Setup")
        print("1- Create new account")
        print("2- Login to existing account")
        menuDo = input("Choose option: ")

        #If Creating New Account
        if(menuDo == '1'):
            #Delete existing data directory
            if(path.exists("./ETH/")):
                print("[Script Output] Deleting existing data directory..")
                command = 'rmdir /q /s "./ETH/"'
                res = subprocess.run(command, shell=True).returncode
                if(res != 0):
                    sys.exit("[Script Output] Could not delete files.")
                else:
                    print("[Script Output] Data directory deleted")

            #Create new account
            print("[Script Output] Creating account...")

            #Create tmp pass file for geth
            tmpFile = open("tmpPass", "w")
            tmpFile.write('123')
            tmpFile.close()

            #Command for creating new account
            command = 'geth account new --datadir ./ETH/node --password tmpPass'

            #Redirect account creation out to logfile
            with open('logs/blockchain/accinitLog.txt', "w") as outfile:
                subprocess.run(command, shell=True, stdout=outfile, stderr=outfile)

            #Read public keys
            keyFiles = [filename for filename in listdir('./ETH/node/keystore/') if filename.startswith("UTC")]

            #Set PubKey
            self.pubKey = "0x" + keyFiles[0].split("--")[2]

            #Create genesis.json
            genesisJson = json.dumps({"config":{"chainId":15,"homesteadBlock":0,"eip150Block":0,"eip155Block":0,"eip158Block":0,"byzantiumBlock":0,"constantinopleBlock":0,"petersburgBlock":0,"clique":{"period":5,"epoch":30000}},"difficulty":"1","gasLimit":"8000000","extradata":"0x{0}{1}{2}".format(64 * '0', self.pubKey[2:], 130 * '0'),"alloc":{"{0}".format(self.pubKey[2:]):{"balance":"3000000000000000000000"}}}, indent=4)
            with open("./ETH/genesis.json","w") as genesisFile :
                genesisFile.write(genesisJson)

            #Initialize data directory
            #Redirect initialization out to logfile
            print("[Script Output] Initializing Node...")
            command = 'geth init --datadir ./ETH/node ./ETH/genesis.json'
            with open('logs/blockchain/nodeinitLog.txt', "w") as outfile:
                init = subprocess.run(command, shell=True,  stdout=outfile, stderr=outfile).returncode

                #If initialization failed then abort
                if(init != 0):
                    sys.exit("[Script Output] Initialization failed. Aborting..")

        #Run node
        print("[Script Output] Starting genesis node... Please enter the node's password when terminal opens.")
        command = 'geth --datadir ./ETH/node --syncmode=full --cache=2048 --networkid 15 --port 30305 --nat extip:{0} --mine --unlock {1} --nodiscover --password {2}'.format(self.ip, self.pubKey, "tmpPass")

        threading.Thread(target=runNode, args=[command], daemon=True).start()

        subprocess.run('cls', shell=True)

        #Initialize web3
        print("Connecting to web3..")
        while True:
            self.web3 = Web3(Web3.IPCProvider())
            if self.web3.isConnected():
                self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)
                if self.web3.geth.personal.list_wallets()[0]['status'] == "Unlocked":
                    print("Web3 connected. ", self.web3.isConnected())
                    break

        #Make pubKey checksum
        self.pubKey = self.web3.toChecksumAddress(self.pubKey)

        #Deploy Contract
        #Contract Abi
        abi = json.loads('[{"inputs":[{"internalType":"uint256","name":"total","type":"uint256"}],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"accountAddress","type":"address"},{"indexed":true,"internalType":"uint256","name":"linkToOGF","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"senderGUID","type":"uint256"},{"indexed":true,"internalType":"uint256","name":"receiverGUID","type":"uint256"},{"indexed":false,"internalType":"string","name":"chunkHash","type":"string"},{"indexed":false,"internalType":"uint256","name":"chunkNb","type":"uint256"}],"name":"logChunk","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"accountAddress","type":"address"},{"indexed":true,"internalType":"uint256","name":"linkToOGF","type":"uint256"}],"name":"logDeletion","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"accountAddress","type":"address"},{"indexed":false,"internalType":"uint256","name":"linkToOGF","type":"uint256"},{"indexed":false,"internalType":"string","name":"fileName","type":"string"},{"indexed":false,"internalType":"string","name":"fileHash","type":"string"},{"indexed":false,"internalType":"uint256","name":"totalSize","type":"uint256"}],"name":"logFile","type":"event"},{"inputs":[{"internalType":"uint256","name":"linkToOGF","type":"uint256"}],"name":"deleteFile","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"enroll","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"getEnrolledStatus","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"sizeData","type":"uint256"}],"name":"giveOmnies","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"myBalance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"linkToOGF","type":"uint256"},{"internalType":"uint256","name":"senderGUID","type":"uint256"},{"internalType":"uint256","name":"receiverGUID","type":"uint256"},{"internalType":"string","name":"chunkHash","type":"string"},{"internalType":"uint256","name":"chunkNb","type":"uint256"}],"name":"uploadChunk","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"linkToOGF","type":"uint256"},{"internalType":"string","name":"fileName","type":"string"},{"internalType":"string","name":"fileHash","type":"string"},{"internalType":"uint256","name":"totalSize","type":"uint256"}],"name":"uploadFile","outputs":[],"stateMutability":"nonpayable","type":"function"}]')
        bytecode = "608060405234801561001057600080fd5b50604051610c6d380380610c6d8339818101604052602081101561003357600080fd5b8101908080519060200190929190505050806004819055506004546000803373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff1681526020019081526020016000208190555033600360006101000a81548173ffffffffffffffffffffffffffffffffffffffff021916908373ffffffffffffffffffffffffffffffffffffffff16021790555050610b8c806100e16000396000f3fe608060405234801561001057600080fd5b50600436106100935760003560e01c8063c9116b6911610066578063c9116b6914610138578063cc8d43be14610156578063e591247e14610198578063e65f2a7e146102fe578063f92bfb121461031c57610093565b806318160ddd146100985780636cd581dc146100b65780638da5cb5b146100d6578063c5b420061461010a575b600080fd5b6100a06103ff565b6040518082815260200191505060405180910390f35b6100be610409565b60405180821515815260200191505060405180910390f35b6100de61045d565b604051808273ffffffffffffffffffffffffffffffffffffffff16815260200191505060405180910390f35b6101366004803603602081101561012057600080fd5b8101908080359060200190929190505050610483565b005b6101406104ca565b6040518082815260200191505060405180910390f35b6101826004803603602081101561016c57600080fd5b8101908080359060200190929190505050610510565b6040518082815260200191505060405180910390f35b6102fc600480360360808110156101ae57600080fd5b8101908080359060200190929190803590602001906401000000008111156101d557600080fd5b8201836020820111156101e757600080fd5b8035906020019184600183028401116401000000008311171561020957600080fd5b91908080601f016020809104026020016040519081016040528093929190818152602001838380828437600081840152601f19601f8201169050808301925050505050505091929192908035906020019064010000000081111561026c57600080fd5b82018360208201111561027e57600080fd5b803590602001918460018302840111640100000000831117156102a057600080fd5b91908080601f016020809104026020016040519081016040528093929190818152602001838380828437600081840152601f19601f820116905080830192505050505050509192919290803590602001909291905050506106fe565b005b6103066108d5565b6040518082815260200191505060405180910390f35b6103fd600480360360a081101561033257600080fd5b810190808035906020019092919080359060200190929190803590602001909291908035906020019064010000000081111561036d57600080fd5b82018360208201111561037f57600080fd5b803590602001918460018302840111640100000000831117156103a157600080fd5b91908080601f016020809104026020016040519081016040528093929190818152602001838380828437600081840152601f19601f82011690508083019250505050505050919291929080359060200190929190505050610a57565b005b6000600454905090565b6000600160003373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16815260200190815260200160002060009054906101000a900460ff16905090565b600360009054906101000a900473ffffffffffffffffffffffffffffffffffffffff1681565b803373ffffffffffffffffffffffffffffffffffffffff167f5e3fab42c9e3f6ddc714be7ec0f99d96e23045ba348188ae7fd4d7ccdccfae0b60405160405180910390a350565b60008060003373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16815260200190815260200160002054905090565b600060011515600160003373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16815260200190815260200160002060009054906101000a900460ff1615151461056f57600080fd5b60146105c3600260003373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff1681526020019081526020016000205442610b2390919063ffffffff16565b116105cd57600080fd5b6000600a610e7884816105dc57fe5b04029050610631816000803373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16815260200190815260200160002054610b3a90919063ffffffff16565b6000803373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff1681526020019081526020016000208190555042600260003373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff168152602001908152602001600020819055506000803373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16815260200190815260200160002054915050919050565b3373ffffffffffffffffffffffffffffffffffffffff167f3e86e6c716ac149c59b4a4b4a36154694562015cc5df8202adada06372128ab285858585604051808581526020018060200180602001848152602001838103835286818151815260200191508051906020019080838360005b8381101561078a57808201518184015260208101905061076f565b50505050905090810190601f1680156107b75780820380516001836020036101000a031916815260200191505b50838103825285818151815260200191508051906020019080838360005b838110156107f05780820151818401526020810190506107d5565b50505050905090810190601f16801561081d5780820380516001836020036101000a031916815260200191505b50965050505050505060405180910390a261088d6001610e78838161083e57fe5b04026000803373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16815260200190815260200160002054610b2390919063ffffffff16565b6000803373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff1681526020019081526020016000208190555050505050565b6000801515600160003373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16815260200190815260200160002060009054906101000a900460ff1615151461093357600080fd5b6113886000803373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff1681526020019081526020016000208190555042600260003373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff1681526020019081526020016000208190555060018060003373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16815260200190815260200160002060006101000a81548160ff0219169083151502179055506000803373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16815260200190815260200160002054905090565b82853373ffffffffffffffffffffffffffffffffffffffff167f4b3afce9d26a711292492379dcd982e9cd2efd95998757bab0129d2b63f862ee8786866040518084815260200180602001838152602001828103825284818151815260200191508051906020019080838360005b83811015610ae0578082015181840152602081019050610ac5565b50505050905090810190601f168015610b0d5780820380516001836020036101000a031916815260200191505b5094505050505060405180910390a45050505050565b600082821115610b2f57fe5b818303905092915050565b600080828401905083811015610b4c57fe5b809150509291505056fea2646970667358221220aafeec821f6765efe3e8bc9119c171fa9283e8616b926a360f5208dc132cb59664736f6c634300060c0033"
        self.web3.eth.defaultAccount = self.web3.eth.accounts[0]

        contractInterface = self.web3.eth.contract(abi=abi, bytecode=bytecode) #Initialize the contract object
        tx_hash =  contractInterface.constructor(99999999999999).transact() #Deploy the contract
        tx_receipt = self.web3.eth.waitForTransactionReceipt(tx_hash) #Retreive the receipt
        #print(self.web3.eth.get_balance(self.web3.pubKey));
        print("Contract Address:",tx_receipt.contractAddress) #Return the contract address using the receipt
        

    #-----------------------------------------------------------------------
    def addToNet(self,enode):
    #-----------------------------------------------------------------------
        #Add node as peer
        self.web3.geth.admin.add_peer(enode)
        print("[Script Output] Adding node as blockchain peer...")


    #-----------------------------------------------------------------------
    def sendETH(self,puk):
    #-----------------------------------------------------------------------
        #Unlock account
        prefixed = [filename for filename in listdir('./ETH/node/keystore/') if filename.startswith("UTC")]
        with open('./ETH/node/keystore/{0}'.format(prefixed[0])) as keyfile:
            encrypted_key = keyfile.read()
            private_key = self.web3.eth.account.decrypt(encrypted_key, '123')

        #Set up transaction to receive ether
        if(self.txNonceCount == 0):                #Initialize Nonce in case of restart
            self.txNonceCount = self.web3.eth.getTransactionCount(self.pubKey)

        nonce = self.txNonceCount
        

        tx = {
            'chainId': 15,
            'nonce': nonce,
            'to': puk,
            'value': self.web3.toWei(100, 'ether'),
            'gas': 200000,
            'gasPrice': self.web3.toWei(50, 'gwei')
        }

        #Sign and send transaction
        signed_tx = self.web3.eth.account.signTransaction(tx, private_key)
        try:
            tx_hash = self.web3.eth.sendRawTransaction(signed_tx.rawTransaction)
            tx_receipt = self.web3.eth.waitForTransactionReceipt(tx_hash)

            print("Status: ", tx_receipt['status'])


            #Check status of eth transaction
            if(tx_receipt['status'] == 1):
                print("Successfully sent ETH!")
                self.txNonceCount += 1
            else:
                print("ETH Tx sent, but status failed!")
                self.sendETH(puk)

        except:
            print("Error with sendETH tx! Retrying..")
            self.sendETH(puk)

class LogPipe(threading.Thread):

    def __init__(self):
        #Setup the object with a logger and a loglevel and start the thread
        threading.Thread.__init__(self)
        self.daemon = False

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