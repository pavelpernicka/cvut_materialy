#include "mbed.h"
 
DigitalOut myled(LED1);
BufferedSerial serial (USBTX, USBRX, 115200);
Ticker blinker;

void blink_n(uint32_t i, Kernel::Clock::duration_u32 t = 50ms){
    for(; i > 0; i--){
        myled = true;
        ThisThread::sleep_for(t);
        myled = false;
        ThisThread::sleep_for(t);
    }
}

void change(){
    myled = !myled;
}

void blink(Kernel::Clock::duration_u32 period){
    blinker.detach();
    blinker.attach(&change, period);
}
 
int main() {
    serial.set_blocking(true);
    const char init_msg = 'i';
    serial.write(&init_msg, 1);
    blink_n(5);
    while(true){
        char received_value;
        ssize_t received_in_fact = serial.read(&received_value, 1);
        char acknowledge_msg = 'a';
        if(received_in_fact == 1){
            switch(received_value){
                case 's': blinker.detach(); myled = true; break;
                case 'e': blinker.detach(); myled = false; break;
                case 'f': blinker.detach(); myled = !myled; break;
                case '0': blinker.detach(); break;
                case '1': blink(50ms); break;
                case '2': blink(100ms); break;
                case '3': blink(200ms); break;
                case '4': blink(500ms); break;
                case '5': blink(1000ms); break;
                default: acknowledge_msg = '!';
            }
        }else{
            acknowledge_msg = '*';
        }
        serial.write(&acknowledge_msg, 1);
    }
}

