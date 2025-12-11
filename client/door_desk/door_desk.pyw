import socket
import struct
import threading
import tkinter as tk
from tkinter import messagebox
import pygame
import time
import sys
import os
import traceback
import pystray
from PIL import Image, ImageTk

BROADCAST_PORT = 5005
RESPONSE_PORT = 5006
SERVER_IP = "192.168.0.69"

START_ALARM = 20
STOP_ALARM = 30

AUDIO_FILE = "assets/door_desk.mp3"


class DeskDashApp:
	def __init__(self):
		# Track last timestamp to ignore duplicates
		self.last_timestamp = None

		# Window hidden by default
		self.root = tk.Tk()
		self.root.title("DeskDash")
		self.root.geometry("360x160")
		self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
		self.root.attributes('-topmost', True)
		self.root.withdraw()

		# UI buttons
		tk.Label(self.root, text="Someone is at the door!", font=("Segoe UI", 14)).pack(pady=15)

		btn_frame = tk.Frame(self.root)
		btn_frame.pack(pady=5)

		tk.Button(btn_frame, text="Answer", font=("Segoe UI", 12), width=10, command=self.answer).grid(row=0, column=0, padx=10)
		tk.Button(btn_frame, text="Ignore", font=("Segoe UI", 12), width=10, command=self.ignore).grid(row=0, column=1, padx=10)

		# Load main icon
		self.icon_img = Image.open("assets/door_desk.ico")
		self.tk_icon = ImageTk.PhotoImage(self.icon_img)
		self.root.iconphoto(False, self.tk_icon)

		# Tray icon setup
		self.tray_icon = pystray.Icon("DeskDash",
			self.icon_img,
			"DeskDash",
			menu=pystray.Menu(pystray.MenuItem("Quit", self.quit_app))
		)

		# Start pygame sound system
		pygame.mixer.init()

		# Background listener thread
		self.listener_thread = threading.Thread(target=self.listen_udp, daemon=True)
		self.listener_thread.start()

		# Tray icon thread
		threading.Thread(target=self.tray_icon.run, daemon=True).start()

	# ==========================================================
	# UDP LISTENER
	# ==========================================================
	def listen_udp(self):
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.bind(("", BROADCAST_PORT))

		while True:
			try:
				data, addr = sock.recvfrom(1024)
				if len(data) < 5:
					continue

				timestamp = struct.unpack("!I", data[:4])[0]
				code = data[4]

				if code == START_ALARM:
					if timestamp != self.last_timestamp:
						self.last_timestamp = timestamp
						self.trigger_alarm()

				elif code == STOP_ALARM:
					self.stop_sound()
					self.hide_window()

			except Exception:
				traceback.print_exc()
				time.sleep(1)

	# ==========================================================
	# BEHAVIOR
	# ==========================================================
	def trigger_alarm(self):
		self.play_sound()

		# Show window on main thread
		self.root.after(0, self.force_show_window)

	def force_show_window(self):
		self.root.deiconify()
		self.root.lift()
		self.root.attributes("-topmost", True)
		self.root.after(200, lambda: self.root.attributes("-topmost", False))

	def hide_window(self):
		self.root.withdraw()

	def quit_app(self, icon=None, item=None):
		self.stop_sound()
		self.tray_icon.stop()
		self.root.quit()
		sys.exit(0)

	# ==========================================================
	# SOUND
	# ==========================================================
	def play_sound(self):
		try:
			pygame.mixer.music.load(AUDIO_FILE)
			pygame.mixer.music.play(-1)
		except Exception as e:
			print("Failed to play sound:", e)

	def stop_sound(self):
		pygame.mixer.music.stop()

	# ==========================================================
	# BUTTONS
	# ==========================================================
	def answer(self):
		self.stop_sound()
		self.send_stop_packet()
		self.hide_window()

	def ignore(self):
		self.stop_sound()
		self.hide_window()

	# ==========================================================
	# SEND UDP TO SERVER
	# ==========================================================
	def send_stop_packet(self):
		try:
			sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			sock.sendto(bytes([STOP_ALARM]), (SERVER_IP, RESPONSE_PORT))
			sock.close()
		except Exception:
			traceback.print_exc()

	# ==========================================================
	# MAIN LOOP
	# ==========================================================
	def run(self):
		self.root.mainloop()


# ----------------------------------------------------------
# RUN THE APP
# ----------------------------------------------------------
if __name__ == "__main__":
	app = DeskDashApp()
	app.run()
