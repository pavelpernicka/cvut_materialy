CFLAGS += -std=c99 -Wall -Werror -pedantic -g

all: main queue
main: main.c
	clang $(CFLAGS) main.c -o main
queue: queue.c
	$(CC) $(CFLAGS) queue.c -o queue

clean:
	rm queue
	rm main