'''
import RPi.GPIO as GPIO
import time

class DoorBell:

    GPIO_STATUS = 1
    GPIO_LED_PWR = 2
    GPIO_LED_GOOD = 3
    GPIO_LED_BUSY = 4
    GPIO_BUZZER = 5

    def __init__(self):

        GPIO.setup(DoorBell.GPIO_STATUS, GPIO.INPUT_PULLUP)

'''


import socket
import time
import random


class DoorCodes:
    NOTHING = b"nodata"
    ALARM = b"getfuckingdoorucunts"


UDP_IP = "192.168a.0.255"
UDP_PORT = 5005

MESSAGE = b"Hello World "

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

while 1:

    MESSAGE = DoorCodes.NOTHING

    rnd = random.randint(0,20)

    if rnd == 0:
        MESSAGE = DoorCodes.ALARM
        print("ALARM")

    sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
    time.sleep(1)





