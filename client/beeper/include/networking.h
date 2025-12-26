#pragma once

#define NETWORK_SUCCESS	0
#define NETWORK_ERROR	1

namespace Network {
	extern const uint8_t PROTOCOL_VERSION;
	extern const uint32_t SEND_IDLE_ACK_AFTER_DURATION;

	extern const uint32_t WIFI_TIMEOUT_ms;
	extern const char* SERVER_IP;
	
	namespace Port {
		extern const uint16_t OUTBOUND;
		extern const uint16_t INBOUND;
	}
	
	namespace State {
		extern const uint8_t SEEKING_CONNECTION;
		extern const uint8_t CONNECTION_ACCEPTED;
		extern const uint8_t START_BEEP;
		extern const uint8_t STOP_BEEP;
		extern const uint8_t IDLE;
	}

};


struct UDPPacket {
	uint8_t protocol_ver;
	uint32_t event_timestamp;
	uint8_t state;

	UDPPacket(const uint32_t event_timestamp, const uint8_t state);
	
	static uint8_t construct_UDPPacket_from_buffer(unsigned char* buffer, const uint32_t size, UDPPacket& packet);
};


bool is_wifi_connected();
void setup_wifi();
bool read_udp_packet(UDPPacket& packet);
void send_packet(const uint32_t event_timestamp, const uint8_t state);

