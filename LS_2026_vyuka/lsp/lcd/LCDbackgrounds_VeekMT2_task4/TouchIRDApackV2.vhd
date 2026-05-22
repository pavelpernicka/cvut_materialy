-------------------------------------------------------------
-- CTU-FFE Prague, Dept. of Control Eng. [Richard Susta]
-- Published under GNU General Public License
-------------------------------------------------------------
-- Package is explained:
--cz: kapitola 7 v  https://dcenet.fel.cvut.cz/edu/fpga/doc/UvodDoVHDL1_concurrent_V20.pdf
--eng: Chapter 7 in https://dcenet.fel.cvut.cz/edu/fpga/doc/CircuitDesignWithVHDL_dataflow_and_structural_eng_V10.pdf 
---------------------------------------------------------------
library ieee; use ieee.std_logic_1164.all; use ieee.numeric_std.all; 
use work.LCDpackV2.all;

package TouchIRDApackV2 is 

 -- Touch modul
 component VeekMT2_I2CTouchLCD is
    port( CLOCK_50, LCD_DCLK, CLRN : in  std_logic := '0'; -- 50 MHz clock, LCD data, clear
          RDY_N : out std_logic := '1'; -- puls '0', if new touch coordinates arrived
	       touch1x, touch1y, touch2x, touch2y : out  xy_t  := XY_ZERO; -- 1st and 2nd touch coordinates
		    touchCount : out unsigned(1 downto 0):=(others=>'0'); -- 0, 1, 2 touches, or 3-more than 2 
		    touchGesture : out unsigned(2 downto 0):=(others=>'0');
		    -- gestures: 0-none; 1,2,3,4 Move up, left, down, right; 5,6  Zoom In, Out
	      TOUCH_INT_n : in std_logic:='0';	-- Veek-MT2 touch interrupt pin, it is required!!!	  
		   TOUCH_I2C_SDA : inout std_logic:='0'; -- Veek-MT2 I2C data bus
	      TOUCH_I2C_SCL : out std_logic:= '0'); -- Veek-MT2 I2C bus clock
  end component;
 -- IRDA modul sending data by RDY-ACK handshake
  component VeekMT2_IRDAv2 is
   generic(IRDA_REPEAT_WAIT_MS : natural := 500); -- wait time before sending the repetition of a pressed key
   port(LCD_DCLK       : in  std_logic; -- 33 MHz, LCD data clock 
         CLRN           : in  std_logic  := '0'; --Active in '0' clear signal
         IRDA_RXD       : in  std_logic  := '0'; -- VEEK_MT2 infrared input.
         AddressCommand : out std_logic_vector(15 downto 0) := (others => '0'); -- Address + Command
         RDY_Command    : out std_logic := '0'; -- Ut announces that a command is ready
         ACK_Command    : in  std_logic := '0'; -- User confirms reading of the
         CmdIsRepeated  : out std_logic := '0'; -- RDY_Command was initiated by IRDA repeating key mode
         IRDA_active    : out std_logic := '0');-- the IRDA sends data, debug flag
end component;

constant TOUCHDATASVL_LENGTH:integer:=2*10+2*9+2+3; -- x-coords, y-coords+count and gesture
subtype TouchDataSlv_t is std_logic_vector(TOUCHDATASVL_LENGTH-1 downto 0);

-- the record is analogy to struct. 
type TouchRecord_t is 
  record x1, y1, x2, y2 : integer range 0 to XCOLUMN_MAX; -- 1023, defined in LDCpackV2
         count : integer range 0 to 3; --number of touches, we process only 2 first
			gesture : integer range 0 to 7;  -- 1 Move up, 2 Move left, 3 Move down, 4 Move Right, 5 Zoom In, 6 Zoom Out, 0 none

  end record;
constant TouchRecord_ZERO : TouchRecord_t := (0,0,0,0,0,0);

-- conversion functions. The record cannot be in entity, so we send it as packed into std_logic_vector 
function to_TouchRecord(touchdata:touchDataSlv_t) return TouchRecord_t;

function to_TouchDataSlv(x1,y1,x2,y2,count, gesture:std_logic_vector) return TouchDataSlv_t;
function to_TouchDataSlv(touchRecord : TouchRecord_t) return TouchDataSlv_t;

end package TouchIRDApackV2;
----------------------------------------------------------------------------------------------------
package body TouchIRDApackV2 is


function to_TouchDataSlv(x1,y1,x2,y2,count, gesture:std_logic_vector) return TouchDataSlv_t is
variable result : TouchDataSlv_t:=(others=>'0');
begin -- The downto-ranges are hints to the compiler about exact sizes 
      -- and also the checking of supplied function argument correctness.
       result:=gesture(2 downto 0) & count(1 downto 0) 
		         & y2(8 downto 0)
					& x2(9 downto 0)
					& y1(8 downto 0)
					& x1(9 downto 0);
		 return result;
end function;

function to_TouchDataSlv(touchRecord : TouchRecord_t) return TouchDataSlv_t is
variable x1,x2: std_logic_vector(9 downto 0);
variable y1,y2: std_logic_vector(8 downto 0);
variable gesture: std_logic_vector(2 downto 0);
variable count: std_logic_vector(1 downto 0);
begin 
   x1:=std_logic_vector(to_unsigned(touchRecord.x1, x1'LENGTH));
   x2:=std_logic_vector(to_unsigned(touchRecord.x2, x2'LENGTH));
   y1:=std_logic_vector(to_unsigned(touchRecord.y1, y1'LENGTH));
   y2:=std_logic_vector(to_unsigned(touchRecord.y2, y2'LENGTH));
   gesture:=std_logic_vector(to_unsigned(touchRecord.gesture, gesture'LENGTH));
   count:=std_logic_vector(to_unsigned(touchRecord.count, count'LENGTH));
   return to_TouchDataSlv(x1,y1,x2,y2,count, gesture); 
end function;

function to_TouchRecord(touchdata:touchDataSlv_t) return TouchRecord_t is
variable H,L:integer range 0 to TouchDataSlv_t'HIGH; -- subscript high low
variable r : TouchRecord_t;
  function s2i(x:std_logic_vector) return integer is
  begin return to_integer(unsigned(x)); 
  end function;
begin 
-- VHDL also allows aggregates at the left assignment side, Qurtus Lite no,
-- so we must iterate. But all code will converted to constants in the compile-time.
      H:= 9; L:=0; 
		r.x1:=s2i(touchdata(H downto L)); L:=H+1; H:=H+9; -- for next y
		r.y1:=s2i(touchdata(H downto L)); L:=H+1; H:=H+10; -- for next x
		r.x2:=s2i(touchdata(H downto L)); L:=H+1; H:=H+9; -- for next y
		r.y2:=s2i(touchdata(H downto L)); L:=H+1; H:=H+2; -- for next count is 2 bits count
		r.count:=s2i(touchdata(H downto L)); L:=H+1; H:=H+3; -- for the next is 3 bits gesture
		r.gesture:=s2i(touchdata(H downto L));
		assert H=TouchDataSlv_t'HIGH report "Wrong ranges in toTouchRecord()" severity error;
		return r;
end function;

 
end package body TouchIRDApackV2;

