
#include <Arduino.h>

#include <WiFi.h>
#include <WiFiUdp.h>

#include "wifi_creds.h"

const int UDP_PORT = 5005;
const int UDP_RESPONSE_PORT = 5006;

uint32_t g_ts_LAST_ALARM = 0;

WiFiUDP udp;
WiFiUDP udp_response;

namespace DoorCodes {
	const char* NO_DATA = "nodata";
	const char* START_ALARM = "A";
	const char* STOP_ALARM = "C";
};


const int GPIO_ALARM = 22;
const int GPIO_BUTTON = 21;

const int GPIO_LED_RED = 20;
const int GPIO_LED_GREEN = 19;

volatile bool g_EVENT_CANCEL_ALARM = false;

unsigned long alarm_prev_millis = 0;
bool alarm_active = false;

void btn_pressed() {
	Serial.print("[DEBUG] btn_pressed()\n");
	g_EVENT_CANCEL_ALARM = true;
}

void start_alarm() {

	Serial.print("[DEBUG] start_alarm() - setting RED LED on\n");

	digitalWrite(GPIO_LED_RED, HIGH);
	digitalWrite(GPIO_LED_GREEN, LOW);

	alarm_prev_millis = millis();
	Serial.print("[DEBUG] start_alarm() - set alarm_active\n");
	alarm_active = true;
	Serial.print("[DEBUG] start_alarm() - unset g_EVENT_CANCEL_ALARM\n");
	g_EVENT_CANCEL_ALARM = false;
}


void stop_alarm() {
	Serial.print("[DEBUG] stop_alarm() - disable buzzer & LEDs\n");
	noTone(GPIO_ALARM);
	digitalWrite(GPIO_ALARM, LOW);
	digitalWrite(GPIO_LED_RED, LOW);
	digitalWrite(GPIO_LED_GREEN, LOW);

	// send cancel packet to server
	Serial.print("[DEBUG] stop_alarm() - send cancel packet to server\n");
	udp_response.beginPacket("192.168.0.69", UDP_RESPONSE_PORT);
	udp_response.print(DoorCodes::STOP_ALARM);
	udp_response.endPacket();

	Serial.print("[DEBUG] stop_alarm() - unset alarm_active\n");
	alarm_active = false;
	Serial.print("[DEBUG] stop_alarm() - unset g_EVENT_CANCEL_ALARM\n");
	g_EVENT_CANCEL_ALARM = false;
}


void handle_alarm() {

	if (!alarm_active) {
		return;
	}

	unsigned long current = millis();

	if (current - alarm_prev_millis >= 270) {
		// toggle beeper
		static bool beep_on = false;
		if (beep_on) {
			noTone(GPIO_ALARM);
		}
		else {
			tone(GPIO_ALARM, 100);
		}

		beep_on = !beep_on;
		alarm_prev_millis = current;
	}

	if (g_EVENT_CANCEL_ALARM) {
		Serial.print("[DEBUG] handle_alarm() - g_EVENT_CANCEL_ALARM is set. Calling stop_alarm\n");
		stop_alarm();
	}
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

		// heartbeat red LED
		int interval = digitalRead(GPIO_LED_RED) ? 250 : 250;
		static unsigned long prev_millis = 0;
		unsigned long current_millis = millis();
		if (current_millis - prev_millis >= interval) {
			prev_millis = current_millis;
			digitalWrite(GPIO_LED_RED, !digitalRead(GPIO_LED_RED));
		}
	}

	Serial.print("[DEBUG] setup_wifi() - Connected to wifi\n");

	udp.begin(UDP_PORT);
	udp_response.begin(UDP_RESPONSE_PORT);
}


struct UDPPacket {
	uint32_t timestamp;
	const char* message;

	UDPPacket(uint32_t ts, const char* msg) {
		this->timestamp = ts;
		this->message = msg;
	}
};

UDPPacket read_udp_packet() {

	// verify data is available
	int packet_size = udp.parsePacket();
	if (!packet_size) {
		return UDPPacket(0, DoorCodes::NO_DATA);
	}

	// read data packet
	char buffer[128] = { 0 };
	int len = udp.read(buffer, sizeof(buffer) - 1);

	// verify at least the timestamp is present
	if (len <= 4) {
		Serial.print("[DEBUG] read_udp_packet() - insufficient data\n");
		return UDPPacket(0, DoorCodes::NO_DATA);
	}

	// need to convert because of endianness
	uint32_t timestamp = (buffer[0] << 24) | (buffer[1] << 16) | (buffer[2] << 8) | (buffer[3]);

	// message is directly after the timestamp
	const char* message = buffer + 4;

	return UDPPacket(timestamp, message);
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
		if (!alarm_active) {
			digitalWrite(GPIO_LED_RED, LOW);
		}
	} else {
		digitalWrite(GPIO_LED_RED, HIGH);
		digitalWrite(GPIO_LED_GREEN, LOW);
		setup_wifi();
		return;
	}

	// heartbeat green LED
	if (!alarm_active) {
		int interval = digitalRead(GPIO_LED_GREEN) ? 50 : 950;
		static unsigned long prev_millis = 0;
		unsigned long current_millis = millis();
		if (current_millis - prev_millis >= interval) {
			prev_millis = current_millis;
			digitalWrite(GPIO_LED_GREEN, !digitalRead(GPIO_LED_GREEN));
		}
	}

	// handle UDP messages
	UDPPacket packet = read_udp_packet();

	Serial.print("[DEBUG] loop() - parsing message\n");

	if (!strcmp(packet.message, DoorCodes::START_ALARM)) {
		if (packet.timestamp > g_ts_LAST_ALARM) {
			Serial.print("[DEBUG] loop() - new alarm packet recieved\n");
			g_ts_LAST_ALARM = packet.timestamp;
			Serial.print("[DEBUG] loop() - recieved packet START_ALARM\n");
			start_alarm();
		}
		else {
			Serial.print("[DEBUG] loop() - repeated alarm packet recieved\n");
		}
	}

	if (!strcmp(packet.message, DoorCodes::STOP_ALARM)) {
		Serial.print("[DEBUG] loop() - recieved packet STOP_ALARM\n");
		g_EVENT_CANCEL_ALARM = true;
	}

	handle_alarm();
}








