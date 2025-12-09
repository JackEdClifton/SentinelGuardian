
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

		print("[DEBUG] GPIOSignal.init() - setting GPIO mode to BCM", flush=True)
		GPIO.setmode(GPIO.BCM)

		print("[DEBUG] GPIOSignal.init() - setup button", flush=True)
		GPIO.setup(GPIOSignal.BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.add_event_detect(GPIOSignal.BUTTON, GPIO.FALLING, callback=alarm, bouncetime=100)

		print("[DEBUG] GPIOSignal.init() - setup beeper & LEDs", flush=True)
		GPIO.setup(GPIOSignal.BEEPER, GPIO.OUT)
		GPIO.setup(GPIOSignal.LED.RED, GPIO.OUT)
		GPIO.setup(GPIOSignal.LED.BLUE, GPIO.OUT)
		GPIO.setup(GPIOSignal.LED.GREEN, GPIO.OUT)

		GPIO.output(GPIOSignal.BEEPER, GPIO.LOW)
		GPIO.output(GPIOSignal.LED.RED, GPIO.LOW)
		GPIO.output(GPIOSignal.LED.BLUE, GPIO.LOW)
		GPIO.output(GPIOSignal.LED.GREEN, GPIO.LOW)

		print("[DEBUG] GPIOSignal.init() - setup done", flush=True)


	@staticmethod
	def _play_beep_pattern():
		print("[DEBUG] GPIOSignal._play_beep_pattern() - beeper started", flush=True)
		for i in range(5):
			GPIO.output(GPIOSignal.BEEPER, GPIO.HIGH)
			time.sleep(0.1)
			GPIO.output(GPIOSignal.BEEPER, GPIO.LOW)
			time.sleep(0.1)

		print("[DEBUG] GPIOSignal._play_beep_pattern() - beeper stopped", flush=True)


	@staticmethod
	def _play_blink_pattern():

		GPIO.output(GPIOSignal.LED.RED, GPIO.LOW)
		ts_start = time.time()

		print("[DEBUG] GPIOSignal._play_blink_pattern() - blink started", flush=True)

		while (
			(not g_EVENT_STOP_ALARM.is_set()) and
			(not g_EVENT_USER_CANCELLED.is_set()) and
			(time.time() - ts_start < 20.0)):

			GPIO.output(GPIOSignal.LED.BLUE, GPIO.HIGH)
			time.sleep(0.05)
			GPIO.output(GPIOSignal.LED.BLUE, GPIO.LOW)
			time.sleep(0.45)

		print("[DEBUG] GPIOSignal._play_blink_pattern() - blink stopped", flush=True)

		print("[DEBUG] GPIOSignal._play_blink_pattern() - g_EVENT_STOP_ALARM.set()", flush=True)
		g_EVENT_STOP_ALARM.set()


	@staticmethod
	def _alarm():

		print("[DEBUG] GPIOSignal._alarm() - setting up threads", flush=True)
		t_beeper = threading.Thread(target=GPIOSignal._play_beep_pattern)
		t_LED = threading.Thread(target=GPIOSignal._play_blink_pattern)
		print("[DEBUG] GPIOSignal._alarm() - starting threads", flush=True)
		t_beeper.start()
		t_LED.start()
		print("[DEBUG] GPIOSignal._alarm() - awaiting threads", flush=True)
		t_beeper.join()
		t_LED.join()
		print("[DEBUG] GPIOSignal._alarm() - threads complete", flush=True)

		GPIO.output(GPIOSignal.BEEPER, GPIO.LOW)
		GPIO.output(GPIOSignal.LED.BLUE, GPIO.LOW)

		# todo: handle red/green signal for 20s
		if g_EVENT_USER_CANCELLED.is_set():
			GPIO.output(GPIOSignal.LED.GREEN, GPIO.HIGH)
		else:
			GPIO.output(GPIOSignal.LED.RED, GPIO.HIGH)

		print("[DEBUG] GPIOSignal._alarm() - response LED set", flush=True)
		time.sleep(20)

		print("[DEBUG] GPIOSignal._alarm() - LEDs turned off", flush=True)
		GPIO.output(GPIOSignal.LED.RED, GPIO.LOW)
		GPIO.output(GPIOSignal.LED.BLUE, GPIO.LOW)
		GPIO.output(GPIOSignal.LED.GREEN, GPIO.LOW)

		print("[DEBUG] GPIOSignal._alarm() - clear all 3 events", flush=True)
		g_EVENT_STOP_ALARM.clear()
		g_EVENT_USER_CANCELLED.clear()
		g_ALARM_IN_PROGRESS.clear()


	def alarm():
		threading.Thread(target=GPIOSignal._alarm, daemon=True).start()



class Networking:
	BROADCAST_IP = "192.168.0.255"
	BROADCAST_PORT = 5005
	LISTEN_PORT = 5006

	START_ALARM = 20
	STOP_ALARM = 30


	@staticmethod
	def send_alarm(timestamp):
		print("[DEBUG] Networking.send_alarm() - sending alarm", flush=True)
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		packet = struct.pack("!I", int(timestamp)) + bytes([Networking.START_ALARM])
		sock.sendto(packet, (Networking.BROADCAST_IP, Networking.BROADCAST_PORT))
		sock.close()
		print("[DEBUG] Networking.send_alarm() - socket closed", flush=True)

	
	@staticmethod
	def send_cancel():
		print("[DEBUG] Networking.send_cancel() - sending cancel", flush=True)
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		packet = struct.pack("!I", int(0)) + bytes([Networking.STOP_ALARM])
		sock.sendto(packet, (Networking.BROADCAST_IP, Networking.BROADCAST_PORT))
		sock.close()
		print("[DEBUG] Networking.send_cancel() - socket closed", flush=True)


	@staticmethod
	def _listen_for_cancel(sock):
		print("[DEBUG] Networking._listen_for_cancel() - setting up socket", flush=True)
		sock.settimeout(0.5)
		sock.bind(("0.0.0.0", Networking.LISTEN_PORT))
		print("[DEBUG] Networking._listen_for_cancel() - running listener loop", flush=True)
		while not (g_EVENT_STOP_ALARM.is_set() or g_EVENT_USER_CANCELLED.is_set()):
			try:
				raw_data, addr = sock.recvfrom(128)
				data = int(bytes.decode(raw_data))
				print("[DEBUG] Networking._listen_for_cancel() - recieved data: " + str(data), flush=True)

				if data == Networking.STOP_ALARM:
					print("[DEBUG] Networking._listen_for_cancel() - CANCEL recieved", flush=True)
					print("[DEBUG] Networking._listen_for_cancel() - setting g_EVENT_USER_CANCELLED", flush=True)
					g_EVENT_USER_CANCELLED.set()
				else:
					print("[DEBUG] Networking._listen_for_cancel() - raw_data does not match Networking.STOP_ALARM... ignoring", flush=True)
					 

			except socket.timeout:
				continue
			except OSError:
				print("[DEBUG] Networking._listen_for_cancel() - OSError", flush=True)
				break # socket closed
			except ValueError:
				print("[ERROR] Networking._listen_for_cancel() - Could not cast data into an int", flush=True)

		


	@staticmethod
	def _alarm():
		ts_start = int(time.time())

		# start listener
		print("[DEBUG] Networking._alarm() - setting up socket", flush=True)
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		listener = threading.Thread(
			target=Networking._listen_for_cancel,
			args=(sock, ),
			daemon=True
		)
		listener.start()
		print("[DEBUG] Networking._alarm() - started listener thread", flush=True)

		while not (g_EVENT_STOP_ALARM.is_set() or g_EVENT_USER_CANCELLED.is_set()):
			
			print("[DEBUG] Networking._alarm() - sending alarm", flush=True)
			Networking.send_alarm(ts_start)
			print("[DEBUG] Networking._alarm() - sent alarm", flush=True)
			

			# do a 5s sleep, but more responsive to the event
			for i in range(10):
				time.sleep(0.5)
				if g_EVENT_STOP_ALARM.is_set() or g_EVENT_USER_CANCELLED.is_set():
					print("[DEBUG] Networking._alarm() - a g_EVENT is set. Breaking sleep loop", flush=True)
					break

		sock.close()
		print("[DEBUG] Networking._alarm() - socket closed", flush=True)
		listener.join()
		print("[DEBUG] Networking._alarm() - listener thread complete", flush=True)

		print("[DEBUG] Networking._alarm() - sending cancel", flush=True)
		Networking.send_cancel()
		print("[DEBUG] Networking._alarm() - sent cancel", flush=True)


	@staticmethod
	def alarm():
		threading.Thread(target=Networking._alarm, daemon=True).start()



g_ALARM_MUTEX = threading.Lock()
def alarm(channel=None):

	print("[DEBUG] alarm() - function called", flush=True)
	if g_ALARM_IN_PROGRESS.is_set():
		print("[DEBUG] alarm() - function returned due to alarm already in progress", flush=True)
		return

	if not g_ALARM_MUTEX.acquire(blocking=False):
		print("[DEBUG] alarm() - function returned as mutex cannot be taken", flush=True)
		return

	# should not need to clear here
	# but do it just incase
	print("[DEBUG] alarm() - clear events", flush=True)
	g_ALARM_IN_PROGRESS.set()
	g_EVENT_STOP_ALARM.clear()
	g_EVENT_USER_CANCELLED.clear()

	print("[DEBUG] alarm() - starting GPIO and network alarms", flush=True)
	GPIOSignal.alarm()
	Networking.alarm()

	print("[DEBUG] alarm() - releasing mutex", flush=True)
	g_ALARM_MUTEX.release()



def init():
	GPIOSignal.init()
	atexit.register(cleanup)
	signal.signal(signal.SIGTERM, lambda *args: cleanup() or exit(0))


def loop():
	time.sleep(1)

	


if __name__ == "__main__":
	try:
		print("[DEBUG] Running init()", flush=True)
		init()
		print("[DEBUG] Starting loop()", flush=True)
		while 1:
			loop()
	except KeyboardInterrupt:
		pass
	finally:
		GPIO.cleanup()


