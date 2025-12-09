

#include <stdint.h>
#include <WiFi.h>
#include <WiFiUdp.h>

#include "networking.h"
#include "wifi_creds.h"
#include "LED_control.h"


WiFiUDP udp;
WiFiUDP udp_response;


const char* SERVER_IP = "192.168.0.69";
const int UDP_PORT = 5005;
const int UDP_RESPONSE_PORT = 5006;


namespace AlarmStatusCodes {
	const uint8_t NO_DATA = 10;
	const uint8_t START_ALARM = 20;
	const uint8_t STOP_ALARM = 30;
};



bool is_wifi_connected() {
	return WiFi.status() == WL_CONNECTED;
}



void setup_wifi() {

	const int WIFI_TIMEOUT_ms = 10000;

	WiFi.disconnect();

	WiFi.mode(WIFI_STA);
	WiFi.begin(WIFI_SSID, WIFI_PASS);
	Serial.print("[DEBUG] setup_wifi() - Connecting to wifi\n");


	unsigned long ts_start = millis();
	while (WiFi.status() != WL_CONNECTED && millis() - ts_start < WIFI_TIMEOUT_ms) {
		delay(150);
		heartbeat_RED_LED_tick();
	}

	Serial.print("[DEBUG] setup_wifi() - Connected to wifi\n");

	udp.begin(UDP_PORT);
	udp_response.begin(UDP_RESPONSE_PORT);
}



UDPPacket::UDPPacket(const uint32_t ts, const uint8_t msg) {
  this->timestamp = ts;
  this->message = msg;
}



UDPPacket read_udp_packet() {

	// verify data is available
	int packet_size = udp.parsePacket();
	if (!packet_size) {
		return UDPPacket(0, AlarmStatusCodes::NO_DATA);
	}

	// read data packet
	char buffer[128] = { 0 };
	int len = udp.read(buffer, sizeof(buffer) - 1);

	// verify at least the timestamp is present
	if (len <= 4) {
		Serial.print("[DEBUG] read_udp_packet() - insufficient data\n");
		return UDPPacket(0, AlarmStatusCodes::NO_DATA);
	}

	// need to convert because of endianness
	uint32_t timestamp = (buffer[0] << 24) | (buffer[1] << 16) | (buffer[2] << 8) | (buffer[3]);

	// message is directly after the timestamp
	uint8_t message = *(buffer + 4);

	return UDPPacket(timestamp, message);
}



void send_stop_packet() {
	udp_response.beginPacket(SERVER_IP, UDP_RESPONSE_PORT);
	udp_response.print(AlarmStatusCodes::STOP_ALARM);
	udp_response.endPacket();
}





