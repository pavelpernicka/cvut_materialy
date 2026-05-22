-------------------------------------------------------------
-- CTU-FFE Prague, Dept. of Control Eng. [Richard Susta]
-- Published under GNU General Public License
-------------------------------------------------------------

library ieee, work; use ieee.std_logic_1164.all; use ieee.numeric_std.all; -- for integer and unsigned types
use work.LCDpackV2.all;
use work.TouchIRDApackV2.all; -- package for Touch and IRDA
 
entity VeekMT2_I2CtouchLCD is
     port( CLOCK_50 : in  std_logic := '0'; -- 50 MHz clock
	         LCD_DCLK : in  std_logic := '0'; -- LCD data clock, 33 MHz exactly
		       CLRN : in std_logic := '0'; -- clear signal
           RDY_N : out std_logic := '1'; -- puls '0' if new value
			     TouchData : out TouchDataSlv_t := (others=>'0');
	         TOUCH_INT_n : in std_logic:='0';		  
			     TOUCH_I2C_SDA : inout std_logic:='0';
	         TOUCH_I2C_SCL : out std_logic:= '0');
end entity;

----==========================================================================================

architecture rtl of VeekMT2_I2CtouchLCD is

component i2c_touch_config_v2
	port
	(
		iClk		: in std_logic;  -- CLOCK_50 is required
		iRSTN		: in std_logic;  -- reset on '0'
		oREADY	: out std_logic; -- READY
		INT_n		: in std_logic;
		oREG_x1	: out std_logic_vector(9 downto 0);
		oREG_y1	: out std_logic_vector(8 downto 0);
		oREG_x2	: out std_logic_vector(9 downto 0);
		oREG_y2	: out std_logic_vector(8 downto 0);
		oREG_x3	: out std_logic_vector(9 downto 0);
		oREG_y3	: out std_logic_vector(8 downto 0);
		oREG_x4	: out std_logic_vector(9 downto 0);
		oREG_y4	: out std_logic_vector(8 downto 0);
		oREG_x5	: out std_logic_vector(9 downto 0);
		oREG_y5	: out std_logic_vector(8 downto 0);
		oREG_gesture	  : out std_logic_vector(7 downto 0);
		oREG_touch_count : out std_logic_vector(3 downto 0);
		I2C_SDAT	: inout std_logic;
		I2C_SCLK	: out std_logic);
end component;

signal touchReady : std_logic := '0';
signal x1in, x2in : std_logic_vector(9 downto 0);
signal y1in, y2in : std_logic_vector(8 downto 0);
signal touchCountIn : std_logic_vector(3 downto 0):=(others=>'0');
signal gestureIn  : std_logic_vector(7 downto 0);
signal watchDog : boolean := false; -- clearing touch count
-- local record for storing RAW data from I2C
type I2SDataSlvRecord_t is
	  record 
	     RDY  : std_logic;
	     x1, x2 : std_logic_vector(9 downto 0); 
	     y1, y2 : std_logic_vector(8 downto 0); 
		   count : std_logic_vector(3 downto 0);
	     gesture : std_logic_vector(7 downto 0);
end record;
constant I2SDataSlvRecord_ZERO:I2SDataSlvRecord_t:= ('0', (others=>'0'),(others=>'0'), (others=>'0'), (others=>'0'),(others=>'0'), (others=>'0')); 
-- synchronizer definitions
constant SYNCHRONIZER_END : positive := 1;
type synarr_t is array(0 to SYNCHRONIZER_END) of I2SDataSlvRecord_t;
signal synarr : synarr_t; -- synchronizer array
attribute ramstyle : string; -- Quartus attribute
-- The attribute tells the Quartus that synarr must not be implementing by SRAM memory
attribute ramstyle of synarr : signal is "logic";

signal SD, sLCD:I2SDataSlvRecord_t:=I2SDataSlvRecord_ZERO;
signal CLK2 :std_logic:='0'; -- CLOCK_50 divided by 2
begin -- architecture

iTouch : i2c_touch_config_v2 port map(iClk=>CLOCK_50, iRSTN=>CLRN, oREADY=>touchReady, INT_n=>TOUCH_INT_n,
           oREG_x1=>x1in, oREG_y1=>y1in, oREG_x2=>x2in, oREG_y2=>y2in, oREG_gesture=>gestureIn,
			  oREG_touch_count=>touchCountIn, I2C_SDAT=>TOUCH_I2C_SDA, I2C_SCLK=>TOUCH_I2C_SCL);
			  
			  -- We lead signals from the CLOCK_50 (50 MHz) clock domain
			  -- to the LCD_DCKL (33 MHz) clock domain of our LCD.
			  -- Any crossing of clock domains requires synchronizers,
			  -- but they work only from slower to faster clocks!!!
			  -- Thus, we divide CLOCK_50 by 2 to 25 MHz and strobe input data by it
			  -- so they change with less frequency than LCD_DCLK.
			  CLK2<=not CLK2 when falling_edge(CLOCK_50);
			  SD <= (RDY=>touchReady,x1=>x1in,x2=>x2in, y1=>y1in,y2=>y2in,
			        count=>touchCountIn,gesture=>gestureIn) when falling_edge(CLK2);

synchro : process(LCD_DCLK) -- synchronizer between clock domains
			 begin
			 if rising_edge(LCD_DCLK) then 
				   sLCD<=synarr(0); synarr(SYNCHRONIZER_END)<=SD;
			 isyn: for i in 0 to SYNCHRONIZER_END-1 loop synarr(i)<=synarr(i+1); end loop;
			 end if;
		  end process;


	 -- The synchronizer by LCD_DCLK	 
pTouchLCD : process(LCD_DCLK, CLRN)
   variable preReady, isRDY_n:std_logic:='1';
   variable reset : std_logic:='1';
   variable touchDataSlv : TouchDataSlv_t:=(others=>'0');
	variable touchCount, touchCountReg : std_logic_vector(1 downto 0):=(others=>'0'); 
   variable touchGesture : std_logic_vector(2 downto 0):=(others=>'0');
	variable  x1, x2 : std_logic_vector(9 downto 0); 
	variable  y1, y2 : std_logic_vector(8 downto 0); 
   begin -- process
	   if CLRN='0' then reset:='1';
	   elsif rising_edge(LCD_DCLK) then
		    touchGesture:="000";
	       if reset then 
			       reset:='0'; preReady:='1'; touchDataSlv:=(others=>'0');
					 touchCountReg:=(others=>'0'); 
					 x1:=(others=>'0');x2:=(others=>'0');
					 y1:=(others=>'0');y2:=(others=>'0');
	       elsif preready='0' and sLCD.RDY='1' then
			     x1:=sLCD.x1; x2:=sLCD.x2; y1:=sLCD.y1; y2:=sLCD.y2;
   	        case unsigned(sLCD.gesture) is
		          when X"10"=> touchGesture:="001"; -- 1 Move up
		          when X"14"=> touchGesture:="010"; -- 2 Move left
		          when X"18"=> touchGesture:="011"; -- 3 Move down
		          when X"1C"=> touchGesture:="100"; -- 4 Move Right
		          when X"48"=> touchGesture:="101"; -- 5 Zoom In
		          when X"49"=> touchGesture:="110"; -- 6 Zoom Out
	            when others=> touchGesture:="000"; -- 0 none
		       end case;

				case sLCD.count is
				  when X"0" => touchCountReg:="00";
				  when X"1" => touchCountReg:="01";
				  when X"2" => touchCountReg:="10";
				  when others => touchCountReg:= "11";
				end case;
			end if;
		  -- watchdog clear touchCount to solve hang on of touch coordinates
		  if watchDog then touchCount:="00"; else touchCount:=touchCountReg; end if;
	  	   
			-- we delay by 1 LCD_DCLK to have stable coordinates.
		  RDY_N <=isRDY_n; isRDY_n:= reset or sLCD.RDY; 
		
		  preready:=sLCD.RDY;
		end if;
		
		touchData<=to_TouchDataSlv(x1, y1, x2, y2, touchCount, touchGesture);
    end process;
	 

-- counter switch touchCount to 0 after 63,5 ms I2C inactivity 
-- to solve hanging touch-coordinates problem
timerOff:process(LCD_DCLK)
    variable counter:unsigned(21 downto 0):=(others=>'0');
	 begin
		if rising_edge(LCD_DCLK) then 
		      watchDog<=false;
		      if sLCD.RDY='1' then counter:=(others=>'0');  
				elsif counter(counter'HIGH)='0' then counter:=counter+1; 
				else watchDog<=true; 
				end if;
		 end if;
		end process; 	 
end architecture;

