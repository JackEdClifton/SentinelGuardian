import socket
import struct
import threading
import tkinter as tk
import pygame
import time
import sys
import traceback
import pystray
from PIL import Image, ImageTk

# ----------------- CONFIG -----------------
SERVER_IP = "192.168.0.69"
BROADCAST_PORT = 5005
RESPONSE_PORT = 5006

SEEKING_INTERVAL = 5.0  # seconds between SEEKING_CONNECTION if no packets
PROTOCOL_VERSION = 1

# Network states
SEEKING_CONNECTION = 10
CONNECTION_ACCEPTED = 11
START_BEEP = 20
STOP_BEEP = 21
IDLE = 30

AUDIO_FILE = "assets/door_desk.mp3"

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

        tk.Label(self.root, text="Someone is at the door!", font=("Segoe UI", 14)).pack(pady=15)
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Answer", font=("Segoe UI", 12), width=10, command=self.answer).grid(row=0, column=0, padx=10)
        tk.Button(btn_frame, text="Ignore", font=("Segoe UI", 12), width=10, command=self.ignore).grid(row=0, column=1, padx=10)

        # Icon / tray
        self.icon_img = Image.open("assets/door_desk.ico")
        self.tk_icon = ImageTk.PhotoImage(self.icon_img)
        self.root.iconphoto(False, self.tk_icon)
        self.tray_icon = pystray.Icon(
            "DeskDash",
            self.icon_img,
            "DeskDash",
            menu=pystray.Menu(pystray.MenuItem("Quit", self.quit_app))
        )

        # Sound
        pygame.mixer.init()

        # Threads
        threading.Thread(target=self.listen_udp, daemon=True).start()
        threading.Thread(target=self.send_seeking_loop, daemon=True).start()
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    # ----------------- UDP LISTENER -----------------
    def listen_udp(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("", BROADCAST_PORT))

        while True:
            try:
                data, addr = sock.recvfrom(1024)
                if len(data) < 6:
                    continue

                proto, timestamp, state = struct.unpack("!BIB", data[:6])

                if proto != PROTOCOL_VERSION:
                    continue

                # Ignore duplicates
                if timestamp != 0 and timestamp <= self.last_timestamp:
                    continue

                self.last_timestamp = timestamp
                self.last_packet_time = time.time()

                if state == START_BEEP:
                    self.trigger_alarm()
                    self.send_idle(timestamp)

                elif state == STOP_BEEP:
                    self.pending_stop = False
                    self.stop_sound()
                    self.hide_window()
                    self.send_idle(timestamp)

                elif state == IDLE:
                    self.send_idle(timestamp)

                elif state == CONNECTION_ACCEPTED:
                    # Can mostly be ignored
                    pass

                elif state == SEEKING_CONNECTION:
                    # Should not happen
                    print("Unexpected SEEKING_CONNECTION from server")

            except Exception:
                traceback.print_exc()
                time.sleep(1)

    # ----------------- SEEKING CONNECTION -----------------
    def send_seeking_loop(self):
        while True:
            current_time = time.time()
            if current_time - self.last_packet_time > SEEKING_INTERVAL:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock.sendto(
                        struct.pack("!BIB", PROTOCOL_VERSION, 0, SEEKING_CONNECTION),
                        (SERVER_IP, RESPONSE_PORT)
                    )
                    sock.close()
                except Exception:
                    traceback.print_exc()

                self.last_packet_time = current_time

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
        self.stop_sound()
        self.tray_icon.stop()
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
        self.send_stop_packet()

    def ignore(self):
        self.stop_sound()
        self.hide_window()

    # ----------------- UDP SENDERS -----------------
    def send_idle(self, timestamp):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(
                struct.pack("!BIB", PROTOCOL_VERSION, timestamp, IDLE),
                (SERVER_IP, RESPONSE_PORT)
            )
            sock.close()
        except Exception:
            traceback.print_exc()

    def send_stop_packet(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(
                struct.pack("!BIB", PROTOCOL_VERSION, self.last_timestamp, STOP_BEEP),
                (SERVER_IP, RESPONSE_PORT)
            )
            sock.close()
        except Exception:
            traceback.print_exc()

    # ----------------- MAIN LOOP -----------------
    def run(self):
        self.root.mainloop()


# ----------------- RUN -----------------
if __name__ == "__main__":
    app = DeskDashApp()
    app.run()
