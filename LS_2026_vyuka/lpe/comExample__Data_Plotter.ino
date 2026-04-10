HardwareSerial Serial2(PA3_ALT1, PA2_ALT1);

HardwareTimer htim3 = HardwareTimer(TIM3);


char rx_buf[256];
int rx_ptr = 0;

int i = 0;


const int analogInPin = PA_0;  
int sensorValue = 0;  


void setup() {
  // put your setup code here, to run once:
  Serial2.begin(9600);
  htim3.setPWM(3, PB_0_ALT1, 20, 50);
  
}
void loop() {
  // put your main code here, to run repeatedly:
  if (Serial2.available() > 0) {
    rx_buf[rx_ptr] = Serial2.read();
    if (rx_buf[rx_ptr] == '\n') {
      rx_buf[rx_ptr + 1] = 0;
     
      switch(rx_buf[0]){
        case '*':
          i=atoi(&rx_buf[1]);
          Serial2.println(i);
          htim3.setCaptureCompare(3, i, PERCENT_COMPARE_FORMAT);  // 50%
        break;

        default:
          Serial2.print(rx_buf);
        break;

      }


      rx_ptr=0;
    } else {
      rx_ptr++;
    }
  }
  analogReadResolution(12);
  sensorValue=analogRead(analogInPin);
  
  Serial2.printf("$$P%f,%f\r\n",(millis()/1000.0),(sensorValue/4096.0)*3.3);
  delay(10);

 // htim3.setCaptureCompare(3, 50, PERCENT_COMPARE_FORMAT);  // 50%
 // delay(10);
 // htim3.setCaptureCompare(3, 00, PERCENT_COMPARE_FORMAT);  // 50%
  //delay(990);
}

