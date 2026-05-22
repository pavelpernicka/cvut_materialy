TBNAME := testbenchV2_ControlPanel
FILES := LCDpackV2.vhd TouchIRDApackV2.vhd UIpack.vhd balon_noshadow_white_opt.vhd PERNIC.vhd VeekMT2_I2CTouchLCD.vhd \
	VeekMT2_IRDAv2.vhd UserInterfaceV2.vhd morse_my.vhd MorseEngine.vhd \
	LCDlogicTask4.vhd LCDlogic4testbench.vhd $(TBNAME).vhd
SIM_TIME ?= 140ms
FRAME_COUNT ?= 8
VIDEO_FPS ?= 1
GHDL ?= ghdl-gcc
GTKWAVE ?= gtkwave
GHDL_FLAGS := -fsynopsys --std=08
TB_EXE := $(shell printf '%s' '$(TBNAME)' | tr '[:upper:]' '[:lower:]')
BUILD_DIR := build
WAVE_FILE ?= $(BUILD_DIR)/$(TBNAME).ghw
ANALYZE_STAMP := $(BUILD_DIR)/analyze.stamp
ELABORATE_STAMP := $(BUILD_DIR)/elaborate.stamp

.PHONY: all analyze elaborate run wave show view gtkview gtkwave lcd-image lcd-show lcd-frames lcd-video lcd-frames-full lcd-video-full clean

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
	-$(BUILD_DIR)/$(TB_EXE) -gCOUNT_OF_FRAMES_G=$(FRAME_COUNT) --stop-time=$(SIM_TIME)

wave: elaborate
	-$(BUILD_DIR)/$(TB_EXE) -gCOUNT_OF_FRAMES_G=$(FRAME_COUNT) --stop-time=$(SIM_TIME) --wave=$(WAVE_FILE)

show: wave
	$(GTKWAVE) $(WAVE_FILE) >/dev/null 2>&1 &

view: show

gtkview: show

gtkwave: show

lcd-image: run
	python3 show_lcd_output.py --no-open

lcd-show: run
	python3 show_lcd_output.py

lcd-frames: run
	python3 show_lcd_output.py --all-frames --no-open

lcd-video: run
	python3 show_lcd_output.py --all-frames --video --fps $(VIDEO_FPS) --no-open

lcd-frames-full:
	$(MAKE) FRAME_COUNT=32 SIM_TIME=550ms lcd-frames

lcd-video-full:
	$(MAKE) FRAME_COUNT=32 SIM_TIME=550ms VIDEO_FPS=1 lcd-video

clean:
	rm -rf $(BUILD_DIR) .build .build-ghdl-gcc
	rm -f work-obj08.cf work-obj93.cf $(TBNAME) $(WAVE_FILE) \
		*.o e~*.o testbenchv2_controlpanel \
		simulation/testbenchLCD.txt simulation/testbenchLCD.ppm \
		simulation/testbenchLCD.png simulation/testbenchLCD_full.png \
		simulation/testbenchLCD.mp4
	rm -rf simulation/frames
