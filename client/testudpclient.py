import socket
import time

class DoorCodes:
    NOTHING = b"nodata"
    ALARM = b"getfuckingdoorucunts"

UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", UDP_PORT))

while 1:
    data, addr = sock.recvfrom(1024)


    if data == DoorCodes.NOTHING:
        print("flash led")
    
    if data == DoorCodes.ALARM:
        print("BEEP BEEP BEEP")
        time.sleep(1)


