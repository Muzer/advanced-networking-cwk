'''
Created on 14 Apr 2015
@author: alex
'''
from comms import listener, timeOuter, sendMessage, broadcastName, get_address
import thread
import xbee
import serial

username = raw_input("What is your name? ")
nameLocatorMap = {}
nameTimeMap = {}
#start process updating naming map
serialStr = '/dev/ttyUSB0'
serialPort = serial.Serial(serialStr, 9600)
zigbee = xbee.ZigBee(serialPort)


myAddr = get_address(zigbee)
bcAddr = 0x000000000000FFFF
print(myAddr)
#nameLocatorMap[username] = myIP
thread.start_new_thread(listener, (zigbee, nameLocatorMap,nameTimeMap,bcAddr,myAddr))
thread.start_new_thread(timeOuter, (zigbee, nameLocatorMap,nameTimeMap, username,myAddr,bcAddr))
#start process timing out name mappings

while True:
    print
    recipient = raw_input("Send message to: ")
    
    # check recipient name is registered
    if not nameLocatorMap.has_key(recipient):
        print("Username '" + recipient + "' is not registered")
        continue
    
    data = raw_input("Message for " + recipient + ": ")
    # send message
    sendMessage(zigbee,username,data,nameLocatorMap.get(recipient),myAddr, recipient)
