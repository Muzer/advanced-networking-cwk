'''
Created on 15 Apr 2015

@author: alex
'''
import json
import time
import calendar
import struct


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

def get_frame(zigbee, name):
    while True:
        frame = zigbee.wait_read_frame()
        if frame["id"] != name:
            continue
        return frame

def get_address(zigbee):
    # First, wait for the XBee to join a network
    print("Waiting for network...")
    while True:
        zigbee.at(command='MY')
        my = get_frame(zigbee, 'at_response')["parameter"]
        if my != '\xff\xfe':
            break
        time.sleep(LOOP_TIME)
    print("Got network.")
    zigbee.at(command='SH')
    sh = struct.unpack(">L", get_frame(zigbee, 'at_response')["parameter"])[0]
    zigbee.at(command='SL')
    sl = struct.unpack(">L", get_frame(zigbee, 'at_response')["parameter"])[0]
    return (sh << 32) + sl
    
def broadcastName(zigbee, username,myAddr,bcAddr):
    "send the username to everyone on the network"
    data = json.dumps({TYPE:NAMING, USERNAME:username, IDENTIFIER:myAddr}) + '\n'
    zigbee.send("tx", dest_addr_long=struct.pack(">Q", bcAddr), dest_addr='\xff\xfe', data=data)
    return

def unicastName(zigbee, username,recipientID,myAddr):
    "send the username to one person on the network"
    data = json.dumps({TYPE:NAMING, USERNAME:username, IDENTIFIER:myAddr})
    zigbee.send("tx", dest_addr_long=struct.pack(">Q", recipientID), dest_addr='\xff\xfe', data=data)
    return

def sendMessage(zigbee, senderName, message, destinationAddr, myAddr, username):
    data = json.dumps({TYPE:MESSAGE, SENDER:senderName, BODY:message, USERNAME:username})
    zigbee.send("tx", dest_addr_long=struct.pack(">Q", destinationAddr), dest_addr='\xff\xfe', data=data)
    return

def timeOuter(zigbee, nameTimeMap,myName,myAddr,bcAddr):
    while True:
        broadcastName(zigbee, myName, myAddr, bcAddr)
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

def listener(zigbee, nameLocatorMap, nameTimeMap, bcAddr, myAddr, router=False, nlmWiFi=None, WiFiMod=None, myIP=None, bcIP=None, myName=None):
    #build a listener
    print("listening for names/messages")
    while True:
        #wait for a connection and read it
        frame = get_frame(zigbee, 'rx')
        #process it
        jData = json.loads(frame["rf_data"])
        if jData.has_key(TYPE):
            msgType = jData.get(TYPE)
            if msgType == NAMING:
                #if its a name update, store it
                if jData.has_key(USERNAME) and jData.has_key(IDENTIFIER):
                    username = jData.get(USERNAME)
                    identifier = jData.get(IDENTIFIER)
                    if username not in nameLocatorMap.keys():
                        print(username + " (" + str(identifier) + ") has joined the chat")
                    #store the name
                    nameLocatorMap[username] = identifier
                    #store time received
                    nameTimeMap[username] = calendar.timegm(time.gmtime())
                    if router and myName != username and not nlmWiFi.has_key(username):
                        WiFiMod.broadcastName(username, myIP, bcIP)
                else:
                    print("Unable to read name")
            elif msgType == MESSAGE:
                #if its a message, print it
                if jData.has_key(SENDER) and jData.has_key(BODY):
                    senderName = jData.get(SENDER)
                    message = jData.get(BODY)
                    username = jData.get(USERNAME)
                    if (not router) or (username == myName):
                        print(senderName + ": " + message)
                    else:
                        if nlmWiFi.has_key(username):
                            WiFiMod.sendMessage(senderName, message, nlmWiFi.get(username), myIP, username)
                        else:
                            print("Username '" + username + "' is not registered")
                else:
                    print("Unable to read message")
            else:
                print("unknown message type")


    print("Listener failed. Restart program")    
    return
