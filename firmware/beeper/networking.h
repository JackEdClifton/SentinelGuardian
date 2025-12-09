#pragma once

struct UDPPacket {
	uint32_t timestamp;
	uint8_t message;

	UDPPacket(const uint32_t ts, const uint8_t msg);
};


namespace AlarmStatusCodes {
	extern const uint8_t NO_DATA;
	extern const uint8_t START_ALARM;
	extern const uint8_t STOP_ALARM;
};


void setup_wifi();
UDPPacket read_udp_packet();
void send_stop_packet();
bool is_wifi_connected();