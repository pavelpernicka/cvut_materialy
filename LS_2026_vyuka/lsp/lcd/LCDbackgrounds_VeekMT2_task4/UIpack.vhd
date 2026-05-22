-------------------------------------------------------------------------------
-- The definitions here are shared by UserInterface and LCDlogicTask4
--*********************************************************
-- The packages are explained:
--cz: kapitola 7 v  https://dcenet.fel.cvut.cz/edu/fpga/doc/UvodDoVHDL1_concurrent_V20.pdf
--eng: Chapter 7 in https://dcenet.fel.cvut.cz/edu/fpga/doc/CircuitDesignWithVHDL_dataflow_and_structural_eng_V10.pdf 
---------------------------------------------------------------
library ieee; use ieee.std_logic_1164.all; use ieee.numeric_std.all; 
use work.LCDpackV2.all;

package UIpack is

  -- central blinking box
  constant BLINK_SIZE : integer := 64;
  constant BLINK_XLEFT: integer :=(LCD_WIDTH-BLINK_SIZE)/2;
  constant BLINK_YTOP : integer :=(LCD_HEIGHT-BLINK_SIZE)/2;

  -- morse speed state
  constant SPEED_LEVEL_BITS : integer := 3;
  constant SPEED_LEVELS     : integer := 2**SPEED_LEVEL_BITS;
  
  -- pause at the end state
  constant PAUSE_LEVEL_BITS    : integer := 3;
  constant PAUSE_LEVELS        : integer := 2**PAUSE_LEVEL_BITS;

  -- play/pause button - top left
  constant PLAY_TOUCH_XCENTER : integer := 40;
  constant PLAY_TOUCH_YCENTER : integer := 36;
  constant PLAY_TOUCH_RADIUS  : integer := 20;

  -- plus/minus under the rainbow
  constant SPEED_MINUS_XCENTER : integer := 156;
  constant SPEED_MINUS_YCENTER : integer := 356;
  constant SPEED_PLUS_XCENTER  : integer := 644;
  constant SPEED_PLUS_YCENTER  : integer := 356;
  constant SPEED_TOUCH_RADIUS  : integer := 18;

  -- pause at the end controlls
  constant PAUSE_MINUS_XCENTER : integer := 700;
  constant PAUSE_MINUS_YCENTER : integer := 36;
  constant PAUSE_PLUS_XCENTER  : integer := 756;
  constant PAUSE_PLUS_YCENTER  : integer := 36;
  constant PAUSE_TOUCH_RADIUS  : integer := 18;
 
  -- button radius extension
  constant TCIRCLE :integer := 16;
 
 
end package;
----------------------------------------------------------------------------------------------------
package body UIpack is
 

	 
end package body;

