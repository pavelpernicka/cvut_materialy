#include <Servo.h>

// MG996R 180 stupnu; ukazkove meze upravit pri kalibraci.
constexpr int MIN_US = 500;
constexpr int MAX_US = 2500;
Servo servo;

void setup() {
  servo.attach(9, MIN_US, MAX_US);
  servo.writeMicroseconds(1500);
}

void loop() {
  const int adc = analogRead(A0);
  const int pulseUs = map(adc, 0, 1023, MIN_US, MAX_US);
  servo.writeMicroseconds(constrain(pulseUs, MIN_US, MAX_US));
  delay(20);
}
