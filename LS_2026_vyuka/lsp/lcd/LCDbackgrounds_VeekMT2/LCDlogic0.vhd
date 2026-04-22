-------------------------------------------------------------
-- LCD image created by logic
-------------------------------------------------------------

library ieee, work; use ieee.std_logic_1164.all; 
use ieee.numeric_std.all; -- for integer and unsigned types
use work.LCDpackV2.all;
entity LCDlogic0 is
    port(xcolumn, yrow  : in  xy_t  := XY_ZERO; -- x, y-coordinate of pixel (column, row indexes)
           XEND_N   : in  std_logic := '0'; -- 32.2 kHz'; '0' only when xcolumn=XCOLUMN_MAX, otherwise '1;
           YEND_N   : in  std_logic := '0'; -- 61.4 Hz; '0' only when max yrow=YROW_MAX, otherwise '1',
           LCD_DE   : in  std_logic := '0';   -- DataEnable indicates the visible part of LCD
           LCD_DCLK : in  std_logic := '0'; -- 33 MHz exactly; LCD data clock
          RGBcolor : out RGB_t); --  defined in LCDpackV2; RGB_t = std_logic_vector(23 downto 0)
end entity;
architecture behavioral of LCDlogic0 is
  constant DARKBLUE: RGB_t := ToRGB(0, 0, 139); -- the background
  begin -- architecture
  
LSPimage : process( xcolumn, yrow, LCD_DE)
-- In any process, we prefer variables. They must be initialized in the code!!!
-- The values after definitions are mainly for simulations. 
   variable RGB :RGB_t := DARKBLUE; -- the color of pixel 
   variable x : integer  range 0 to XCOLUMN_MAX:=0; 
   variable y : integer  range 0 to YROW_MAX:=0; 
  begin 
     x := to_integer(xcolumn); y := to_integer(yrow); -- we convert unsigned inputs to integers
     ---------- our image -------------------------
     RGB :=DARKBLUE;   
     
     if x<LCD_WIDTH/2 xor y<LCD_HEIGHT/2 then RGB:=GREEN; end if; -- chess pattern
     ------------------------------------------------------------
     if LCD_DE = '0' then  RGB  := BLACK; end if; -- auxiliary clipping to LCD visible area
    
	   RGBcolor <= RGB; -- assigning to output at the end
   end process;
	
end architecture;


 