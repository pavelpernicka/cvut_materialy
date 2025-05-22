
#CC:=ccache $(CC)
CFLAGS+=-O2

OBJS=$(patsubst %.c,%.o,$(wildcard *.c))

CFLAGS+=-std=gnu99
#CFLAGS+=-std=c99
CFLAGS+=-pedantic -Wall

CFLAGS+=$(shell sdl2-config --cflags)
LDFLAGS+=$(shell sdl2-config --libs)
LDFLAGS+=-lSDL2_image

LDFLAGS+=-ljpeg

TARGET=texam

bin: $(TARGET)

$(OBJS): %.o: %.c
	$(CC) -c $< $(CFLAGS) $(CPPFLAGS) -o $@

$(TARGET): $(OBJS)
	$(CC) $(OBJS) $(LDFLAGS) -o $@

clean:
	$(RM) $(OBJS) $(TARGET)
	$(RM) -rf *.ppm *.jpg *.jpeg

