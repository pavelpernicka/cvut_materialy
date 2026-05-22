========================================================
 @README for Version B with the simplified UI 
 - the list of Touch and IRDA remote basic files
========================================================

Demo_ControlPanel.bdf - top-level entity
  -- Important note: VeekMT2_LCDgenV2 should have the instance name "iLCDgenerator" 
  -- that is referred from the TimeQuest Analyzer definitions VeekMT2_LCD.sdc
  
UserInterfaceV2.vhd -- UI (User Interface) for processing touch LCD and IRDA remote
LCDlogicTask4.vhd -- image drawing according to parameters sent from UI

--------- packages --------------------------------
LCDpackV2.vhd -- LCD definitions
TouchIRDApack.vhd - definitions for Touch module and IRDA remote
UIpack.vhd -- the shered definition UI and LCDlogic* and related only to this solution

==========================================================
LCDlogicTask4testbench.vhd -- it embeds LCDlogicTask4 with the testbench replacement of UI
testbenchV2_ControlPanel.vhd  -- performs multi-frame testbench by simulating LCDlogicTask4testbench.vhd.

simulation/runMoreFrames.bat  -- batch file for running simulation in GHDL

=================================================================
*** VeekMT2 files
VeekMT2_LCDgenV2.vhd - LCD generator
VeekMT2_LCDregV2.vhd - LCD register

---------------------------------------------------------------------------
-- The following modules are embedded in UserInterfaceV2.vhd 
-  Add them in your project file list, but do not insert them into a BDF schema! 
---------------------------------------------------------------------------
VeekMT2_IRDAv2.vhd - IRDA remote module version 2 containing a newly added time filter 
-- that suppresses too-fast repetitions of pressed keys from remote controls.

VeekMT2_I2CTouchLCD.vhd - the LCD touch module for I2C bus
I2C/i2c_touch_config_v2.v  - processing I2C interface written in Verilog

====================================================================
VeekMT2_PinAssignments.csv - Pin Assignments of VeekMT2 board

*** TimeQuest Analyzer files - always copy them into each LCD Quartus project

VeekMT2.sdc - basic definitions for TimeQuest Analyzer
VeekMT2_LCD.sdc - added definition for VeekMT2_LCDgenV2 with the instance name "iLCDgenerator"


