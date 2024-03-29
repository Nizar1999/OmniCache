import socket
import uuid
import sys
import threading
import datetime
import subprocess
import time
import json
import math
from pathlib import Path
from blockchain_C import bcNode
from os import listdir , walk , remove, stat
from os.path import isfile, join , getsize , basename ,exists
import hashlib
import shutil
import random
from Crypto.Cipher import AES
from Crypto.Util.number import getPrime
from math import gcd

class Node:
    #-----------------------------------------------------------------------
    def __init__(self,myip,port,bNode,npeer=10,guid=None):
    #-----------------------------------------------------------------------
        self.bNode=bNode
        self.myip=myip
        self.port=port

        if guid:
            self.guid=guid
        else:
            print("guid was not provided, should be later on")
            self.guid=guid

        self.npeer=npeer #max number of peers

        self.peers={} #our routing table
        self.keys={} #keys established with peers 

        self.protocol={
            'JOIN':self.join,#JOIN code
            'UPFL':self.upfl,#UPFL code :  upload file 
            'AKFL':self.akfl,#Acknowledge file code
            'FUND':self.fund,#FUND code request to genesis to send eth when account is empty
            'ADPR':self.adpr,#ADPR code add peer when new peer joins
            'DEFS':self.defs,#DEFS code define self after getting id and table from genesis
            'ADBN':self.adbn,#ADBN code add blockchain node after gettting it's PK and Enode
            'RSCM':self.rscm,#RSCM code establish shared secret key with peer
            'PING':self.ping,#PING request to test connection and latency
            'DWFL':self.dwfl,#DWFL request to download file
            'RJON':self.rjon}#RJON request to peers rejoining maybe with different accounts
        
        """ if self.bNode.isGenesis:
            self.lastid=0
            self.guid=self.lastid
        else: """
        print("normal peer")

        self.startTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.turnoff=False
        self.ready=False
        self.space=500*(10**6) #in Bytes
        self.chunkSize=3704 #multiple of 13 and less then 4096
        self.fileQueue={}
        self.myItems={}
        self.replicationFactor=1
        self.threads={}
        self.hold=[]
        self.connections={}

    #================================Protocols===============================================
    
    def rjon(self,peercon,data):
        try:
            peer=min(self.peers.keys())
            toforward=self.peers[peer]
            self.connectAndSend(toforward[0],toforward[1],"rjon",data,pId=peer,waitReply=False)
            self.logging("Forwarding a {} request to peer id = {}".format("RJON",peer))
        except Exception as e:
            print(e)
    
    def join(self,peercon,data): #JOIN code
        ip, port = data.split('-')
        """ if self.bNode.isGenesis :
            #if this node is the genesis node send him eather and add him to table
            if not self.peerLimitReached():
                if [ip,int(port)] not in self.peers.values():
                    self.addPeer(self.lastid+1,ip,int(port))
                    self.lastid+=1 
                    #need to save lastid offline

                    #broadcast peer added
                    tosend="-".join([str(self.lastid),ip,str(port)])
                    self.broadcast("adpr",tosend,self.lastid)
                    #send the joining node an id and routing table
                    table=self.peers.copy()
                    table[self.guid]=[self.myip,self.port]
                    print(self.peers)
                    table=json.dumps(table)
                    tosend="-".join([str(self.lastid),self.bNode.pubKey,table]) #this wont work if table is big because recv 4096 bytes only
                    # ! on the receiver side the keys will be of type Char
                    self.connectAndSend(ip,int(port),'defs',tosend,pId=self.lastid,waitReply=False)
                    #self.bNode.addToNet(enode)
                    #self.bNode.sendETH(puk)
                    self.logging("New peer {} joined the Network".format(self.lastid))
                else:
                    peerguid=self.get_key([ip,int(port)])
                    #send the joining node an id and routing table
                    table=self.peers.copy()
                    table[self.guid]=[self.myip,self.port]
                    print("Peer {} rejoined".format(peerguid))
                    table=json.dumps(table)
                    tosend="-".join([str(peerguid),self.bNode.pubKey,table]) #this wont work if table is big because recv 4096 bytes only
                    # ! on the receiver side the keys will be of type Char
                    self.connectAndSend(ip,int(port),'defs',tosend,pId=peerguid,waitReply=False)
                    #self.bNode.addToNet(enode)
                    #self.bNode.sendETH(puk)
                    self.logging("Peer {} rejoined the Network".format(self.lastid))
        else: """
        try:
            peer=min(self.peers.keys())
            toforward=self.peers[peer]
            self.connectAndSend(toforward[0],toforward[1],"join",data,pId=peer,waitReply=False)
            self.logging("Forwarding a {} request to peer id = {}".format("JOIN",peer))
        except Exception as e:
            print(e)


    def adbn(self,peercon,data):
        pk , enode= data.split('-')
        """ if self.bNode.isGenesis :
            self.bNode.addToNet(enode)
            self.logging("added new peer to the blockchain network *") 
            self.bNode.sendETH(pk)
        else: """
        self.bNode.addToNet(enode)
        self.logging("added new peer to the blockchain network")
        #if adbn was broadcasted comment out the code below

        """ peer = min(self.peers.keys())
        toforward = self.peers[peer]
        self.connectAndSend(toforward[0],toforward[1],"adbn",data,pId=peer,waitReply=False)
        self.logging("Forwarding a {} request to peer id = {}".format("ADBN",peer)) """

    def ping(self,peercon,data):
        peercon.sendData('ping','pong')

    def upfl(self,peercon,data): # UPFL code :  upload file
        chunkID=data[0].decode('utf-8')
        print(chunkID)
        #print(pack[1])
        chunk=data[1]
        print('g1')
        chunkHash =  hashlib.sha1(chunk).hexdigest()
        self.hold.append(chunkHash)
        #save chunk
        if self.saveChunk(chunk,chunkHash):
            print(chunkID," ---ACK")
            tosend=chunkID+'-1'
            peercon.sendData('ackf',tosend)
            self.logging("Received file named : {}".format(chunkHash))
        else:
            tosend=chunkID+'-0'
            peercon.sendData('ackf',tosend)
            self.logging("* Receive file failed : {}")

        
    def dwfl(self,peercon,data):
        chunkHash = data
        filename = self.getFile(chunkHash)
        if filename:
            self.sendFile(peercon,filename)
        else:
            peercon.sendData('akfl','0')



    def akfl(self,peercon,data): # Acknowledge file code
        pid , fileN = data.split('-')
        print("got ACK for file named: ",fileN)
        self.logging("peer {} uploaded a file named : {}".format(pid,fileN))

    #not used in this scenario
    def fund(self,peercon,data): #FUND code request to genesis to send eth when account is empty
        pass


    def adpr(self,peercon,data): # ADPR code add peer when new peer joins
        pid , ip , port = data.split('-')
        self.addPeer(int(pid),ip,int(port))

    
    def defs(self,peercon,data): # DEFS code define self after getting id and table from genesis
        guid , genesisPK ,table = data.split('-')
        guid=int(guid)
        table=json.loads(table)
        self.setmyid(guid)
        for peer in table :
            if int(peer) != guid:
                self.peers[int(peer)]=table[peer]
        self.logging("Sucessfully defined as peerID = {} \n with table {}\n Genesis PK : {}".format(guid,table,genesisPK))
        #start generating keys
        
        self.generateKeys()

        #self.bNode.postRunInit()
        if(not self.bNode.exists):
            self.bNode.createGenesisJson(genesisPK)
            
        self.ready=True
        thread = threading.Thread(target=self.heartbeats)
        thread.start()
        self.threads['hearts']=thread
        #self.bNode.initBlockchainNode(genesisPK=genesisPK)

        #at the end send an add blockchain node to network (ADBN) request
        #peer=max(self.peers.keys()) #or random 
        #toforward=self.peers[peer]
        
        #self.connectAndSend(toforward[0],toforward[1],"adbn",tosend,pId=peer,waitReply=False)
        #passphrase = input("Enter passphrase: ")
        #self.bNode.postRunInit(passphrase)       
        # we could broadcast to everyone but we would need to ommit the forwarding from the adbn function
        #tosend='-'.join([self.bNode.pubKey,self.bNode.enode])
        #self.broadcast("adbn",tosend,-1)
        
        #time.sleep(20)
        #self.bNode.enroll()
        #time.sleep(6)
        
        #self.startCleaning()
        """ time.sleep(3)
        if len(self.peers)>1:
            time.sleep(1)
            self.test() """

    #========================================================================================
    
    #=========================================Secure Comms===================================
    
    #--------------------------------------------------------------------------------------
    def primRoots(self,modulo):
    #--------------------------------------------------------------------------------------
        coprime_set = {num for num in range(1, modulo) if gcd(num, modulo) == 1}
        return [g for g in range(1, modulo) if coprime_set == {pow(g, powers, modulo)
                for powers in range(1, modulo)}]


    #protocol code needs to be created for this function
    #--------------------------------------------------------------------------------------
    def establishSecComm(self,target):
    #--------------------------------------------------------------------------------------
        '''
        Uses Diffie Helman key exchange to setup a shared secret key between the 2 parties
        '''
        P=getPrime(10)
        G=random.choice(self.primRoots(P))
        #print("P = {}, G = {}".format(P,G))
        #a for bob
        a= random.randint(2,1000) #privat
        x=pow(G,a)%P #public

        # share/send P,G and x
        #then receive y
        tosend='-'.join([str(self.guid),str(P),str(G),str(x)])
        try:
            ip , port = self.peers[target]
            code, y=self.connectAndSend(ip,port,'rscm',tosend)
            #shared secret
            if code=='yscm':
                ka=pow(int(y),a)%P
                key=hashlib.sha256(ka.to_bytes(10,byteorder='big')).digest()
                self.keys[target]=key
                return True
            else:
                return False
        except:
            self.logging("* Could not connect to establish secure coms with {} ".format(target))
            return False


    #--------------------------------------------------------------------------------------
    def rscm(self,peercon,data):
    #--------------------------------------------------------------------------------------
        try:
            guid,P,G,x=data.split('-')
            guid=int(guid)
            P=int(P)
            G=int(G)
            x=int(x)
            b= random.randint(2,1000) #privat
            y=pow(G,b)%P #public
            #send y
            peercon.sendData('yscm',str(y))
            kb=pow(x,b)%P
            key=hashlib.sha256(kb.to_bytes(10,byteorder='big')).digest()
            self.logging("Generated a key with peer : {}".format(guid))
            self.keys[guid]=key #store it with in table
        except:
            self.logging("Could not generated a key with peer : {}".format(guid))


    #--------------------------------------------------------------------------------------
    def encrypt(self,key,to_encrypt):
    #--------------------------------------------------------------------------------------
        cipher=AES.new(key,AES.MODE_EAX)
        nonce = cipher.nonce
        ciphertext, tag = cipher.encrypt_and_digest(to_encrypt)
        return (ciphertext,nonce,tag)


    #--------------------------------------------------------------------------------------
    def decrypt(self,key ,nonce,to_decrypt):
    #--------------------------------------------------------------------------------------
        cipher=AES.new(key,AES.MODE_EAX,nonce=nonce)
        plaintext=cipher.decrypt(to_decrypt)
        return plaintext
        
    #--------------------------------------------------------------------------------------
    def generateKeys(self):
    #--------------------------------------------------------------------------------------
        try:
            for peer in self.peers:
                time.sleep(0.5)
                if self.testCon(peer)[0]:
                    self.establishSecComm(peer)
                    self.logging("Established secure coms with peer : {} ".format(peer))
                else:
                    self.logging("Peer : {} is offline".format(peer))
        except:
            self.logging("* Could not  establish secure coms with peer : {} ".format(peer))
        

    #========================================================================================

    
    
    
    #==========================================Files=========================================
    
    """  
    #--------------------------------------------------------------------------------------
    def fetchMyFiles(self):
    #--------------------------------------------------------------------------------------
        '''
        Return clients files in a dict with linkToOGF as key
        [
            {
                linkToOGF
                fileName
                fileHash
                totalSize
            },
        ]
        '''
        try:
            myFiles= self.bNode.filterByAddress()
            return myFiles
        except Exception as e:
            self.logging('* Failed to retraive files from blockchain')
            print(e)
            return None
        

    #--------------------------------------------------------------------------------------
    def fetchChunks(self,linkToOGF):
    #--------------------------------------------------------------------------------------
        '''
        Return  file chunks in an array of dicts
        [
            {
                chunkNb
                linkToOGF
                senderGUID
                receiverGUID
                chunkHash
            },
        ]
        '''
        try:
            chunks=self.bNode.filterByFile(linkToOGF)
            return chunks
        except Exception as e:
            print(e)
            return None """

    """ #--------------------------------------------------------------------------------------
    def deleteFile(self,linkToOGF):
    #--------------------------------------------------------------------------------------
        '''
        Invalidates a file with specific linkToOGF
        '''
        self.bNode.logDeletion(linkToOGF) """


    #--------------------------------------------------------------------------------------
    def saveChunk(self,chunk,chunkHash,mine=False):
    #--------------------------------------------------------------------------------------
        try:
            if mine:
                f= open(Path("./myFiles/"+chunkHash),'wb')
            else:
                f= open(Path("./hosted/"+chunkHash),'wb')
                #if self.getUsedSpace() >= self.space:
                    #return False
            f.write(chunk)
            f.close()
            return True
        except Exception as e:
            print(e)
            return False
    

    #--------------------------------------------------------------------------------------
    def downloadChunk(self,target,chunkHash):
    #--------------------------------------------------------------------------------------
        '''
        Download chunk with chunkhash from target peer 
        '''
        ip , port = self.peers[target]
        try:
            code , reply = self.connectAndSend(ip,port,'dwfl',chunkHash,self.keys[target])
        except Exception as e:
            print(e)
            self.logging('* Problem occured while downloading chunk {}'.format(chunkHash))
            return False

        if code == 'gtfl':
            self.saveChunk(reply,chunkHash,mine=True)
            self.logging('Chunk {} has been downloaded'.format(chunkHash))
            return True
        else:
            if reply=='0' and code =='akfl':
                print('Peer {} does not have file {}'.format(target,chunkHash))
                self.logging('Chunk {} failed to download from peer {}'.format(chunkHash,target))
                return False

    #--------------------------------------------------------------------------------------
    def getChunk(self,toDownload,chunkHash,recvGUID,downloadedChunks,ordered_chunks,number):
    #--------------------------------------------------------------------------------------
        '''
        Test connection to peer and download the chunk if it's not already downloaded
        '''
        if chunkHash not in toDownload:
            toDownload.append(chunkHash)
            if (chunkHash not in downloadedChunks) and self.testCon(recvGUID)[0]:
                if self.downloadChunk(recvGUID,chunkHash):
                    downloadedChunks.append(chunkHash)
                    ordered_chunks[number]=chunkHash
                    print(chunkHash, 'Downloaded')
                else:
                    toDownload.remove(chunkHash)
                    print(chunkHash, 'Not Downloaded')

    #--------------------------------------------------------------------------------------
    def chunksMissing(self,linkToOGF,ordered_chunks):
    #--------------------------------------------------------------------------------------
        '''
        Checks for any missing chunks
        '''
        myFiles = self.bNode.filterByAddress()
        totalSize=0
        for item in myFiles:
            if item['linkToOGF'] == linkToOGF:
                totalSize = item['totalSize']

        numberOfChunks=totalSize//self.chunkSize
        missingChunksOrder=[]
        for i in range(numberOfChunks):
            if i not in ordered_chunks:
                missingChunksOrder.append(i)
        
        if not missingChunksOrder:
            return (False,missingChunksOrder)
        else:
            return (True,missingChunksOrder)

    #--------------------------------------------------------------------------------------
    def getMissingCInfo(self,chunks,missingChunksOrder):
    #--------------------------------------------------------------------------------------
        '''
        Get the information of missing chunks
        '''
        missingChunks=[]
        for chunk in chunks:
            if chunk['chunkNb'] in missingChunksOrder:
                missingChunks.append(chunk)
        return missingChunks

    #--------------------------------------------------------------------------------------
    def mergeChunks(self,fileName,ordered_chunks):
    #--------------------------------------------------------------------------------------
        '''
        Reconstruct a file after having downloaded all it'chunks
        '''
        with open(Path("./myFiles/"+fileName),'ab') as Ofile:
            for num in range(len(ordered_chunks)):
                with open(Path("./myFiles/"+ordered_chunks[num]),'rb') as chunk:
                    Ofile.write(chunk.read())
        print("Merged chunks into {}".format(fileName))

           

    #--------------------------------------------------------------------------------------
    def downloadFile(self,fileName,linkToOGF):
    #--------------------------------------------------------------------------------------
        '''
        Downloads all chunks pertaining to a file and reconstructs it locally
        '''
        downloadedChunks=[]
        chunks = self.bNode.filterByFile(linkToOGF)
        ordered_chunks = {}
        downloadThreads=[]
        queue=0
        check=''
        toDownload=[]
        if chunks != None:
            for chunk in chunks:
                if queue<3:
                    x=threading.Thread(target=self.getChunk,args=[toDownload,chunk['chunkHash'],chunk['receiverGUID'],downloadedChunks,ordered_chunks,chunk['chunkNb'],])
                    downloadThreads.append(x)
                    x.start()
                    queue+=1
                    time.sleep(1)
                else:
                    for thread in downloadThreads:
                        thread.join()
                    queue=0
            
            for thread in downloadThreads:
                thread.join()
            
            downloadThreads.clear()
            queue=0
            check = self.chunksMissing(linkToOGF,ordered_chunks)
            tries=0
            while check[0] and tries<10:
                time.sleep(2)
                toDownload = self.getMissingCInfo(chunks,check[1])
                for chunk in toDownload:
                    if queue<3:
                        x=threading.Thread(target=self.getChunk,args=[chunk['chunkHash'],chunk['receiverGUID'],downloadedChunks,ordered_chunks,chunk['chunkNb'],])
                        downloadThreads.append(x)
                        x.start()
                        queue+=1
                    else:
                        for thread in downloadThreads:
                            thread.join()
                        queue=0
                
                for thread in downloadThreads:
                    thread.join()
                
                check = self.chunksMissing(linkToOGF,ordered_chunks)
                tries+=1
            #reconstruct after all is downloaded
            self.mergeChunks(fileName,ordered_chunks)
            if not check[0]:
                self.DeleteFiles(chunks,hDir=False)






    #--------------------------------------------------------------------------------------
    def getHostedFiles(self):
    #--------------------------------------------------------------------------------------
        '''
        Returns a list of all the files hosted locally
        '''
        hostedFiles=[]
        for (dirpath , dirnames , filenames) in walk(Path("./hosted")):
            for item in filenames:
                hostedFiles.append(item)
        return hostedFiles

    #--------------------------------------------------------------------------------------
    def DeleteFiles(self,filesList,hDir=True):
    #--------------------------------------------------------------------------------------
        '''
        Delete files that are in the fileList from hosted or myFiles dir
        '''
        directory=''
        files=[]
        if hDir:
            files=filesList
            directory=Path("./hosted")
            print('Deleting')
            for (dirpath , dirnames , filenames) in walk(directory):
                for item in filenames:
                    if item not in files:
                        remove(join(directory,item))
                        self.logging('Deleted File : {}'.format(item))
        else:
            #list of chunks not chunk hashes only
            for chunk in filesList:
                files.append(chunk['chunkHash'])
            directory=Path("./myFiles")
            print('Deleting')
            for (dirpath , dirnames , filenames) in walk(directory):
                for item in filenames:
                    if item in files:
                        remove(join(directory,item))
                        self.logging('Deleted File : {}'.format(item))
        

    #--------------------------------------------------------------------------------------
    def cleanHosted(self, omniesLabel, dataLabel):
    #--------------------------------------------------------------------------------------
        '''
        Delete files that are no longer valid 
        '''
        while True:
            time.sleep(2*60)
            print("cleaning")
            hostedFiles = self.getHostedFiles()
            #print(hostedFiles)
            if not hostedFiles:
                continue
            else:
                toNotDelete = self.bNode.filterByRGUID(self.guid, hostedFiles) #hashes
                #print(toNotDelete)
                print('started Deleting')
                items = list(set(toNotDelete + self.hold)) 
                self.DeleteFiles(items)
                self.hold.clear()
                if len(self.getHostedFiles()):
                    self.bNode.requestPayment(len(self.getHostedFiles())*self.chunkSize)
                print(self.bNode.getOmnies())
                omniesLabel.setText(str(self.bNode.getOmnies()))
                usedSpace = self.getUsedSpace()
                postFixList = ["KB", "MB", "GB", "TB"]
                postFix = "B"
                count = 0
                while(usedSpace >= 1024):
                    postFix = postFixList[count]
                    count += 1
                    usedSpace /= 1024

                dataLabel.setText("Hosting: " + "{:.3f}".format(usedSpace) + " " + postFix)

    #--------------------------------------------------------------------------------------
    def startCleaning(self, omniesLabel, hostingLabel):
    #--------------------------------------------------------------------------------------
        '''
        Start the cleaning thread 
        '''
        cleaner = threading.Thread(target=self.cleanHosted,args=[omniesLabel, hostingLabel,])
        self.threads['cleaner']=cleaner
        cleaner.start()


    #--------------------------------------------------------------------------------------
    def getFile(self,chunkHash):
    #--------------------------------------------------------------------------------------
        '''
        gets the file with chunkhash as name
        '''
        for (dirpath , dirnames , filenames) in walk(Path("./hosted")):
            for item in filenames:
                if item==chunkHash:
                    return item
        return None


    #--------------------------------------------------------------------------------------
    def getUsedSpace(self):
    #--------------------------------------------------------------------------------------
        '''
        gets the used space inside the folder
        '''
        total = 0
        for dirpath , dirnames , filenames in walk('./hosted'):
            for item in filenames:
                itemPath = join(dirpath, item)
                total += getsize(itemPath)
        return total

    #--------------------------------------------------------------------------------------
    def spaceCheck(self):
    #--------------------------------------------------------------------------------------
        '''
        gets the used space inside the folder
        '''
        total = self.getUsedSpace()
        disktotal ,used ,free = shutil.disk_usage('.')

        if free < self.space :
            return (False , 0) # not enough free space
        elif free >= self.space and total > self.space:
            return (False , 1) # user needs to extend the space limit if he wants to host more
        elif free >= self.space and total <= self.space:
            return (True , 2) # all good


    #--------------------------------------------------------------------------------------
    def setup(self):
    #--------------------------------------------------------------------------------------
        '''
        creates needed dirs if not already existant and returns their content 
        '''
        Path("./myFiles").mkdir(exist_ok=True)
        Path("./hosted").mkdir(exist_ok=True)
        #initial scan for files
        myfiles = [f for f in listdir(str(Path("./myFiles"))) if isfile(join(str(Path("./myFiles")), f))]
        hfiles = [f for f in listdir(str(Path("./hosted"))) if isfile(join(str(Path("./hosted")), f))]
        print(myfiles,'\n',hfiles)
        self.logging("Folders set \n myFiles : \n{}\nhosted : \n{}".format(myfiles,hfiles))
        return [myfiles, hfiles]

    def test(self):
        fpath=Path("./myFiles/test1.txt")
        print(self.sendChunks(fpath))

    def sendFile(self,peercon,filename):
        pck=''
        with open(Path("./hosted/"+filename),'rb') as file:
            pck=file.read()
        try:
            peercon.sendData('gtfl',pck,self.keys[peercon.peerguid],fil=True,guid=self.guid)
        except:
            self.logging('* Unable to send back requested file to {}'.format(peercon.peerguid))
        

    #--------------------------------------------------------------------------------------
    def sendChunks(self,filepath,progressbar=None):
    #--------------------------------------------------------------------------------------
        '''
        Uploads the file in chunks to the peers on the network
        '''
        totalSize = math.ceil((stat(filepath).st_size/self.chunkSize))*self.chunkSize
        fileHash = hashlib.sha1() #original file hash
        #fileID = str(uuid.uuid1()).replace('-','') #generate unique random id
        fileID = uuid.uuid1().int
        chunkSize=self.chunkSize
        order=0
        with open(filepath,'rb') as file:
            # loop till the end of the file
            cHashes=[]
            chunk = b' '
            dash='-'.encode('utf-8')
            chunk = file.read(chunkSize)
            while chunk :
                time.sleep(2)
                chunkID = str(uuid.uuid1()).replace('-','') #generate unique random id
                #chunk = file.read(chunkSize)
                chunkHash =  hashlib.sha1(chunk).hexdigest()
                #self.fileQueue[chunkID] = chunkHash #chunkID : chunkHash
                #cHashes.append(chunkHash)
                fileHash.update(chunk)
                #upload chunk here
                #a routing function must be implemented but for now lets randomize it
                tosend=chunkID.encode('utf-8')+dash+chunk
                rep=self.replicationFactor
                receivers=[]
                while rep>0:
                    done=False
                    #host , port='',''
                    while not done:
                        #resend if not acknowledged | may need to ommit this because tcp already does it under the hood
                        #to=random.randint(0,len(self.peers.keys())-1)
                        #print(1)
                        peer=self.route(rand=True)
                        if peer in receivers:
                            while peer in receivers:
                                peer=self.route(rand=True)
                        receivers.append(peer)
                        host , port =self.peers[peer]
                        key=self.keys[peer]
                        #code, reply = self.connectAndSend(host, port, 'upfl', tosend) #awaits a reply
                        #sendata(sock,'upfl',tosend,key,fil=True)
                        print(chunkID)
                        print("hh")
                        try:
                            #code , reply = recvdata(sock)
                            code , reply =self.connectAndSend(host, port, 'upfl', tosend,key=key,file=True) #awaits a reply
                        except Exception as e:
                            print(e)
                            print('here')
                            receivers.remove(peer)
                            continue
                        print('gg')
                        fid , ack = reply.split('-')
                        if code=='ackf' and fid==chunkID:
                            if ack == '1':
                                #issue chunck transaction here
                                #-------------------------
                                # bool issue_transaction(bool isChunk,string senderGUID,string receiverGUID,string chunkHash,string representationOfOriginalFile)
                                self.bNode.logChunkUpload(fileID,self.guid,peer,chunkHash,order)
                                print("chunk acknowledged")
                                #-------------------------
                                print(chunkID," ---ACK")
                                done = True 
                                rep-=1
                                #chunk = file.read(chunkSize)
                                #order+=1
                            else:
                                print('failed to send chunk')
                                done =  False
                receivers.clear()
                chunk = file.read(chunkSize)
                order+=1
                if progressbar:
                    progvalue = (order*100)//(totalSize//self.chunkSize)
                    progressbar.setValue(progvalue)
        fileHash = fileHash.hexdigest()
        #issue file transaction here 
        #-------------------------
        print("file uploaded")
        self.bNode.logFileUpload(fileID,basename(filepath),fileHash,(order)*self.chunkSize)
        #time.sleep(5)
        #myfile=self.bNode.filterByAddress()
        #myfiles = self.fetchMyFiles()
        #time.sleep(5)
        #self.bNode.logDeletion(fileID)
        #time.sleep(10)
        #self.bNode.filterByAddress()
        #self.downloadFile(myfiles[0]['fileName'],myfiles[0]['linkToOGF'])
        #-------------------------
        #self.myItems[basename(filepath)]={fileHash : cHashes}

        return [basename(filepath),fileID]










    #========================================================================================
   
   
    #--------------------------------------------------------------------------
    def get_key(self,value):
    #--------------------------------------------------------------------------
        for key, val in self.peers.items():
            if val==value:
                return key
        return None

    #--------------------------------------------------------------------------
    def save(self):
    #--------------------------------------------------------------------------
        try:
            Path("./data").mkdir(exist_ok=True)
            data={'guid':self.guid}
            filename=Path("./data/Node_data.txt")
            file = open(filename,'w') 
            file.write(json.dumps(data))
            file.close()
        except:
            self.logging("** {} could not be created".format(str(filename)))

    #--------------------------------------------------------------------------
    def loadData(self):
    #--------------------------------------------------------------------------
        try:
            filename=Path("./data/Node_data.txt")
            if filename.exists():
                file = open(filename,'r')
                content = file.read()
                data = json.loads(content)
                file.close()
                # set values for the node
                self.guid=data['guid']

                return True
            else:
                return False
        except Exception as e:
            print(e)
            self.logging("** Unable to load data")
            return False

    #--------------------------------------------------------------------------
    def run(self,command):
    #--------------------------------------------------------------------------
        """ 
        Run command with no output and return returncode 
        """
        res = subprocess.run(command,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT).returncode
        return res


    #--------------------------------------------------------------------------
    def setupFirewall(self,mainPort,gethPort):
    #--------------------------------------------------------------------------
        '''
        Creates Firewall rules for the mainPort(tcp in and  out) and for the gethPort (tcp in and  out, udp in and  out)
        '''
        rules=[
            'netsh advfirewall firewall show rule name= "A_test1" dir=in',
            'netsh advfirewall firewall add rule name= "A_test1" dir=in action=allow protocol=TCP localport={}'.format(str(mainPort)),
            'netsh advfirewall firewall show rule name= "A_test1" dir=out',
            'netsh advfirewall firewall add rule name= "A_test1" dir=out action=allow protocol=TCP remoteport={}'.format(str(mainPort)),
            'netsh advfirewall firewall show rule name= "A_test2T" dir=in',
            'netsh advfirewall firewall add rule name= "A_test2T" dir=in action=allow protocol=TCP localport={}'.format(str(gethPort)),
            'netsh advfirewall firewall show rule name= "A_test2T" dir=out',
            'netsh advfirewall firewall add rule name= "A_test2T" dir=out action=allow protocol=TCP remoteport={}'.format(str(gethPort)),
            'netsh advfirewall firewall show rule name= "A_test2U" dir=in',
            'netsh advfirewall firewall add rule name= "A_test2U" dir=in action=allow protocol=UDP localport={}'.format(str(gethPort)),
            'netsh advfirewall firewall show rule name= "A_test2U" dir=out',
            'netsh advfirewall firewall add rule name= "A_test2U" dir=out action=allow protocol=UDP remoteport={}'.format(str(gethPort))
            ]
        x=0
        isRuleA=False
        result=''
        for rule in rules:
            if not isRuleA:
                result=self.run(rule)
                isRuleA=False
            else:
                print("skipping")
                isRuleA=False
                continue
            if result ==0:
                if 'show' in rule:
                    isRuleA=True
                print('rule {} successfully applied'.format(x))   
            else:
                print('rule {} failed to apply'.format(x))
            x+=1

    #--------------------------------------------------------------------------
    def route(self,rand=False):
    #--------------------------------------------------------------------------
        '''
        Find an online peer and return his GUID
        '''
        if rand:
            peers = list(self.peers.keys())
            peers.sort()
            while True:
                test = random.randint(1,len(peers)-1)
                if (peers[test] != self.guid and self.connections[peers[test]][0]):
                    return peers[test]
                else:
                    self.logging('** GUID : {} is offline'.format(test))
                time.sleep(0.5)
        else:
            while True:
                #need to not return genesis guid (0)
                for GUID in self.peers:
                    if self.connections[GUID][0] and GUID!=0:
                        return GUID
                    else:
                        self.logging('** GUID : {} is offline'.format(GUID))
                time.sleep(2)

    def heartbeats(self):
        '''
        Sends HearBeat messages periodically 
        '''
        while True:
            
            for peer in self.peers:
                if peer != 0:
                    self.connections[peer]=self.testCon(peer)
            time.sleep(60)

    #--------------------------------------------------------------------------
    def testCon(self,target):
    #--------------------------------------------------------------------------
        '''
        Send Ping request to test connection
        '''
        try:
            t0=time.perf_counter_ns()
            #time.sleep(2)
            #send ping
            #recv pong
            ip , port = self.peers[target]
            code , msg = self.connectAndSend(ip,port,'ping','ping')
            if code=='ping' and msg=='pong':
                t1=(time.perf_counter_ns()-t0)//1000000
                return (True,t1)
            else:
                return (False,-2)
        except:
            return (False,-1)

    #--------------------------------------------------------------------------
    def setmyid( self, guid ):
    #--------------------------------------------------------------------------
	    self.guid = guid
    
    #--------------------------------------------------------------------------------------
    def broadcast(self,msgType,msgData,pid):
    #--------------------------------------------------------------------------------------
        for peer in self.peers :
            if peer != pid and peer!=self.guid and self.testCon(peer)[0]:
                time.sleep(0.5) #just to test
                ip , port = self.peers[peer]
                self.connectAndSend(ip,port,msgType,msgData,pId=peer,waitReply=False)

    #--------------------------------------------------------------------------------------
    def logging(self,error):
    #--------------------------------------------------------------------------------------
        '''
        function that is used to write to log files
        '''
        try:
            Path("./logs/p2p").mkdir(parents=True,exist_ok=True)
            filename=Path("./logs/p2p/"+self.startTime.replace(':','-')+".txt")
            file = open(filename,'a') 
            file.write("[{}] : ".format(datetime.datetime.now().strftime("%H:%M:%S"))+error+'\n') 
            file.close()
        except:
            print("{} could not be created".format(str(filename)))


    #--------------------------------------------------------------------------------------
    def peerLimitReached(self):
    #--------------------------------------------------------------------------------------
        if self.npeer == len(self.peers) or len(self.peers) > self.npeer :
            return True
        else:
            return False

    #--------------------------------------------------------------------------------------
    def addPeer(self,peerid,ip,port):
    #--------------------------------------------------------------------------------------
        if peerid not in self.peers :
            self.peers[peerid]=[ip,port]
            self.logging("{} peer was added with address {} and port {}".format(peerid,ip,port))
        else:
            old=self.peers[peerid]
            self.peers[peerid]=[ip,port]
            self.logging("Updated peer {} from {} ==> {}".format(peerid,old,[ip,port]))


    #--------------------------------------------------------------------------------------
    def createServerSocket(self):
    #--------------------------------------------------------------------------------------
        '''
        create a server socket from myip and port then listen
        '''
        try:
            inbound = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            inbound.bind((self.myip,self.port))
            inbound.listen()
            return inbound
        except :
            self.logging("* error in createServerSocket : on ip={} port={}".format(self.myip,self.port))
    

    #--------------------------------------------------------------------------------------
    def connectAndSend(self,host,port,msgType,msgData,key=None,file=False,pId=None,waitReply=True):
    #--------------------------------------------------------------------------------------
        '''
        connect and send message to specified peer
        '''
        #msgreply=[]
        try:
            peerconn=PeerConnection(host,port,self.startTime,peerguid=pId,Keys=self.keys)
            if not key:
                peerconn.sendData(msgType,msgData)
            else:
                peerconn.sendData(msgType,msgData,key=key,fil=file,guid=self.guid)
            if msgType=='upfl':
                self.logging("Sent {} to peerid : {}".format(msgType,pId))
            else:
                self.logging("Sent {}-{} to peerid : {}".format(msgType,msgData,pId))

            if waitReply:
                onereply=peerconn.recvdata() #this caters to onereply only
                '''while (onereply != (None,None)):
                    msgreply.append(onereply)
                    self.logging("Got a reply from peerid : {}".format(pId))
                    onereply=peerconn.recvdata()# may need to delete'''
                peerconn.close()
                self.logging("Received reply from {}".format(host))
                return onereply
            else:
                #time.sleep(2) #for testing
                peerconn.close()
        except:
            self.logging("* Could not connect and send to {} : {} on {}".format(pId,host,port))
        


    #--------------------------------------------------------------------------------------
    def handlePeer(self,clientSocket):
    #--------------------------------------------------------------------------------------
        host , port = clientSocket.getpeername()
        self.logging("* Connection to {} has been esstablished".format(str((host,port))))
        '''
        handle peer depending request/ProtocolCode
        '''
        peerconn = PeerConnection(host,port,self.startTime,sock=clientSocket,Keys=self.keys)

        try:
            protocolCode , data = peerconn.recvdata()
            if protocolCode : 
                protocolCode = protocolCode.upper()
                
            if protocolCode in self.protocol :
                self.protocol[protocolCode](peerconn , data)
            else :
                self.logging("{} code not recognized ".format(protocolCode))
        except Exception as e:
            print(e)
            self.logging("* error while handeling peer {}:{} with code {}".format(host,port,protocolCode))
            
        #may need to keep open
        self.logging("Closing connection with {} : {}".format(host , port))
        peerconn.close()


    #--------------------------------------------------------------------------------------
    def connectionSpawner(self):
    #--------------------------------------------------------------------------------------
        self.setupFirewall(self.port,30305)
        self.setup()
        inbound=self.createServerSocket()
        #inbound.settimeout(70)# this line could be deleted to avoid possible problems 
        print("started listening on port : ",self.port)
        self.logging("started listening on port : {}".format(self.port))
        '''
        this function spwanes inbound connections and sends them off to be handled in threads
        '''
        while not self.turnoff:
            try:
                clientSocket , address = inbound.accept()
                thred=threading.Thread(target=self.handlePeer,args=[clientSocket],daemon=True)
                #uses daemon thread to be able to test, in real application proccess will keep running in background after program closes
                thred.start()
            except :
                self.logging("* error in connectionsSpawner : was not able to spawn a connection to {}".format(address))
                continue
        
        inbound.close()


#==========================================================================================
class PeerConnection:

    #--------------------------------------------------------------------------------------
    def __init__(self,peerip,port,start,sock=None,peerguid=None,Keys=None):
    #--------------------------------------------------------------------------------------

        self.peerguid=peerguid 
        self.peerip=peerip
        self.port=int(port)
        self.start=start
        self.Keys=Keys
        '''
        if socket not available create it and connect
        '''
        if not sock:
            try:
                self.sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                self.sock.connect((self.peerip,self.port))
            except:
                self.logging("* peercon could not connect to {} on {}".format(self.peerip,self.port))
        else:
            self.sock=sock
    

    #--------------------------------------------------------------------------------------
    def logging(self,error):
    #--------------------------------------------------------------------------------------
        '''
        function that is use to write to log files
        '''
        try:
            Path("./logs/p2p").mkdir(parents=True ,exist_ok=True)
            filename=Path("./logs/p2p/"+self.start.replace(':','-')+".txt")
            file = open(filename,'a') 
            file.write("[{}] : ".format(datetime.datetime.now().strftime("%H:%M:%S"))+error+'\n') 
            file.close()
        except:
            self.logging("* {} could not be created".format(str(filename)))


    #--------------------------------------------------------------------------------------   
    def setPeerGuid(self,guid):
    #--------------------------------------------------------------------------------------
        self.peerguid=guid
    

    #--------------------------------------------------------------------------------------
    def forgeMessage(self,msgType,msgData):
    #--------------------------------------------------------------------------------------
        #The network byte order is defined to always be big-endian (>)
        msg="-".join([msgType,msgData])
        return msg.encode("utf-8")

    #--------------------------------------------------------------------------------------
    def encrypt(self,key,to_encrypt):
    #--------------------------------------------------------------------------------------
        cipher=AES.new(key,AES.MODE_EAX)
        nonce = cipher.nonce
        ciphertext, tag = cipher.encrypt_and_digest(to_encrypt)
        return (ciphertext,nonce,tag)

    #--------------------------------------------------------------------------------------
    def decrypt(self,key ,nonce,to_decrypt):
    #--------------------------------------------------------------------------------------
        cipher=AES.new(key,AES.MODE_EAX,nonce=nonce)
        plaintext=cipher.decrypt(to_decrypt)
        return plaintext

    #--------------------------------------------------------------------------------------
    def sendData(self,msgType,msgData,key=None,fil=False,guid=None):
    #--------------------------------------------------------------------------------------

        '''
        send msg and return true on success 
        '''
        try:
            
            if key:
                if not fil:
                    msg=msgData.encode('utf-8')
                    msg,nonce,tag = self.encrypt(key,msg)
                    dash='-'.encode('utf-8')
                    shi='[]'.encode('utf-8')
                    self.sock.sendall((msgType+'_'+str(guid)).encode('utf-8')+dash+msg+shi+nonce)
                else:
                    #print("content : ",msgData)
                    msg,nonce,tag = self.encrypt(key,msgData)
                    dash='-'.encode('utf-8')
                    shi='[]'.encode('utf-8')
                    #print(msg)
                    #print("size : ",sys.getsizeof(msg))
                    self.sock.sendall((msgType+'_'+str(guid)).encode('utf-8')+dash+msg+shi+nonce)
                    #print((msgType+'_'+str(guid)).encode('utf-8')+dash+msg+shi+nonce)
                    print("total size : ",sys.getsizeof(msgType.encode('utf-8')+dash+msg+dash+nonce))
                    print("sent chunck")
            else:
                msg=self.forgeMessage(msgType,msgData)
                self.sock.sendall(msg)
        except Exception as e:
            print(e)
            self.logging("* failed to send data from {} on {}".format(self.peerip,self.port))
            return False
        return True


   
    #--------------------------------------------------------------------------------------    
    def recvdata(self,key=None):
    #--------------------------------------------------------------------------------------
        try:
            received=self.sock.recv(4096)
            #print("Received:")
            #print(received)
            try:
                code,data=received.split('-'.encode('utf-8'),1)
                #print(code)
                #print(data)
                code = code.decode('utf-8')
                guid=''
                if '_' in code:
                    code,guid=code.split('_',1)
                    guid=int(guid)
                    self.peerguid=guid
                    print(guid)

                if code =='upfl':
                    size=sys.getsizeof(received)
                    print("size received",sys.getsizeof(received))
                    while True:
                        try:
                            self.sock.settimeout(0.7)
                            received+=self.sock.recv(4096)
                            size=sys.getsizeof(received)
                        except socket.timeout:
                            self.sock.settimeout(None)
                            break

                    #print("received : ",received)
                    code,data=received.split('-'.encode('utf-8'),1)
                    code = code.decode('utf-8')
                    if '_' in code:
                        code,guid=code.split('_',1)
                        guid=int(guid)
                        print(guid)

                    shi='[]'.encode('utf-8')
                    stuff=data.split(shi)
                    msg=self.decrypt(self.Keys[guid],stuff[-1],stuff[0])
                    msg =msg.split('-'.encode('utf-8'),1)
                    #print(msg)
                    return (code,msg)
                else:
                    stuff=data.split('[]'.encode('utf-8'))
                    #print(">-",stuff)
                    try:
                        mg=stuff[-1].decode('utf-8','strict')
                        #print('----------')
                        return (code,data.decode('utf-8'))
                    except UnicodeDecodeError:
                        msg=self.decrypt(self.Keys[guid],stuff[-1],stuff[0])
                        #print(msg)
                        if code!='gtfl':
                            msg=msg.decode('utf-8')
                        #print(msg)
                        return (code,msg)    
            except Exception as e:
                print(e)
        except:
            self.logging("* failed to receive data from {} on {}".format(self.peerip,self.port))


    #--------------------------------------------------------------------------------------
    def close(self):
    #--------------------------------------------------------------------------------------
        '''
        close the connection , sendData and recvdate wont work after this
        '''
        self.sock.close()
        self.sock=None


    def __str__(self):
        return "|%s|" % self.peerguid