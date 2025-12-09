
#include <Arduino.h>

#include "LED_control.h"

void heartbeat_RED_LED_tick() {
  int interval = digitalRead(GPIO_LED_RED) ? 250 : 250;
  static unsigned long prev_millis = 0;
  unsigned long current_millis = millis();
  if (current_millis - prev_millis >= interval) {
    prev_millis = current_millis;
    digitalWrite(GPIO_LED_RED, !digitalRead(GPIO_LED_RED));
  }
}