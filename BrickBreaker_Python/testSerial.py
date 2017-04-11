# -*- coding: cp1252 -*-
import time
import serial


serConnection = serial.Serial()
serConnection.port="COM1"
serConnection.baudrate=9600
serConnection.parity=serial.PARITY_NONE
serConnection.stopbits=serial.STOPBITS_ONE
serConnection.bytesize=serial.EIGHTBITS

try: 
    serConnection.open()
except Exception, e:
    print "error open serial port: " + str(e)
    exit()

if serConnection.isOpen():
    print "el puerto está abierto"

print("Application running...")
def tweet_message(message):
    time.sleep(1)


while(True):
    #print("Awaiting serial input...")

    message = ""
    #print("El tamaño del mensaje es:" +serConnection.in_waiting())
    while serConnection.inWaiting() > 0:
        message = serConnection.read(1)
    if message != "":
        print(message)


    time.sleep(.02)
