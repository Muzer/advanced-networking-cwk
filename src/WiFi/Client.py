'''
Created on 14 Apr 2015
@author: alex
'''
from comms import get_bc_address, messageListener, timeOuter, nameListener, sendMessage, broadcastName, get_ip_address
import thread

username = raw_input("What is your name? ")
#socket.gethostname()
nameLocatorMap = {}#"pi":"192.168.42.1"
nameTimeMap = {}
#start process updating naming map
interface = 'wlan0'
myIP = get_ip_address(interface)
bcIP = get_bc_address(interface)
print(myIP)
#nameLocatorMap[username] = myIP
thread.start_new_thread(messageListener, (nameLocatorMap,myIP,))
thread.start_new_thread(nameListener, (nameLocatorMap,nameTimeMap,bcIP,))
thread.start_new_thread(timeOuter, (nameLocatorMap,nameTimeMap,username,myIP,bcIP,))
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
    sendMessage(username,data,nameLocatorMap.get(recipient),myIP, recipient)
    
