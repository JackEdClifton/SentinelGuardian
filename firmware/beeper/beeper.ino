
#include <WiFi.h>
#include <WiFiUdp.h>

#include "wifi_creds.h"

const int UDP_PORT = 5005;

WiFiUDP udp;

namespace DoorCodes {
  const char* NOTHING = "nodata";
  const char* ALARM = "getfuckingdoorucunts";
};


const int GPIO_ALARM = 20;

void alarm() {
  for (int repeat = 0; repeat < 2; repeat++) {
    for (int i = 0; i < 16; i++) {
      tone(GPIO_ALARM, 2000);  // 2kHz tone
      delay(100);              // tone duration
      noTone(GPIO_ALARM);      // stop tone
      delay(50);               // pause between beeps
    }
    digitalWrite(GPIO_ALARM, LOW);
    delay(200);                // pause between sequences
  }
}


void setup_wifi() {
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("Connecting to wifi\n");
  delay(5000);

  while (WiFi.status() != WL_CONNECTED) {
    Serial.print("Not connected to wifi\n");
    digitalWrite(GPIO_ALARM, HIGH);

  switch (WiFi.status()) {
      case WL_IDLE_STATUS: Serial.println("WL_IDLE_STATUS"); break;
      case WL_NO_SSID_AVAIL: Serial.println("WL_NO_SSID_AVAIL"); break;
      case WL_CONNECT_FAILED: Serial.println("WL_CONNECT_FAILED"); break;
//      case WL_WRONG_PASSWORD: Serial.println("WL_WRONG_PASSWORD"); break;
      case WL_DISCONNECTED: Serial.println("WL_DISCONNECTED"); break;
      case WL_CONNECTED: Serial.println("WL_CONNECTED"); break;
      default: Serial.println("UNKNOWN");
    }


    delay(500);
  }
  digitalWrite(GPIO_ALARM, LOW);

  udp.begin(UDP_PORT);
}


bool read_parse_udp_packet() {
  int packet_size = udp.parsePacket();
  if (!packet_size) {
    return 0;
  }

  char buffer[128];
  int len = udp.read(buffer, sizeof(buffer) -1);
  if (len <= 0) {
    return 0;
  }

  buffer[len] = 0;

  if (strcmp(buffer, DoorCodes:: NOTHING) == 0) {
    return 0;
  }

  if (strcmp(buffer, DoorCodes:: ALARM) == 0) {
    return 1;
  }

  return 0; // can't be sure

}


void setup() {
  Serial.begin(115200);
  pinMode(GPIO_ALARM, OUTPUT);
  digitalWrite(GPIO_ALARM, LOW);
  setup_wifi();
}



void loop() {

  if (read_parse_udp_packet()) {
    for (int i = 10; i; i--) {
      alarm();
      delay(2000);
    }

  }

  delay(50);
}





