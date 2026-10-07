PORT ?= /dev/ttyACM0
IDF_TARGET ?= esp32s3
FLASH_AFTER ?= no-reset

.PHONY: build flash monitor fullflash menuconfig erase web clean set-target ensure-target

set-target:
	idf.py set-target $(IDF_TARGET)

ensure-target:
	@if [ ! -f build/CMakeCache.txt ] || ! grep -q 'IDF_TARGET:STRING=$(IDF_TARGET)' build/CMakeCache.txt || [ ! -f sdkconfig ] || ! grep -q 'CONFIG_IDF_TARGET="$(IDF_TARGET)"' sdkconfig; then \
		echo "Synchronizing ESP-IDF target to $(IDF_TARGET)"; \
		idf.py set-target $(IDF_TARGET); \
	fi

build: ensure-target
	idf.py -DIDF_TARGET=$(IDF_TARGET) build

flash: ensure-target
	SERIAL_TOOL_EXTRA_ARGS="--after=$(FLASH_AFTER)" idf.py -DIDF_TARGET=$(IDF_TARGET) -p $(PORT) flash

monitor: ensure-target
	idf.py -DIDF_TARGET=$(IDF_TARGET) -p $(PORT) monitor

fullflash: ensure-target
	SERIAL_TOOL_EXTRA_ARGS="--after=$(FLASH_AFTER)" idf.py -DIDF_TARGET=$(IDF_TARGET) -p $(PORT) flash monitor

menuconfig: ensure-target
	idf.py -DIDF_TARGET=$(IDF_TARGET) menuconfig

erase: ensure-target
	idf.py -DIDF_TARGET=$(IDF_TARGET) -p $(PORT) erase-flash

web:
	python3 tools/pack_web.py

clean:
	idf.py -DIDF_TARGET=$(IDF_TARGET) clean
