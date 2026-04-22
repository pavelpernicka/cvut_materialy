TBNAME := testbenchV2_LCDlogic
FILES := LCDpackV2.vhd balon.vhd LCDlogicMy.vhd $(TBNAME).vhd
SIM_TIME ?= 20ms
GHDL ?= ghdl-gcc
GTKWAVE ?= gtkwave
GHDL_FLAGS := -fsynopsys --std=08
TB_EXE := $(shell printf '%s' '$(TBNAME)' | tr '[:upper:]' '[:lower:]')
BUILD_DIR := build
WAVE_FILE ?= $(BUILD_DIR)/$(TBNAME).ghw
ANALYZE_STAMP := $(BUILD_DIR)/analyze.stamp
ELABORATE_STAMP := $(BUILD_DIR)/elaborate.stamp

.PHONY: all analyze elaborate run wave show view gtkview gtkwave lcd-image lcd-show clean

all: run

analyze: $(ANALYZE_STAMP)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(ANALYZE_STAMP): $(FILES) | $(BUILD_DIR)
	cd $(BUILD_DIR) && $(GHDL) -a $(GHDL_FLAGS) $(addprefix ../,$(FILES))
	touch $(ANALYZE_STAMP)

elaborate: $(ELABORATE_STAMP)

$(ELABORATE_STAMP): $(ANALYZE_STAMP)
	cd $(BUILD_DIR) && $(GHDL) -e $(GHDL_FLAGS) $(TBNAME)
	touch $(ELABORATE_STAMP)

run: elaborate
	$(BUILD_DIR)/$(TB_EXE) --stop-time=$(SIM_TIME)

wave: elaborate
	$(BUILD_DIR)/$(TB_EXE) --stop-time=$(SIM_TIME) --wave=$(WAVE_FILE)

show: wave
	$(GTKWAVE) $(WAVE_FILE) >/dev/null 2>&1 &

view: show

gtkview: show

gtkwave: show

lcd-image: run
	python3 show_lcd_output.py --no-open

lcd-show: run
	python3 show_lcd_output.py

clean:
	rm -rf $(BUILD_DIR) .build .build-ghdl-gcc
	rm -f work-obj08.cf work-obj93.cf $(TBNAME) $(WAVE_FILE) \
		*.o e~*.o testbenchv2_lcdlogic \
		simulation/testbenchLCD.txt simulation/testbenchLCD.ppm \
		simulation/testbenchLCD.png simulation/testbenchLCD_full.png
