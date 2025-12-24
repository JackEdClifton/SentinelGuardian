
import time
import enum
import socket
import struct

from logging import Logging


class NetworkSettings:
	PROTOCOL_VERSION = 1
	TIMEOUT_DURATION = 200
	SEND_IDLE_ACK_AFTER_DURATION = 90 # don't send IDLE ACK if last packet was within x seconds

	class Port:
		OUTBOUND = 5005
		INBOUND = 5006

	class State(enum.IntEnum):
		SEEKING_CONNECTION = 10
		CONNECTION_ACCEPTED = 11
		START_BEEP = 20
		STOP_BEEP = 21
		IDLE = 30


	@staticmethod
	def inbound_packet_listener(callback):
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.bind(("0.0.0.0", NetworkSettings.Port.INBOUND))

		while True:
			data, addr = sock.recvfrom(128)

			packet = Packet(data, addr)
			callback(packet)


class Packet:
	def __init__(self, recvfrom_data, recvfrom_addr):
		try:
			self.protocol_ver, self.event_timestamp, self.state = struct.unpack("!BIB", recvfrom_data[:6])
		except struct.error:
			raise ValueError("Invalid packet length")

		self.ip_address = recvfrom_addr[0]



class Client:

	def __init__(self, ip_address, state):
		self.ip_address = ip_address
		self.last_packet_real_ts = int(time.time())
		self.last_packet_event_ts = int(time.time())
		self.last_packet_state = state
		self.consecutive_packets_missed = 0


	def send_packet(self, timestamp: int, state: int):

		if type(timestamp) != int:
			raise TypeError(f"timestamp must be an 'int'. Not {type(timestamp)} {timestamp}")
		
		if type(state) != int:
			raise TypeError(f"state must be an 'int'. Not {type(state)} {state}")

		if state > 255 or state < 0:
			raise ValueError(f"state must be 0 <= state <= 255. Not {state}")


		Logging.info(f"sending packet {state.name} to {self.ip_address}")

		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		packet = struct.pack("!BIB", NetworkSettings.PROTOCOL_VERSION, timestamp, state)
		sock.sendto(packet, (self.ip_address, NetworkSettings.Port.OUTBOUND))
		sock.close()
	

	def update_state(self, packet):

		if self.last_packet_event_ts > packet.event_timestamp:
			Logging.warn("Disregarding old packet")
			return

		# generating timestamp here probably add small delay
		# so not 100% accurate, but it will be negligable for this application
		self.last_packet_real_ts = int(time.time())
		self.last_packet_event_ts = packet.event_timestamp
		self.last_packet_state = packet.state


	def update_last_seen_ts(self):

		current_time = (time.time())

		if current_time > self.last_packet_real_ts:
			self.last_packet_real_ts = current_time

