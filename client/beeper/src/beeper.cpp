
#include <Arduino.h>
#include "hardware/clocks.h"

#include "networking.h"
#include "gpio_controller.h"
#include "logging.h"

unsigned long current_event_start_timestamp = 0;
unsigned long last_packet_received_timestamp = 0;

const unsigned long MAX_ACK_INTERVAL_ms = 1000 * (90 + 10); // 10s is margin to account for network latency
const unsigned long SEEKING_CONNECTION_REQUEST_INTERVAL_ms = 5000;

void on_button_press() {
	Logging::info(__func__, "button pressed");
	send_packet(current_event_start_timestamp, Network::State::STOP_BEEP);
	// we send packet, but don't act yet, because the server will send back a response
	// if this response is not received, then the user will know something went wrong
}


// rewriting here
void handle_packet(const UDPPacket& packet) {

	// check packet is not old
	if (packet.event_timestamp != 0 && packet.event_timestamp < current_event_start_timestamp) {
		return;
	}



	if (packet.state == Network::State::SEEKING_CONNECTION) {
		Logging::error(__func__, "we should never recieve SEEKING_CONNECTION packet. Only send it");
		return;
	}


	if (packet.state == Network::State::CONNECTION_ACCEPTED) {
		GPIOController::configure_idle_flash();
		last_packet_received_timestamp = millis();
		// we might handle this based on state later
		// for now we just assume it worked
		// and retry after a timeout
		return;
	}


	if (packet.state == Network::State::START_BEEP) {
		Logging::info(__func__, "start beep packet received");
		GPIOController::configure_alarm();
		current_event_start_timestamp = packet.event_timestamp;
		last_packet_received_timestamp = millis();
		send_packet(current_event_start_timestamp, packet.state);
	}


	if (packet.state == Network::State::STOP_BEEP) {
		Logging::info(__func__, "stop beep packet received");
		GPIOController::configure_idle_flash();
		last_packet_received_timestamp = millis();
		send_packet(current_event_start_timestamp, packet.state);
	}


	if (packet.state == Network::State::IDLE) {
		Logging::info(__func__, "ACK packet received");
		last_packet_received_timestamp = millis();
		send_packet(current_event_start_timestamp, packet.state);
	}

}


void setup() {
	Logging::init();
	GPIOController::init(on_button_press);
}



void loop() {

	delay(10);
	GPIOController::tick();

	// handle wifi
	while (!is_wifi_connected()) {
		Logging::debug(__func__, "configuring wifi");
		GPIOController::configure_no_wifi();
		setup_wifi();
	}

	UDPPacket packet = UDPPacket(0, 0);
	if (read_udp_packet(packet) == NETWORK_SUCCESS) {
		Logging::debug(__func__, "handling packet");
		handle_packet(packet);
	}

	unsigned long current_time = millis();

	if (current_time - last_packet_received_timestamp > MAX_ACK_INTERVAL_ms) {

		static unsigned long last_seeking_connection_packet_sent = 0;

		if (current_time - last_seeking_connection_packet_sent > SEEKING_CONNECTION_REQUEST_INTERVAL_ms) {
			send_packet(0, Network::State::SEEKING_CONNECTION);
			last_seeking_connection_packet_sent = current_time;
		}

	}

}


/*

Let's think about what I need now

Start by connecting to wifi
Let the main loop handle the rest

:loop
	is_wifi_connected
	before doing anything we need to know we are still connected

	read_udp_packet
	then make another function to handle this packet
	this will usually read 0 bytes and exit straight away

	If last packet received is over theshold, send SEEKING_CONNECTION packet
	initial value should be 0 to force this to be run instantly

event callback, if button is pressed send STOP_BEEP packet




*/





