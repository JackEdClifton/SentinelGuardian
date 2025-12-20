
#include <Arduino.h>
#include "hardware/clocks.h"

#include "networking.h"
#include "LED_control.h"
#include "logging.h"

uint32_t g_ts_LAST_ALARM = 0;



volatile bool g_EVENT_CANCEL_ALARM = false;

unsigned long alarm_prev_millis = 0;
bool alarm_active = false;

void btn_pressed() {
	Logging::Trace(__func__);
	g_EVENT_CANCEL_ALARM = true;
}

void start_alarm() {

	Logging::Trace(__func__);

	digitalWrite(GPIO_LED_RED, HIGH);
	digitalWrite(GPIO_LED_GREEN, LOW);

	alarm_prev_millis = millis();
	Logging::debug(__func__, "set alarm active");
	alarm_active = true;
	Logging::debug(__func__, "unset g_EVENT_CANCEL_ALARM");
	g_EVENT_CANCEL_ALARM = false;
}


void stop_alarm() {
	Logging::Trace(__func__);
	Logging::debug(__func__, "disable buzzer & LEDs");
	noTone(GPIO_ALARM);
	digitalWrite(GPIO_ALARM, LOW);
	digitalWrite(GPIO_LED_RED, LOW);
	digitalWrite(GPIO_LED_GREEN, LOW);

	// send cancel packet to server
	Logging::info(__func__, "send cancel packet to server");
  send_stop_packet();

	Logging::debug(__func__, "unset alarm_active");
	alarm_active = false;
	Logging::debug(__func__, "unset g_EVENT_CANCEL_ALARM");
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
		Logging::debug(__func__, "g_EVENT_CANCEL_ALARM is set. Calling stop_alarm");
		stop_alarm();
	}
}







void setup() {

	Logging::init();

	if (!set_sys_clock_khz(65000, true)) {
		Logging::warn(__func__, "Failed to apply CPU clock freq");
	}

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

	if (packet.message == AlarmStatusCodes::START_ALARM) {
		if (packet.timestamp > g_ts_LAST_ALARM) {
			Logging::info(__func__, "new alarm packet recieved");
			g_ts_LAST_ALARM = packet.timestamp;
			Logging::info(__func__, "recieved packet START_ALARM");
			start_alarm();
		}
		else {
			Logging::info(__func__, "repeated alarm packet recieved");
		}
	}

	if (packet.message == AlarmStatusCodes::STOP_ALARM) {
		Logging::info(__func__, "recieved packet STOP_ALARM");
		g_EVENT_CANCEL_ALARM = true;
	}

	handle_alarm();
}








