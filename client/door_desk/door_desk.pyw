import socket
import struct
import threading
import tkinter as tk
import pygame
import time
import sys
import traceback
import pystray
from PIL import Image
from io import BytesIO
import signal

# ----------------- CONFIG -----------------

AUDIO_FILE = "assets/door_desk.mp3"
g_CLIENT_RUNNING = True

class Packet:
	def __init__(self, recvfrom_data, recvfrom_addr):
		try:
			self.protocol_ver, self.event_timestamp, self.state = struct.unpack("!BIB", recvfrom_data[:6])
		except struct.error:
			raise ValueError("Invalid packet length")

		self.ip_address = recvfrom_addr[0]



class Network:
	PROTOCOL_VERSION = 1
	SERVER_IP = "192.168.0.69"
	
	class Port:
		INBOUND = 5005
		OUTBOUND = 5006


	class State:
		SEEKING_CONNECTION = 10
		CONNECTION_ACCEPTED = 11
		START_BEEP = 20
		STOP_BEEP = 21
		IDLE = 30

	@staticmethod
	def send_packet(timestamp: int, state: int):
		if type(timestamp) != int:
			raise TypeError(f"timestamp must be an 'int'. Not {type(timestamp)} {timestamp}")
		
		if type(state) != int and type(state) != Network.State:
			raise TypeError(f"state must be an 'int'. Not {type(state)} {state}")

		if state > 255 or state < 0:
			raise ValueError(f"state must be 0 <= state <= 255. Not {state}")
		
		print(f"Sending packet {timestamp} - {state}")

		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		packet = struct.pack("!BIB", Network.PROTOCOL_VERSION, timestamp, state)
		sock.sendto(packet, (Network.SERVER_IP, Network.Port.OUTBOUND))
		sock.close()
	

	@staticmethod
	def packet_listener(callback):
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.bind(("0.0.0.0", Network.Port.INBOUND))
		sock.settimeout(0.5)

		print("Listening for packets")
		while g_CLIENT_RUNNING:
			try:
				data, addr = sock.recvfrom(128)
			except socket.timeout:
				continue

			packet = Packet(data, addr)
			callback(packet)



class Timers:
	current_event_start_timestamp = 0
	last_packet_received_timestamp = 0
	last_seeking_conneciton_packet_sent_timestamp = 0
	MAX_ACK_INTERVAL_ms = 1000 * (90 + 10)
	SEEKING_CONNECTION_REQUEST_INTERVAL_ms = 5000



class AppIcon:
	file_path = "assets/door_desk.ico"

	tray = None
	window = None


	def init():
		img = Image.open(AppIcon.file_path).convert("RGBA")

		AppIcon.tray = img.resize((32, 32))

		img64 = img.resize((64, 64))
		buf = BytesIO()
		img64.save(buf, format="PNG")
		buf.seek(0)
		AppIcon.window = tk.PhotoImage(data=buf.read())



# ----------------- DESKTOP APP -----------------
class DeskDashApp:
	def __init__(self):
		self.last_timestamp = 0
		self.last_packet_time = 0
		self.pending_stop = False

		# Tkinter setup
		self.root = tk.Tk()
		self.root.title("DeskDash")
		self.root.geometry("360x160")
		self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
		self.root.attributes('-topmost', True)
		self.root.withdraw()

		AppIcon.init()

		tk.Label(self.root, text="Someone is at the door!", font=("Segoe UI", 14)).pack(pady=15)
		btn_frame = tk.Frame(self.root)
		btn_frame.pack(pady=5)
		tk.Button(btn_frame, text="Answer", font=("Segoe UI", 12), width=10, command=self.answer).grid(row=0, column=0, padx=10)
		tk.Button(btn_frame, text="Ignore", font=("Segoe UI", 12), width=10, command=self.ignore).grid(row=0, column=1, padx=10)

		# Icon / tray
		self.root.iconphoto(True, AppIcon.window)
		self.tray_icon = pystray.Icon(
			"DeskDash",
			AppIcon.tray,
			"DeskDash",
			menu=pystray.Menu(pystray.MenuItem("Quit", self.quit_app))
		)

		# Sound
		pygame.mixer.init()

		# Threads
		threading.Thread(target=Network.packet_listener, args=(self.handle_packet,), daemon=True).start()
		threading.Thread(target=self.tray_icon.run, daemon=True).start()
		time.sleep(1) # just to make sure the listening thread has started
		threading.Thread(target=self.send_seeking_loop, daemon=True).start()

		signal.signal(signal.SIGINT, self.handle_sigint)

	# ----------------- UDP LISTENER -----------------
	def handle_packet(self, packet):

		try:

			if packet.protocol_ver != Network.PROTOCOL_VERSION:
				return

			# Ignore duplicates
			if packet.event_timestamp != 0 and packet.event_timestamp <= self.last_timestamp:
				return


			if packet.state == Network.State.START_BEEP:
				print("stat beep packet")
				self.trigger_alarm()  # only call on 0, new packets cause audio to reset
				Timers.current_event_start_timestamp = packet.event_timestamp
				Timers.last_packet_received_timestamp = time.time()
				Network.send_packet(packet.event_timestamp, packet.state)

			elif packet.state == Network.State.STOP_BEEP:
				print("stop beep packet]")
				self.stop_sound()
				self.hide_window()
				self.pending_stop = False
				Timers.current_event_start_timestamp = packet.event_timestamp
				Network.send_packet(packet.event_timestamp, packet.state)

			elif packet.state == Network.State.IDLE:
				print("recieved idle packet")
				Timers.last_packet_received_timestamp = time.time()
				Network.send_packet(packet.event_timestamp, packet.state)

			elif packet.state == Network.State.CONNECTION_ACCEPTED:
				print("connection is accepted")
				Timers.last_packet_received_timestamp = time.time()

			elif packet.state == Network.State.SEEKING_CONNECTION:
				# Should not happen
				print("Unexpected SEEKING_CONNECTION from server")
				return

		except Exception:
			traceback.print_exc()
			time.sleep(1)

	# ----------------- SEEKING CONNECTION -----------------
	def send_seeking_loop(self):
		while g_CLIENT_RUNNING:
			current_time = time.time()
			if current_time - Timers.last_packet_received_timestamp > Timers.MAX_ACK_INTERVAL_ms:
				if current_time - Timers.last_seeking_conneciton_packet_sent_timestamp > Timers.SEEKING_CONNECTION_REQUEST_INTERVAL_ms:
					Network.send_packet(0, Network.State.SEEKING_CONNECTION)
					Timers.last_seeking_conneciton_packet_sent_timestamp = current_time

			time.sleep(1)

	# ----------------- BEHAVIOR -----------------
	def trigger_alarm(self):
		self.play_sound()
		self.root.after(0, self.force_show_window)

	def force_show_window(self):
		self.root.deiconify()
		self.root.lift()
		self.root.attributes("-topmost", True)
		self.root.after(200, lambda: self.root.attributes("-topmost", False))

	def hide_window(self):
		self.root.withdraw()

	def quit_app(self, icon=None, item=None):
		global g_CLIENT_RUNNING
		g_CLIENT_RUNNING = False

		self.stop_sound()
		pygame.mixer.quit()
		
		self.tray_icon.stop()

		for callback_id in self.root.tk.call('after', 'info'):
			self.root.after_cancel(callback_id)

		self.root.quit()
		sys.exit(0)

	# ----------------- SOUND -----------------
	def play_sound(self):
		try:
			pygame.mixer.music.load(AUDIO_FILE)
			pygame.mixer.music.play(-1)
		except Exception as e:
			print("Failed to play sound:", e)

	def stop_sound(self):
		pygame.mixer.music.stop()

	# ----------------- BUTTONS -----------------
	def answer(self):
		self.pending_stop = True
		Network.send_packet(Timers.current_event_start_timestamp, Network.State.STOP_BEEP)

	def ignore(self):
		self.stop_sound()
		self.hide_window()


	# ----------------- MAIN LOOP -----------------
	def run(self):
		self.root.mainloop()
	
	def handle_sigint(self, signum, frame):
		self.quit_app()


# ----------------- RUN -----------------
if __name__ == "__main__":
	app = DeskDashApp()
	app.run()
