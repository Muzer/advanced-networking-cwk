'''
Created on 14 Apr 2015
@author: alex
'''
import zigbee.comms
import WiFi.comms
import thread
import serial
import xbee

username = raw_input("What is your name? ")
#socket.gethostname()
nameLocatorMapWiFi = {}#"pi":"192.168.42.1"
nameLocatorMapZigbee = {}#"pi":"192.168.42.1"
nameTimeMapWiFi = {}
nameTimeMapZigbee = {}
#start process updating naming map
interface = 'wlan0'
myIP = WiFi.comms.get_ip_address(interface)
bcIP = WiFi.comms.get_bc_address(interface)
print(myIP)
serialStr = '/dev/ttyUSB0'
serialPort = serial.Serial(serialStr, 9600)
zbee = xbee.ZigBee(serialPort)

myAddr = zigbee.comms.get_address(zbee)
bcAddr = 0x000000000000FFFF
#nameLocatorMap[username] = myIP
thread.start_new_thread(WiFi.comms.messageListener, (nameLocatorMapWiFi,myIP,True,nameLocatorMapZigbee,zigbee.comms, zbee, myAddr, username))
thread.start_new_thread(WiFi.comms.nameListener, (nameLocatorMapWiFi,nameTimeMapWiFi,bcIP,True,nameLocatorMapZigbee,zigbee.comms,zbee,myAddr,bcAddr, username))
thread.start_new_thread(zigbee.comms.listener, (zbee, nameLocatorMapZigbee,nameTimeMapZigbee,bcAddr,myAddr,True,nameLocatorMapWiFi,WiFi.comms, myIP, bcIP, username))
thread.start_new_thread(WiFi.comms.timeOuter, (nameLocatorMapWifi, nameTimeMapWiFi, username,myIP,bcIP,))
thread.start_new_thread(zigbee.comms.timeOuter, (zbee, nameLocatorMapZigbee, nameTimeMapZigbee, username,myAddr,bcAddr))
#start process timing out name mappings

while True:
    print
    recipient = raw_input("Send message to: ")
    
    # check recipient name is registered
    if nameLocatorMapWiFi.has_key(recipient):
        data = raw_input("Message for " + recipient + ": ")
        # send message
        WiFi.comms.sendMessage(username,data,nameLocatorMapWiFi.get(recipient),myIP, recipient)
    elif nameLocatorMapZigbee.has_key(recipient):
        data = raw_input("Message for " + recipient + ": ")
        # send message
        zigbee.comms.sendMessage(zbee, username,data,nameLocatorMapZigbee.get(recipient),myAddr, recipient)
    else:
        print("Username '" + recipient + "' is not registered")
        continue
    
    
