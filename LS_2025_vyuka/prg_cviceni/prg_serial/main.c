#include <stdio.h>
#include <stdbool.h>
#include <stdlib.h>
#include <signal.h>
 
#include "prg_serial.h"

void sig_handler(int signal_code) {
  serial_set_raw(0);
  exit(0);
}

int main(int argc, char *argv[]){
	signal(SIGINT, sig_handler);
	int ret = 0;
	char c;
	const char *serial = argc > 1 ? argv[1] : "/dev/ttyACM0";
	int fd = serial_open(serial);
	if (fd != -1) { // read from serial port
	   	serial_set_raw(1); // set the raw mode
   		_Bool quit = 0;
   	while (!quit) {
      	if ((c = getchar()) == 's' || c == 'e' || c == 'f' || (c > 48 && c < 54)) {
         	if (serial_putc(fd, c) == -1) {
            	fprintf(stderr, "ERROR: Error in received responses\n");
            	quit = 1;
         	}else{
         		fprintf(stdout, "Sent\n");
         		char rec = serial_getc(fd);
         		if(rec=='a'){
         			fprintf(stdout, "OK\n");
         		}else{
         			fprintf(stdout, "KO\n");
         		}
         	}
      	}
      	quit = c == 'q';
   	} // end while()
   	serial_close(fd);
   	serial_set_raw(0);
	} else {
   		fprintf(stderr, "ERROR: Cannot open device %s\n", serial);
	}
	return ret;
}
