
import RPi.GPIO as GPIO
import time
import socket
import threading

class Networking:
    UDP_IP = "192.168a.0.255"
    UDP_PORT = 5005

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    def init():
        Networking.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def alarm():
        Networking.sock.sendto(MESSAGE, (Networking.UDP_IP, Networking.UDP_PORT))


class DoorCodes:
    NOTHING = b"nodata"
    ALARM = b"getfuckingdoorucunts"


class GPIOSignal:

    _alarm_stop_event = threading.Event()

    class LED:
        RED = 17
        BLUE = 22
        GREEN = 27

    BEEPER = 23
    BUTTON = 24

    def init():
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(GPIOSignal.BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(GPIOSignal.BEEPER, GPIO.OUT)

        GPIO.setup(GPIOSignal.LED.RED, GPIO.OUT)
        GPIO.setup(GPIOSignal.LED.BLUE, GPIO.OUT)
        GPIO.setup(GPIOSignal.LED.GREEN, GPIO.OUT)

        GPIO.output(GPIOSignal.BEEPER, GPIO.LOW)
        GPIO.output(GPIOSignal.LED.RED, GPIO.HIGH)
        GPIO.output(GPIOSignal.LED.BLUE, GPIO.LOW)
        GPIO.output(GPIOSignal.LED.GREEN, GPIO.LOW)
        

    def _alarm_beeper_thread():
        
        for i in range(5):
            GPIO.output(GPIOSignal.BEEPER, GPIO.HIGH)
            time.sleep(0.1)
            GPIO.output(GPIOSignal.BEEPER, GPIO.LOW)
            time.sleep(0.1)
        
        GPIOSignal._alarm_stop_event.set()

    
    def _alarm_LED_thread():
        
        GPIO.output(GPIOSignal.LED.RED, GPIO.LOW)

        while not GPIOSignal._alarm_stop_event.is_set():
            GPIO.output(GPIOSignal.LED.BLUE, GPIO.HIGH)
            time.sleep(0.05)
            GPIO.output(GPIOSignal.LED.BLUE, GPIO.LOW)
            time.sleep(0.05)
        
        GPIO.output(GPIOSignal.LED.RED, GPIO.HIGH)
    

    def alarm():
        t_beeper = threading.Thread(target=GPIOSignal._alarm_beeper_thread)
        t_LED = threading.Thread(target=GPIOSignal._alarm_LED_thread)
        t_beeper.start()
        t_LED.start()
        t_beeper.join()
        t_LED.join()
        GPIOSignal._alarm_stop_event.clear()





def init():
    GPIOSignal.init()
    Networking.init()



def loop():
    time.sleep(0.1)
    
    if GPIO.input(GPIOSignal.BUTTON) == GPIO.LOW:

        GPIOSignal.alarm()



if __name__ == "__main__":
    init()
    while 1:
        loop()


