
#include <WiFi.h>
#include <WiFiUdp.h>

#include "wifi_creds.h"

const int UDP_PORT = 5005;

WiFiUDP udp;

namespace DoorCodes {
const char* NOTHING = "nodata";
const char* ALARM = "getfuckingdoorucunts";

enum Codes {
	NO_DATA = 0,
	START_ALARM,
	STOP_ALARM
};
};


const int GPIO_ALARM = 22;
const int GPIO_BUTTON = 21;

const int GPIO_LED_RED = 20;
const int GPIO_LED_GREEN = 19;

volatile bool g_EVENT_CANCEL_ALARM = false;

void btn_pressed() {
	g_EVENT_CANCEL_ALARM = true;
}

void alarm() {

	digitalWrite(GPIO_LED_RED, HIGH);
	digitalWrite(GPIO_LED_GREEN, LOW);

	while (!g_EVENT_CANCEL_ALARM) {
		tone(GPIO_ALARM, 100);  // 2kHz tone
		delay(200);             // tone duration
		noTone(GPIO_ALARM);     // stop tone
		delay(70);              // pause between beeps
	}

	digitalWrite(GPIO_ALARM, LOW);
	digitalWrite(GPIO_LED_RED, LOW);
	digitalWrite(GPIO_LED_GREEN, LOW);

	g_EVENT_CANCEL_ALARM = false;
}


void setup_wifi() {

	WiFi.disconnect();

	WiFi.mode(WIFI_STA);
	WiFi.begin(WIFI_SSID, WIFI_PASS);
	Serial.print("Connecting to wifi\n");

	while (WiFi.status() != WL_CONNECTED) {
		Serial.print("Not connected to wifi\n");

		switch (WiFi.status()) {
			case WL_IDLE_STATUS: Serial.println("WL_IDLE_STATUS"); break;
			case WL_NO_SSID_AVAIL: Serial.println("WL_NO_SSID_AVAIL"); break;
			case WL_CONNECT_FAILED:
				Serial.println("WL_CONNECT_FAILED");
				break;
				//		this one is not defined for some reason
				//			case WL_WRONG_PASSWORD: Serial.println("WL_WRONG_PASSWORD"); break;
			case WL_DISCONNECTED: Serial.println("WL_DISCONNECTED"); break;
			case WL_CONNECTED: Serial.println("WL_CONNECTED"); break;
			default: Serial.println("UNKNOWN");
		}

		// heartbeat red LED
		int interval = digitalRead(GPIO_LED_RED) ? 500 : 500;
		static unsigned long prev_millis = 0;
		unsigned long current_millis = millis();
		if (current_millis - prev_millis >= interval) {
			prev_millis = current_millis;
			digitalWrite(GPIO_LED_RED, !digitalRead(GPIO_LED_RED));
		}


		delay(150);
	}

	udp.begin(UDP_PORT);
}



int read_parse_udp_packet() {

	// verify data is available
	int packet_size = udp.parsePacket();
	if (!packet_size) {
		return DoorCodes::Codes::NO_DATA;
	}

	// read data packet
	char buffer[128] = { 0 };
	int len = udp.read(buffer, sizeof(buffer) - 1);

	// verify at least the timestamp is present
	if (len <= 4) {
		return DoorCodes::Codes::NO_DATA;
	}

	// need to convert because of endianness
	uint32_t timestamp =
	  (buffer[0] << 24) | (buffer[1] << 16) | (buffer[2] << 8) | (buffer[3]);

	// message is directly after the timestamp
	const char* message = buffer + 4;

	if (strcmp(message, DoorCodes::NOTHING) == 0) {
		return DoorCodes::Codes::STOP_ALARM;
	}

	if (strcmp(message, DoorCodes::ALARM) == 0) {
		return DoorCodes::Codes::START_ALARM;
	}

	return DoorCodes::Codes::NO_DATA;  // can't be sure
}


void setup() {

	Serial.begin(115200);

	// configure LEDs
	pinMode(GPIO_LED_RED, OUTPUT);
	pinMode(GPIO_LED_GREEN, OUTPUT);
	digitalWrite(GPIO_LED_RED, HIGH);
	digitalWrite(GPIO_LED_GREEN, LOW);

	// configure beeper
	pinMode(GPIO_ALARM, OUTPUT);
	digitalWrite(GPIO_ALARM, LOW);

	// configure button
	pinMode(GPIO_BUTTON, INPUT_PULLUP);
	attachInterrupt(digitalPinToInterrupt(GPIO_BUTTON), btn_pressed, FALLING);

	// configure wifi
	setup_wifi();
}


void loop() {

	delay(10);

	// handle wifi
	if (WiFi.status() == WL_CONNECTED) {
		digitalWrite(GPIO_LED_RED, LOW);
	} else {
		digitalWrite(GPIO_LED_RED, HIGH);
		digitalWrite(GPIO_LED_GREEN, LOW);
		setup_wifi();
		delay(200);
		return;
	}

	// heartbeat green LED
	int interval = digitalRead(GPIO_LED_GREEN) ? 50 : 950;
	static unsigned long prev_millis = 0;
	unsigned long current_millis = millis();
	if (current_millis - prev_millis >= interval) {
		prev_millis = current_millis;
		digitalWrite(GPIO_LED_GREEN, !digitalRead(GPIO_LED_GREEN));
	}

	// handle networking
	int packet_code = read_parse_udp_packet();

	if (packet_code == DoorCodes::Codes::NO_DATA) {
		return;
	}

	else if (packet_code == DoorCodes::Codes::STOP_ALARM) {
		g_EVENT_CANCEL_ALARM = true;
	}

	else if (packet_code == DoorCodes::Codes::START_ALARM) {
		alarm();
	}
}
