import threading
import datetime
from pathlib import Path
import time
import subprocess
from p2p_G import Node
from blockchain_G import bcNode

subprocess.run('cls', shell=True)
print("Test Environment Setup Script")

#Obtain IP and Port
ip = input('[Script Output] IP: ') #providing your ip (if in lan local otherwise public)
port =4444 #eval(input("[Script Output] Port: ")) # Port dedicated for the P2P network
subprocess.run('cls', shell=True)

#Check if genesis
""" isGenesis = True if input("[Script Output] Is genesis? (y/n): ") ==  'y' else False
print("isGenesis = ", isGenesis) """

#Initialize blockchain node
bc_Node = bcNode(ip)

#Initialize p2p node
myNode = Node(ip, port,bc_Node, npeer=10)

#if(isGenesis):
#Start listening for any connection/request 
myNode.connectionSpawner()

""" else:
    print('[Script Output] Enter Node info to connect to \n')
    hip = input("[Script Output] Target IP: ")
    hport = eval(input("[Script Output] Target Port: "))
    # prepare join request arguments 
    tosend='-'.join([ip,str(port)])
    # start listening on provided port
    thread=threading.Thread(target=myNode.connectionSpawner,args=[])
    thread.start()
    #send join request
    myNode.connectAndSend(hip,hport,'join',tosend,waitReply=False) """