CFLAGS+=  -pedantic -Wall -std=c99 -O3
all: main

main: main.c prg_serial.o
	$(CC) $(CFLAGS) main.c prg_serial.o -o main

prg_serial.o: prg_serial.c prg_serial.h
	$(CC) $(CFLAGS) -c prg_serial.c -o prg_serial.o
	
clean:
	$(RM) *.o
	$(RM) $(HW) prg_serial.so

.PHONY: clean zip
