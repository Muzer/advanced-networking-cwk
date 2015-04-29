'''
Created on 15 Apr 2015

@author: alex
'''
import json
import socket
import time
import calendar

import netifaces #may need sudo apt-get install python-netifaces

#it's over 9000! and isn't listed as on the wikipedia ports page, so will probably be free
MSG_PORT = 9003
NAME_PORT = 9005
#values or tags for use in json message encoding
TYPE = "type"
SENDER = "sender"
BODY = "body"
MESSAGE = "message"
NAMING = "naming"
USERNAME = "username"
IDENTIFIER = "identifier"

LOOP_TIME = 5
MAX_LOOPS = 4

# from http://stackoverflow.com/a/24196955
def get_ip_address(ifname):
    addr = netifaces.ifaddresses(ifname)[socket.AF_INET][0]['addr']
    return addr
    
def get_bc_address(ifname):
    addr = netifaces.ifaddresses(ifname)[socket.AF_INET][0]['broadcast']
    return addr

def broadcastName(username,myIP,bcIP):
    "send the username to everyone on the network"
    data = json.dumps({TYPE:NAMING, USERNAME:username, IDENTIFIER:myIP}) + '\n'
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #s.bind(("192.168.42.255", 9006))
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.sendto(data,(bcIP, NAME_PORT))
    s.close()
    return

def unicastName(username,recipientID,myIP):
    "send the username to one person on the network"
    data = json.dumps({TYPE:NAMING, USERNAME:username, IDENTIFIER:myIP})
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((myIP, 9006))
    s.sendto(data,(recipientID, NAME_PORT))
    s.close()
    return

def sendMessage(senderName, message, destinationIP, myIP, username):
    data = json.dumps({TYPE:MESSAGE, SENDER:senderName, BODY:message, USERNAME:username})
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((myIP, 9004))
    s.sendto(data,(destinationIP, MSG_PORT))
    s.close()
    return

def timeOuter(nameTimeMap,myName,myIP,bcIP):
    while True:
        broadcastName(myName, myIP, bcIP)
        now = calendar.timegm(time.gmtime())
        toRemove = set()
        for name in nameTimeMap.iterkeys():
            nameTime = nameTimeMap.get(name)
            if now > nameTime + (LOOP_TIME * MAX_LOOPS):
                toRemove.add(name)
        for name in toRemove:
            nameTimeMap.pop(name)
            print(name + " removed")
        time.sleep(LOOP_TIME)
    return

def nameListener(nameLocatorMap, nameTimeMap, bcIP, router=False, nlmZigbee=None, zigbeeMod=None, zigbee=None, myAddr=None, bcAddr=None, myName=None):
    #build a listener
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((bcIP,NAME_PORT))
    print("listening for names")
    while True:
        #wait for a connection and read it
        data, addr = s.recvfrom(1024)
        #process it
        jData = json.loads(data)
        if jData.has_key(TYPE):
            msgType = jData.get(TYPE)
            if msgType == NAMING:
                #if its a name update, store it
                if jData.has_key(USERNAME) and jData.has_key(IDENTIFIER):
                    username = jData.get(USERNAME)
                    identifier = jData.get(IDENTIFIER)
                    if router and username in nlmZigbee.keys():
                        continue
                    if username not in nameLocatorMap.keys():
                        print(username + " (" + identifier + ") has joined the chat")
                    #store the name
                    nameLocatorMap[username] = identifier
                    #store time received
                    nameTimeMap[username] = calendar.timegm(time.gmtime())
                    #Broadcast over bridge
                    if router and username != myName and not nlmZigbee.has_key(username):
                        zigbeeMod.broadcastName(zigbee, username, myAddr, bcAddr)
                else:
                    print("Unable to read name")
            else:
                print("unknown message type")

        
    print("Name listener failed. Restart program")    
    return

def messageListener(nameLocatorMap, myIP, router=False, nlmZigbee=None, zigbeeMod=None, zigbee=None, myAddr=None, myName=None):
    #build a listener
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((myIP,MSG_PORT))
    print("listening for messages")
    while True:
        #wait for a connection and read it
        data, addr = s.recvfrom(1024)
        #process it
        jData = json.loads(data)
        if jData.has_key(TYPE):
            msgType = jData.get(TYPE)
            if msgType == MESSAGE:
                #if its a message, print it
                if jData.has_key(SENDER) and jData.has_key(BODY):
                    senderName = jData.get(SENDER)
                    message = jData.get(BODY)
                    username = jData.get(USERNAME)
                    if (not router) or (username == myName):
                        print(senderName + ": " + message)
                    else:
                        if nlmZigbee.has_key(username):
                            zigbeeMod.sendMessage(zigbee, senderName, message, nlmZigbee.get(username), myAddr, username)
                        else:
                            print("Username '" + username + "' is not registered")
                else:
                    print("Unable to read message")
            else:
                print("unknown message type")

        
    print("Message listener failed. Restart program")    
    return
