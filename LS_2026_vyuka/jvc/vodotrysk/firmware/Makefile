PORT ?= /dev/ttyACM0

.PHONY: build flash monitor fullflash menuconfig erase web clean

build:
	idf.py build

flash:
	idf.py -p $(PORT) flash

monitor:
	idf.py -p $(PORT) monitor

fullflash:
	idf.py -p $(PORT) flash monitor

menuconfig:
	idf.py menuconfig

erase:
	idf.py -p $(PORT) erase-flash

web:
	python3 tools/pack_web.py

clean:
	idf.py clean
