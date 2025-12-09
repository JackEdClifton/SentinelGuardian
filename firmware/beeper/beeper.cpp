
#include <Arduino.h>

#include "networking.h"
#include "LED_control.h"

uint32_t g_ts_LAST_ALARM = 0;



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
  send_stop_packet();

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
	if (is_wifi_connected()) {
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

	if (packet.message == AlarmStatusCodes::START_ALARM) {
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

	if (packet.message == AlarmStatusCodes::STOP_ALARM) {
		Serial.print("[DEBUG] loop() - recieved packet STOP_ALARM\n");
		g_EVENT_CANCEL_ALARM = true;
	}

	handle_alarm();
}








