
import RPi.GPIO as GPIO
import threading
import time


class GPIOController:

	class Pinout:
		class LED:
			RED = 17
			BLUE = 22
			GREEN = 27
		BEEPER = 23
		BUTTON = 24


	class Beeper:

		_beep_lock = threading.Lock()

		@staticmethod
		def init():
			GPIO.setup(GPIOController.Pinout.BEEPER, GPIO.OUT)
			GPIO.output(GPIOController.Pinout.BEEPER, GPIO.LOW)
		
		@staticmethod
		def start_beep_pattern():
			if not GPIOController.Beeper._beep_lock.acquire(blocking=False):
				return

			def _play_beep_pattern():
				try:
					for i in range(5):
						GPIO.output(GPIOController.Pinout.BEEPER, GPIO.HIGH)
						time.sleep(0.1)
						GPIO.output(GPIOController.Pinout.BEEPER, GPIO.LOW)
						time.sleep(0.1)
				finally:
					GPIOController.Beeper._beep_lock.release()

			threading.Thread(target=_play_beep_pattern, daemon=True).start()



	class LED:

		BLUE_BLINK_TIME_ON = 0.05
		BLUE_BLINK_TIME_OFF = 0.45
		LED_GREEN_RED_HOLD = 30

		_event_stop_current_task = threading.Event()
		_lock_led_control = threading.Lock()

		@staticmethod
		def init():
			GPIO.setup(GPIOController.Pinout.LED.RED, GPIO.OUT)
			GPIO.setup(GPIOController.Pinout.LED.BLUE, GPIO.OUT)
			GPIO.setup(GPIOController.Pinout.LED.GREEN, GPIO.OUT)

			GPIO.output(GPIOController.Pinout.LED.RED, GPIO.LOW)
			GPIO.output(GPIOController.Pinout.LED.BLUE, GPIO.LOW)
			GPIO.output(GPIOController.Pinout.LED.GREEN, GPIO.LOW)


		@staticmethod
		def cancel_current_task():
			GPIOController.LED._event_stop_current_task.set()
			with GPIOController.LED._lock_led_control:
				GPIOController.LED._event_stop_current_task.clear()


		@staticmethod
		def set_off():
			with GPIOController.LED._lock_led_control:
				GPIO.output(GPIOController.Pinout.LED.RED, GPIO.LOW)
				GPIO.output(GPIOController.Pinout.LED.BLUE, GPIO.LOW)
				GPIO.output(GPIOController.Pinout.LED.GREEN, GPIO.LOW)


		@staticmethod
		def _auto_timed_hold_led_solid(LED):

			def _auto_timed_hold_led_solid_task(LED):

				with GPIOController.LED._lock_led_control:

					GPIO.output(LED, GPIO.HIGH)

					start_time = time.time()

					while ((not GPIOController.LED._event_stop_current_task.is_set())
						and (time.time() - start_time < GPIOController.LED.LED_GREEN_RED_HOLD)):
						time.sleep(0.1)

					GPIO.output(LED, GPIO.LOW)

			threading.Thread(target=_auto_timed_hold_led_solid_task,
				args=(LED,), daemon=True).start()


		@staticmethod
		def set_red():
			GPIOController.LED.cancel_current_task()
			GPIOController.LED.set_off()
			GPIOController.LED._auto_timed_hold_led_solid(GPIOController.Pinout.LED.RED)


		@staticmethod
		def set_green():
			GPIOController.LED.cancel_current_task()
			GPIOController.LED.set_off()
			GPIOController.LED._auto_timed_hold_led_solid(GPIOController.Pinout.LED.GREEN)


		@staticmethod
		def blink_blue():
			GPIOController.LED.cancel_current_task()
			GPIOController.LED.set_off()

			def _blink():

				with GPIOController.LED._lock_led_control:

					start_time = time.time()

					# we do not need a timeout here
					# we reply on the main function calling set_off()
					while not GPIOController.LED._event_stop_current_task.is_set():
						GPIO.output(GPIOController.Pinout.LED.BLUE, GPIO.HIGH)
						time.sleep(GPIOController.LED.BLUE_BLINK_TIME_ON)
						GPIO.output(GPIOController.Pinout.LED.BLUE, GPIO.LOW)
						time.sleep(GPIOController.LED.BLUE_BLINK_TIME_OFF)
					

			threading.Thread(target=_blink, daemon=True).start()


	

	@staticmethod
	def init(on_press_callback):
		GPIO.setmode(GPIO.BCM)
		GPIOController.Beeper.init()
		GPIOController.LED.init()

		GPIO.setup(GPIOController.Pinout.BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.add_event_detect(GPIOController.Pinout.BUTTON, GPIO.FALLING, callback=on_press_callback, bouncetime=100)
