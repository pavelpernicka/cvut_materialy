CFLAGS += -pedantic -Wall -std=c99 -g

all: main cal
main: main.c
	$(CC) $(CFLAGS) main.c -o main
cal: cal.c
	$(CC) $(CFLAGS) cal.c -o cal
	
debug: debug.c
	$(CC) $(CFLAGS) debug.c -o debug

clean:
	rm main
	rm cal
