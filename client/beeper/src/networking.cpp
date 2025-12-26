

#include <stdint.h>
#include <WiFi.h>
#include <WiFiUdp.h>

#include "networking.h"
#include "wifi_creds.h"

#include "logging.h"


WiFiUDP udp;
WiFiUDP udp_response;


namespace Network {
	const uint8_t PROTOCOL_VERSION = 1;
	const uint32_t SEND_IDLE_ACK_AFTER_DURATION = 90;

	const uint32_t WIFI_TIMEOUT_ms = 10000;
	const char* SERVER_IP = "192.168.0.69";
	
	namespace Port {
		const uint16_t OUTBOUND = 5006;
		const uint16_t INBOUND = 5005;
	}
	
	namespace State {
		const uint8_t NO_DATA = 1;
		const uint8_t SEEKING_CONNECTION = 10;
		const uint8_t CONNECTION_ACCEPTED = 11;
		const uint8_t START_BEEP = 20;
		const uint8_t STOP_BEEP = 21;
		const uint8_t IDLE = 30;
	}

};


UDPPacket::UDPPacket(const uint32_t event_timestamp, const uint8_t state) {
	this->protocol_ver = Network::PROTOCOL_VERSION;
	this->event_timestamp = event_timestamp;
	this->state = state;
}


uint8_t UDPPacket::construct_UDPPacket_from_buffer(unsigned char* buffer, const uint32_t size, UDPPacket& packet) {

	constexpr uint32_t expected_size = sizeof(protocol_ver) + sizeof(event_timestamp) + sizeof(state);

	if (size != expected_size) {
		Logging::error(__func__, "Invalid buffer size");
		return NETWORK_ERROR;
	}

	if (buffer[0] != Network::PROTOCOL_VERSION) {
		Logging::error(__func__, "Invalid protocol version");
		return NETWORK_ERROR;
	}

	uint32_t timestamp =
		((uint32_t)buffer[1] << 24) |
		((uint32_t)buffer[2] << 16) |
		((uint32_t)buffer[3] << 8)  |
		((uint32_t)buffer[4]);

	uint8_t state = buffer[5];

	packet = UDPPacket(timestamp, state);

	return NETWORK_SUCCESS;	
}


bool is_wifi_connected() {
	return WiFi.status() == WL_CONNECTED;
}


void setup_wifi() {

	WiFi.disconnect();

	WiFi.mode(WIFI_STA);
	WiFi.begin(WIFI_SSID, WIFI_PASS);
	Logging::info(__func__, "Connecting to wifi");


	unsigned long ts_start = millis();
	while (WiFi.status() != WL_CONNECTED) {

		if (millis() - ts_start > Network::WIFI_TIMEOUT_ms) {
			Logging::warn(__func__, "Timed out connecting to wifi");
			return;
		}

		delay(100);
	}

	Logging::info(__func__, "Connected to wifi");
	
	udp.begin(Network::Port::INBOUND);
	udp_response.begin(Network::Port::OUTBOUND);

	send_packet(0, Network::State::SEEKING_CONNECTION);
}


bool read_udp_packet(UDPPacket& packet) {

	// verify data is available
	int packet_size = udp.parsePacket();
	if (!packet_size) {
		return NETWORK_ERROR;
	}

	// read data packet
	unsigned char buffer[16] = { 0 };
	int len = udp.read(buffer, sizeof(buffer));

	UDPPacket new_packet(0, 0);
	if (UDPPacket::construct_UDPPacket_from_buffer(buffer, len, new_packet) != NETWORK_SUCCESS) {
		Logging::error(__func__, "Could not construct packet from received data");
		udp.flush();
		return NETWORK_ERROR;
	}

	packet = new_packet;
	return NETWORK_SUCCESS;
}


void send_packet(const uint32_t event_timestamp, const uint8_t state) {

	const uint8_t big_endian_event_timestamp[4] = {
		(event_timestamp >> 24) & 0xff,
		(event_timestamp >> 16) & 0xff,
		(event_timestamp >> 8) & 0xff,
		(event_timestamp >> 0) & 0xff
	};

	udp_response.beginPacket(Network::SERVER_IP, Network::Port::OUTBOUND);
	udp_response.write(Network::PROTOCOL_VERSION);
	udp_response.write(big_endian_event_timestamp, 4);
	udp_response.write(state);
	udp_response.endPacket();
}





