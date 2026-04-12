PROJECT := rs41
BUILD_DIR := build

CC := arm-none-eabi-gcc
OBJCOPY := arm-none-eabi-objcopy
SIZE := arm-none-eabi-size

CPUFLAGS := -mcpu=cortex-m3 -mthumb
CFLAGS := $(CPUFLAGS) -std=c11 -Os -g3 -ffreestanding -fno-builtin \
	-Wall -Wextra -Wshadow -Wundef -Wdouble-promotion -Wformat=2 \
	-ffunction-sections -fdata-sections -Iinclude -MMD -MP
LDFLAGS := $(CPUFLAGS) -T linker/stm32f100c8.ld -nostdlib -nostartfiles \
	-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/$(PROJECT).map -lgcc

SRCS := \
	src/startup_stm32f100c8.c \
	src/platform.c \
	src/uart.c \
	src/spi.c \
	src/adc.c \
	src/crc16.c \
	src/gps.c \
	src/protocol.c \
	src/si4032.c \
	src/main.c

OBJS := $(SRCS:src/%.c=$(BUILD_DIR)/%.o)
DEPS := $(OBJS:.o=.d)

ELF := $(BUILD_DIR)/$(PROJECT).elf
BIN := $(BUILD_DIR)/$(PROJECT).bin
HEX := $(BUILD_DIR)/$(PROJECT).hex

OPENOCD ?= openocd
OPENOCD_CFG ?= ./openocd_rs41.cfg
FLASH_SCRIPT := ./tools/flash_openocd.sh

.PHONY: all clean flash flash-unprotect size

all: $(BIN) $(HEX)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(BUILD_DIR)/%.o: src/%.c | $(BUILD_DIR)
	$(CC) $(CFLAGS) -c $< -o $@

$(ELF): $(OBJS)
	$(CC) $(OBJS) $(LDFLAGS) -o $@

$(BIN): $(ELF)
	$(OBJCOPY) -O binary $< $@

$(HEX): $(ELF)
	$(OBJCOPY) -O ihex $< $@

size: $(ELF)
	$(SIZE) $<

flash: $(ELF)
	OPENOCD="$(OPENOCD)" OPENOCD_CFG="$(OPENOCD_CFG)" $(FLASH_SCRIPT) $(ELF)

flash-unprotect:
	OPENOCD="$(OPENOCD)" OPENOCD_CFG="$(OPENOCD_CFG)" $(FLASH_SCRIPT) --unprotect

clean:
	rm -rf $(BUILD_DIR)

-include $(DEPS)
