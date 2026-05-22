--------------------------------------------------------
-- The entity is intended only for using in testbenchV2_ControlPanel.vhd only
-- It replaces UserInterface by simulating its outputs
-------------------------------------------------------------------------
library ieee, work; use ieee.std_logic_1164.all; use ieee.numeric_std.all; 
use work.LCDpackV2.all; 
use work.TouchIRDApackV2.all; -- package for Touch and IRDA
use work.UIpack.all; -- definitiona releated to this ControlPanel solution

entity LCDlogic4testbench is 
    port(xcolumn  : in  xy_t; -- x-coordinate of pixel (column index)
         yrow     : in  xy_t; -- y-coordinate of pixel (row index)
         XEND_N   : in  std_logic; -- '0' only when xcolumn=1023, otherwise '1', f=32227 Hz= 33e6/1024 
         YEND_N   : in  std_logic; -- '0' only when yrow=524, otherwise '1', f=61.384 Hz = 33e6/(1024*525)
         LCD_DE   : in  std_logic; -- DataEnable control signal of LCD controller
         LCD_DCLK : in  std_logic; -- LCD data clock, exactly 33 MHz
         RGBcolor : out RGB_t);         --  color data type RGB_t = std_logic_vector(23 downto 0), defined in LCDpackage
end entity;
 
architecture rtl OF LCDlogic4testbench IS 

component LCDlogicTask4 is
    generic(IsTestbench:boolean:=FALSE);
    port(morseBit           : in  std_logic:='0';
         morseDash          : in  std_logic:='0';
         morseStop          : in  std_logic:='0';
         morseIndex         : in  unsigned(5 downto 0):=(others=>'0');
         xcolumn  : in  xy_t      := XY_ZERO; -- x-coordinate of pixel (column index)
         yrow     : in  xy_t      := XY_ZERO; -- y-coordinate of pixel (row index)
         XEND_N   : in  std_logic := '0'; -- '0' only when xcolumn=1023, otherwise '1', f=32227 Hz= 33e6/1024 
         YEND_N   : in  std_logic := '0'; -- '0' only when yrow=524, otherwise '1', f=61.384 Hz = 33e6/(1024*525)
         LCD_DE   : in  std_logic := '0'; -- DataEnable control signal of LCD controller
         LCD_DCLK : in  std_logic := '0'; -- LCD data clock, exactly 33 MHz
         touchCoordinates : in   TouchDataSlv_t := (others => '0'); -- coordinates packet to std_logic_vector 
         commandStop        : in  std_logic:='0'; -- '1' if stopped
         pauseCountdown     : in  unsigned(PAUSE_LEVEL_BITS-1 downto 0):=(others=>'0');
         pauseLevel         : in  unsigned(PAUSE_LEVEL_BITS-1 downto 0):=(others=>'0');
         speedLevel         : in  unsigned(SPEED_LEVEL_BITS-1 downto 0):=(others=>'0');
         RGBcolor : out RGB_t:=BLACK);
end component;

signal touchCoordinates_s :  TouchDataSlv_t:=(others=>'0');
signal commandStop_s :  std_logic:='0';
signal speedLevel_s : unsigned(SPEED_LEVEL_BITS-1 downto 0):=to_unsigned(SPEED_LEVELS-1, SPEED_LEVEL_BITS);
signal pauseLevel_s : unsigned(PAUSE_LEVEL_BITS-1 downto 0):=(others=>'0');
signal pauseCountdown_s : unsigned(PAUSE_LEVEL_BITS-1 downto 0):=(others=>'0');
signal morseBit_s, morseDash_s, morseStop_s : std_logic:='0';
signal morseIndex_s : unsigned(5 downto 0):=(others=>'0');

begin 
 iMorse : entity work.MorseEngine
    generic map(IsTestbench=>true)
    port map(LCD_DCLK=>LCD_DCLK, YEND_N=>YEND_N, commandStop=>commandStop_s, pauseLevel=>pauseLevel_s, speedLevel=>speedLevel_s,
             morseBit=>morseBit_s, morseDash=>morseDash_s, morseStop=>morseStop_s, morseIndex=>morseIndex_s,
             pauseCountdown=>pauseCountdown_s);

   -- we inserted the instance of LCDlogicTask4
iLogic : LCDlogicTask4
    generic map(IsTestbench=>true)
    port map(morseBit=>morseBit_s, morseDash=>morseDash_s, morseStop=>morseStop_s, morseIndex=>morseIndex_s,
             xcolumn=>xcolumn,  yrow=>yrow,  XEND_N=>XEND_N, YEND_N=>YEND_N,  LCD_DE=>LCD_DE, LCD_DCLK=>LCD_DCLK,
             touchCoordinates=>touchCoordinates_s,   commandStop=>commandStop_s, pauseCountdown=>pauseCountdown_s, pauseLevel=>pauseLevel_s,
             speedLevel=>speedLevel_s,
             RGBcolor=>RGBcolor);         

 -- we substitute UserInterface by generating its outputs

testGenerator : process(YEND_N)               
   variable tr:TouchRecord_t:=TouchRecord_ZERO;
   variable cntrSimStep:integer range 0 to 31:=0;  -- for generating test signals  
begin
      if falling_edge(YEND_N) then -- YEND_N='0' in the last row of LCD frames
        -- zmena speed pomoci simulace kliknuti na tlacitka
		  tr:=TouchRecord_ZERO;
        if cntrSimStep>=3 and cntrSimStep<3+SPEED_LEVELS then
            tr.count:=1;
            tr.x1:=SPEED_MINUS_XCENTER;
            tr.y1:=SPEED_MINUS_YCENTER;
        end if;
        
		  -- We increment the simulation counter for 32 LCD frames
		  if cntrSimStep<31 then cntrSimStep:=cntrSimStep+1; end if;
          if cntrSimStep < 3 then
            speedLevel_s <= to_unsigned(SPEED_LEVELS-1, speedLevel_s'length);
          elsif cntrSimStep < 3 + SPEED_LEVELS then
            speedLevel_s <= to_unsigned(SPEED_LEVELS - 1 - (cntrSimStep - 3), speedLevel_s'length);
         elsif cntrSimStep < 3 + SPEED_LEVELS + 2 then
            speedLevel_s <= (others => '0');
         else
            speedLevel_s <= to_unsigned(SPEED_LEVELS-1, speedLevel_s'length);
         end if;
         pauseLevel_s <= to_unsigned(4, pauseLevel_s'length);
       
         commandStop_s<='0';

		end if; -- if falling_edge(YEND_N)
		
	  touchCoordinates_s<=to_TouchDataSlv(tr); -- pack tr of TouchRecord_t type to std_logic_vector 
  end process;

end architecture;
