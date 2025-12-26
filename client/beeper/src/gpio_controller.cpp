
#include <Arduino.h>

#include "gpio_controller.h"


#define GPIO_ALARM		22
#define GPIO_BUTTON		21
#define GPIO_LED_RED	20
#define GPIO_LED_GREEN	19


namespace GPIOController {

    namespace Buzzer {
		static bool is_enabled = false;
		static bool is_tone_playing = false;
		static unsigned long prev_millis = 0;
		static const unsigned long toggle_interval = 270;
		static const unsigned int tone_frequency = 100;

		static void init() {
			pinMode(GPIO_ALARM, OUTPUT);
			digitalWrite(GPIO_ALARM, LOW);
		}
		
        static void tick() {
			
			if (!is_enabled) {
				return;
			}
			
			unsigned long current_millis = millis();

			if (current_millis - prev_millis >= toggle_interval) {
				
				if (is_tone_playing) {
					noTone(GPIO_ALARM);
					is_tone_playing = false;
				} else {
					tone(GPIO_ALARM, tone_frequency);
					is_tone_playing = true;
				}

				prev_millis = current_millis;
			}

		}

        static void enable() {
			is_enabled = true;
		}

        static void disable() {
			noTone(GPIO_ALARM);
			digitalWrite(GPIO_ALARM, LOW);
			is_enabled = false;
			is_tone_playing = false;
		}
    };

    namespace LED {
		static pin_size_t active_flash_pin = -1;
		static unsigned long prev_millis = 0;
		static const uint32_t led_on_duration = 250;
		static const uint32_t led_off_duration = 250;

		static void init() {
			pinMode(GPIO_LED_RED, OUTPUT);
			pinMode(GPIO_LED_GREEN, OUTPUT);
			digitalWrite(GPIO_LED_RED, LOW);
			digitalWrite(GPIO_LED_GREEN, LOW);
		}

        static void tick() {
			if (active_flash_pin == -1) {
				return;
			}

			PinStatus pin_state = digitalRead(active_flash_pin);
			int interval = pin_state ? led_on_duration : led_off_duration;
			unsigned long current_millis = millis();

			if (current_millis - prev_millis >= interval) {
				prev_millis = current_millis;
				digitalWrite(active_flash_pin, !pin_state);
			}
		}

        static void set_none() {
			active_flash_pin = -1;
			digitalWrite(GPIO_LED_RED, LOW);
			digitalWrite(GPIO_LED_GREEN, LOW);
		}

        static void set_red() {
			active_flash_pin = -1;
			digitalWrite(GPIO_LED_RED, HIGH);
			digitalWrite(GPIO_LED_GREEN, LOW);
		}

        static void set_green() {
			active_flash_pin = -1;
			digitalWrite(GPIO_LED_RED, LOW);
			digitalWrite(GPIO_LED_GREEN, HIGH);
		}

        static void flash_red() {
			active_flash_pin = GPIO_LED_RED;
			digitalWrite(GPIO_LED_GREEN, LOW);
		}

        static void flash_green() {
			active_flash_pin = GPIO_LED_GREEN;
			digitalWrite(GPIO_LED_RED, LOW);
		}
    };


	void init(void(*button_press_callback)()) {
		Buzzer::init();
		LED::init();
		pinMode(GPIO_BUTTON, INPUT_PULLUP);
		attachInterrupt(digitalPinToInterrupt(GPIO_BUTTON), button_press_callback, FALLING);
	}

    void tick() {
		Buzzer::tick();
		LED::tick();
	}

    void configure_no_wifi() {
		Buzzer::disable();
		LED::flash_red();
	}

    void configure_idle_flash() {
		Buzzer::disable();
		LED::flash_green();
	}

    void configure_alarm() {
		Buzzer::enable();
		LED::set_red();
	}

};