#include <LiquidCrystal.h>

LiquidCrystal lcd(7, 8, 9, 10, 11, 12);

const int BUTTON_PIN = 2;
bool listening = false;
bool lastButtonState = HIGH;

void setup() {
  Serial.begin(9600);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  lcd.begin(16, 2);
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("lulu.ai...");
}

void loop() {
  // Toggle button — press once = START, press again = STOP
  bool buttonState = digitalRead(BUTTON_PIN);
  if (lastButtonState == HIGH && buttonState == LOW) {
    delay(50);  // debounce
    if (!listening) {
      Serial.println("START");
      listening = true;
    } else {
      Serial.println("STOP");
      listening = false;
    }
  }
  lastButtonState = buttonState;

  // Update LCD from status strings sent by Python
  if (Serial.available()) {
    String status = Serial.readStringUntil('\n');
    status.trim();
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print(status.substring(0, 16));
  }
}
