#pragma once

struct UDPPacket {
	uint32_t timestamp;
	const char* message;

	UDPPacket(uint32_t ts, const char* msg);
};


namespace DoorCodes {
	extern const char* NO_DATA;
	extern const char* START_ALARM;
	extern const char* STOP_ALARM;
};


void setup_wifi();
UDPPacket read_udp_packet();
void send_stop_packet();
bool is_wifi_connected();