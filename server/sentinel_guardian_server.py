
import RPi.GPIO as GPIO
import time
import socket
import threading
import struct
import atexit
import signal

g_EVENT_STOP_ALARM = threading.Event()
g_EVENT_USER_CANCELLED = threading.Event()
g_ALARM_IN_PROGRESS = threading.Event()


def cleanup():
	GPIO.cleanup()



class GPIOSignal:

	class LED:
		RED = 17
		BLUE = 22
		GREEN = 27

	BEEPER = 23
	BUTTON = 24


	@staticmethod
	def init():

		print("[DEBUG] GPIOSignal.init() - setting GPIO mode to BCM")
		GPIO.setmode(GPIO.BCM)

		print("[DEBUG] GPIOSignal.init() - setup button")
		GPIO.setup(GPIOSignal.BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.add_event_detect(GPIOSignal.BUTTON, GPIO.FALLING, callback=alarm, bouncetime=100)

		print("[DEBUG] GPIOSignal.init() - setup beeper & LEDs")
		GPIO.setup(GPIOSignal.BEEPER, GPIO.OUT)
		GPIO.setup(GPIOSignal.LED.RED, GPIO.OUT)
		GPIO.setup(GPIOSignal.LED.BLUE, GPIO.OUT)
		GPIO.setup(GPIOSignal.LED.GREEN, GPIO.OUT)

		GPIO.output(GPIOSignal.BEEPER, GPIO.LOW)
		GPIO.output(GPIOSignal.LED.RED, GPIO.LOW)
		GPIO.output(GPIOSignal.LED.BLUE, GPIO.LOW)
		GPIO.output(GPIOSignal.LED.GREEN, GPIO.LOW)

		print("[DEBUG] GPIOSignal.init() - setup done")


	@staticmethod
	def _play_beep_pattern():
		print("[DEBUG] GPIOSignal._play_beep_pattern() - beeper started")
		for i in range(5):
			GPIO.output(GPIOSignal.BEEPER, GPIO.HIGH)
			time.sleep(0.1)
			GPIO.output(GPIOSignal.BEEPER, GPIO.LOW)
			time.sleep(0.1)

		print("[DEBUG] GPIOSignal._play_beep_pattern() - beeper stopped")


	@staticmethod
	def _play_blink_pattern():

		GPIO.output(GPIOSignal.LED.RED, GPIO.LOW)
		ts_start = time.time()

		print("[DEBUG] GPIOSignal._play_blink_pattern() - blink started")

		while (
			(not g_EVENT_STOP_ALARM.is_set()) and
			(not g_EVENT_USER_CANCELLED.is_set()) and
			(time.time() - ts_start < 20.0)):

			GPIO.output(GPIOSignal.LED.BLUE, GPIO.HIGH)
			time.sleep(0.05)
			GPIO.output(GPIOSignal.LED.BLUE, GPIO.LOW)
			time.sleep(0.45)

		print("[DEBUG] GPIOSignal._play_blink_pattern() - blink stopped")

		print("[DEBUG] GPIOSignal._play_blink_pattern() - g_EVENT_STOP_ALARM.set()")
		g_EVENT_STOP_ALARM.set()


	@staticmethod
	def _alarm():

		print("[DEBUG] GPIOSignal._alarm() - setting up threads")
		t_beeper = threading.Thread(target=GPIOSignal._play_beep_pattern)
		t_LED = threading.Thread(target=GPIOSignal._play_blink_pattern)
		print("[DEBUG] GPIOSignal._alarm() - starting threads")
		t_beeper.start()
		t_LED.start()
		print("[DEBUG] GPIOSignal._alarm() - awaiting threads")
		t_beeper.join()
		t_LED.join()
		print("[DEBUG] GPIOSignal._alarm() - threads complete")

		GPIO.output(GPIOSignal.BEEPER, GPIO.LOW)
		GPIO.output(GPIOSignal.LED.BLUE, GPIO.LOW)

		# todo: handle red/green signal for 20s
		if g_EVENT_USER_CANCELLED.is_set():
			GPIO.output(GPIOSignal.LED.GREEN, GPIO.HIGH)
		else:
			GPIO.output(GPIOSignal.LED.RED, GPIO.HIGH)

		print("[DEBUG] GPIOSignal._alarm() - response LED set")
		time.sleep(20)

		print("[DEBUG] GPIOSignal._alarm() - LEDs turned off")
		GPIO.output(GPIOSignal.LED.RED, GPIO.LOW)
		GPIO.output(GPIOSignal.LED.BLUE, GPIO.LOW)
		GPIO.output(GPIOSignal.LED.GREEN, GPIO.LOW)

		print("[DEBUG] GPIOSignal._alarm() - clear all 3 events")
		g_EVENT_STOP_ALARM.clear()
		g_EVENT_USER_CANCELLED.clear()
		g_ALARM_IN_PROGRESS.clear()


	def alarm():
		threading.Thread(target=GPIOSignal._alarm, daemon=True).start()



class Networking:
	BROADCAST_IP = "192.168.0.255"
	BROADCAST_PORT = 5005
	LISTEN_PORT = 5006

	CODE_ALARM = b"A"
	CODE_CANCEL = b"C"


	@staticmethod
	def send_alarm(timestamp):
		print("[DEBUG] Networking.send_alarm() - sending alarm")
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		packet = struct.pack("!I", int(timestamp)) + Networking.CODE_ALARM
		sock.sendto(packet, (Networking.BROADCAST_IP, Networking.BROADCAST_PORT))
		sock.close()
		print("[DEBUG] Networking.send_alarm() - socket closed")

	
	@staticmethod
	def send_cancel():
		print("[DEBUG] Networking.send_cancel() - sending cancel")
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		packet = struct.pack("!I", int(0)) + Networking.CODE_CANCEL
		sock.sendto(packet, (Networking.BROADCAST_IP, Networking.BROADCAST_PORT))
		sock.close()
		print("[DEBUG] Networking.send_cancel() - socket closed")


	@staticmethod
	def _listen_for_cancel(sock):
		print("[DEBUG] Networking._listen_for_cancel() - setting up socket")
		sock.settimeout(0.5)
		sock.bind(("0.0.0.0", Networking.LISTEN_PORT))
		print("[DEBUG] Networking._listen_for_cancel() - running listener loop")
		while not (g_EVENT_STOP_ALARM.is_set() or g_EVENT_USER_CANCELLED.is_set()):
			try:
				data, addr = sock.recvfrom(128)
				print("[DEBUG] Networking._listen_for_cancel() - recieved data")

				if data == Networking.CODE_CANCEL:
					print("[DEBUG] Networking._listen_for_cancel() - CANCEL recieved")
					print("[DEBUG] Networking._listen_for_cancel() - setting g_EVENT_USER_CANCELLED")
					g_EVENT_USER_CANCELLED.set()
					 

			except socket.timeout:
				continue
			except OSError:
				print("[DEBUG] Networking._listen_for_cancel() - OSError")
				break # socket closed

		


	@staticmethod
	def _alarm():
		ts_start = int(time.time())

		# start listener
		print("[DEBUG] Networking._alarm() - setting up socket")
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		listener = threading.Thread(
			target=Networking._listen_for_cancel,
			args=(sock, ),
			daemon=True
		)
		listener.start()
		print("[DEBUG] Networking._alarm() - started listener thread")

		while not (g_EVENT_STOP_ALARM.is_set() or g_EVENT_USER_CANCELLED.is_set()):
			
			print("[DEBUG] Networking._alarm() - sending alarm")
			Networking.send_alarm(ts_start)
			print("[DEBUG] Networking._alarm() - sent alarm")
			

			# do a 5s sleep, but more responsive to the event
			for i in range(10):
				time.sleep(0.5)
				if g_EVENT_STOP_ALARM.is_set() or g_EVENT_USER_CANCELLED.is_set():
					print("[DEBUG] Networking._alarm() - a g_EVENT is set. Breaking sleep loop")
					break

		sock.close()
		print("[DEBUG] Networking._alarm() - socket closed")
		listener.join()
		print("[DEBUG] Networking._alarm() - listener thread complete")

		print("[DEBUG] Networking._alarm() - sending cancel")
		Networking.send_cancel()
		print("[DEBUG] Networking._alarm() - sent cancel")


	@staticmethod
	def alarm():
		threading.Thread(target=Networking._alarm, daemon=True).start()



g_ALARM_MUTEX = threading.Lock()
def alarm(channel=None):

	print("[DEBUG] alarm() - function called")
	if g_ALARM_IN_PROGRESS.is_set():
		print("[DEBUG] alarm() - function returned due to alarm already in progress")
		return

	if not g_ALARM_MUTEX.acquire(blocking=False):
		print("[DEBUG] alarm() - function returned as mutex cannot be taken")
		return

	# should not need to clear here
	# but do it just incase
	print("[DEBUG] alarm() - clear events")
	g_ALARM_IN_PROGRESS.set()
	g_EVENT_STOP_ALARM.clear()
	g_EVENT_USER_CANCELLED.clear()

	print("[DEBUG] alarm() - starting GPIO and network alarms")
	GPIOSignal.alarm()
	Networking.alarm()

	print("[DEBUG] alarm() - releasing mutex")
	g_ALARM_MUTEX.release()



def init():
	GPIOSignal.init()
	atexit.register(cleanup)
	signal.signal(signal.SIGTERM, lambda *args: cleanup() or exit(0))


def loop():
	time.sleep(1)

	


if __name__ == "__main__":
	try:
		print("[DEBUG] Running init()")
		init()
		print("[DEBUG] Starting loop()")
		while 1:
			loop()
	except KeyboardInterrupt:
		pass
	finally:
		GPIO.cleanup()


