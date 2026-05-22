-------------------------------------------------------------
-- CTU-FFE Prague, Dept. of Control Eng. [Richard Susta]
-- Published under GNU General Public License
-------------------------------------------------------------
library ieee, work;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
 
entity VeekMT2_IRDAv2 is
   generic(IRDA_REPEAT_WAIT_MS : natural := 500);
   port(LCD_DCLK       : in  std_logic; -- 33 MHz 
         CLRN           : in  std_logic                     := '0'; --Active in '0' clear signal
         IRDA_RXD       : in  std_logic                     := '0'; -- VEEK_MT2 infrared input.
         AddressCommand : out std_logic_vector(15 downto 0) := (others => '0'); -- Address + Command
         RDY_Command    : out std_logic                     := '0'; -- command ready
         ACK_Command    : in  std_logic                     := '0';  -- confirm RDY_Command
         CmdIsRepeated  : out std_logic                     := '0'; -- sent with RDY_Command
         IRDA_active    : out std_logic                     := '0');-- communication begins, a packet is sent
end entity;

architecture rtl of VeekMT2_IRDAv2 is

    -- "Shift register" which stores the 16 most recent received bits.
    signal received_bits            : std_logic_vector(32 downto 0) := (32 => '1', others => '0');
    --  signal clk_32mhz:std_logic:='0';
    signal Clk_33MHz                : std_logic                     := '0';
    signal confirm, packetEndSignal, repeatSignal : std_logic       := '0';

    --
    -- NEC protocol timings.
    -- 

    -- The NEC header is a 9ms pulse; these constants specify the ideal and realistic timings of that header.
    constant HEADER_MINUMUM_PULSE_LENGTH : integer := 230912; -- 0x38600 = cca 7 ms, NEC @ 9ms 
    constant HEADER_MAX_ADDRESS_START    : integer := 163840; -- = 0x28000 = 4.96 ms, org 4.5 ms;
	 
    -- Stores the maximum amount of time we'll wait for a "repeat packet". If we don't receieve a repeat
    -- packet in this time, we'll decide that the key must have been released.
    constant KEY_PRESS_TIMEOUT : integer := 3563520; -- = 0x366000, 107.9 ms

    constant CR_IDLE   : integer := 0;
    constant CR_HEADER : integer := 1;
    constant CR_REPEAT : integer := 2;
    constant CR_DATA   : integer := 3;

    signal CounterResult   : integer range CR_IDLE to CR_DATA;
    signal CounterData     : std_logic := '0';
    signal CounterIsNew    : boolean   := FALSE;
    signal CounterClearNew : boolean   := FALSE;
	 
	  -- blocking of repeating keyw
  signal resetDelay, doneDelay : boolean := false;


begin
    Clk_33MHz <= LCD_DCLK;

    PulseCounter : process(Clk_33MHz)
        variable cntr1     : unsigned(23 downto 0) := (others => '0');
        variable cntr0     : unsigned(23 downto 0) := (others => '0');
        variable IRDA_filter:std_logic_vector(0 to 3):=(others => '0');
        variable IRDA : std_logic:='0';
        variable lastIRDA : std_logic             := '0';
    begin
        if rising_edge(Clk_33MHz) then
            if (IRDA='0' and IRDA_filter="1111")
                or (IRDA='1' and IRDA_filter="0000") 
            then IRDA:=IRDA_filter(0);
            end if;
				-- input IRDA_RXD is in negated logic
            IRDA_filter:=(not IRDA_RXD) & IRDA_filter(0 to 2);

            if CLRN = '0' then
                cntr0 := (others => '0'); cntr1  := (others => '0');
                lastIRDA := '0';
            else
                if lastIRDA = '0' and IRDA = '1' then
                    CounterData  <= '0';
                    CounterIsNew <= TRUE;
                    CounterResult <= CR_IDLE;
                    if cntr0<HEADER_MAX_ADDRESS_START then
                        if cntr1>=HEADER_MINUMUM_PULSE_LENGTH then
                           if cntr0>=3*(cntr1/8) then
                               CounterResult <= CR_HEADER;
                           elsif cntr0>=1*(cntr1/8) then 
                               CounterResult <= CR_REPEAT;
                           end if;
                        else
                            CounterResult <= CR_DATA;
                            if cntr0<cntr1+cntr1/4 then
                               CounterData   <= '0';
                           else 
                               CounterData   <= '1';
                           end if;
                        end if;    
                    end if;    
                    cntr0 := (others => '0'); cntr1  := (others => '0');
                else
                    if IRDA='1' and cntr1(22) = '0' then
                        cntr1 := cntr1 + 1; -- cntr<4194304, cca 254 ms
                    end if;
                    if IRDA='0' and cntr0(22) = '0' then
                        cntr0 := cntr0 + 1; -- cntr<4194304, cca 254 ms
                    end if;
                end if;
                lastIRDA := IRDA;
                if CounterClearNew then CounterIsNew <= FALSE;
                end if;
            end if;
        end if;
    end process;

    -- data_is_valid <= '1' when received_bits(15 downto 8) = not received_bits(7 downto 0);
    process(Clk_33MHz)
        variable data_is_valid : boolean := FALSE;
        variable waitACK       : boolean := FALSE;
        variable waitConfirm   : boolean := FALSE;
        variable watchDog : unsigned(23 downto 0):=(others=>'0');
    begin
        if rising_edge(Clk_33MHz) then
            if packetEndSignal = '1' then
                if not waitConfirm then
                    data_is_valid := TRUE; -- (received_bits(15 downto 8) = not received_bits(7 downto 0));
                    if data_is_valid and packetEndSignal = '1' then
                        AddressCommand <= received_bits(8 downto 1) & received_bits(24 downto 17);
                        RDY_Command    <= '1';
                        waitACK        := TRUE;
                     end if;
                end if;
                -- packet is always confirmed
                confirm     <= '1'; -- confirming accepting data
                waitConfirm := TRUE;
            elsif repeatSignal='1' then
               if not waitConfirm then
                    CmdIsRepeated<='1';
                    RDY_Command    <= '1';
                    waitACK        := TRUE;
               end if;
                confirm     <= '1';
                waitConfirm := TRUE;
            else 
                confirm     <= '0';
                waitConfirm := FALSE;
            end if;
            if waitACK and (ACK_Command or watchDog(watchDog'HIGH))='1' then
                RDY_Command <= '0'; CmdIsRepeated<='0';
                waitACK     := false;
            end if;
            if waitACK then watchDog:=watchDog+1;
            else watchDog:=(others=>'0');
            end if;
        end if;
    end process;

    --
    process(LCD_DCLK)
        type state_t is (IDLE, WAIT_FOR_HEADER, WAIT_FOR_HEADER_CR, WAIT_FOR_REPEAT_CR,
                         READ_DATA, READ_DATA_CR, PROCESS_PACKET, SEND_PACKET, WAIT_FOR_CONFIRM,
                         WAIT_RESET_REPEAT_DELAY, WAIT_FOR_REPEAT_CONFIRM
                        );

        --Current and next state logic for the FSM.
        variable state, last_state : state_t                             := IDLE;
     begin
        if rising_edge(LCD_DCLK) then
            packetEndSignal <= '0';
            if CLRN = '0'  then
                state           := IDLE;
                last_state      := IDLE;
                 packetEndSignal <= '0'; repeatSignal<='0'; resetDelay<=true;
            else
                IRDA_active<='1'; 
                 packetEndSignal <= '0'; repeatSignal<='0';
                case state is
                    when IDLE=>
                        CounterClearNew <= true; resetDelay<=false;
	                     if not CounterIsNew then
                            CounterClearNew <= false;
                            state           := WAIT_FOR_HEADER;
                        end if;
					  
				    when WAIT_FOR_HEADER =>
                        IRDA_active<='0'; CounterClearNew <= false;
                        if CounterIsNew then
                            if CounterResult = CR_HEADER then
                                received_bits <= (32 => '1', others => '0');
                                state := WAIT_FOR_HEADER_CR;
                            elsif CounterResult = CR_REPEAT then
                                 state := WAIT_FOR_REPEAT_CR;
                         else 
                             state:=IDLE;
                         end if;
                         CounterClearNew <= true;
                        end if;
                    when WAIT_FOR_HEADER_CR =>
                        CounterClearNew <= true;
                       if not CounterIsNew then
                            CounterClearNew <= false;
                            state           := READ_DATA;
                        end if;
                    when WAIT_FOR_REPEAT_CR =>
                        CounterClearNew <= true;
								if not doneDelay then state:=IDLE; -- blocking repeating key
								else state:=WAIT_RESET_REPEAT_DELAY; 
								end if;
						when WAIT_RESET_REPEAT_DELAY=>
 							   resetDelay<=true;
								if not doneDelay then
 								  repeatSignal<='1'; 
                          if not CounterIsNew then
                             state := WAIT_FOR_REPEAT_CONFIRM; CounterClearNew <= false;
                           end if;
								end if;
                  when WAIT_FOR_REPEAT_CONFIRM =>
  							   resetDelay<=false;
                       repeatSignal <= '1';
                        if confirm = '1' then
                            state := IDLE;
                        end if;
                    when READ_DATA =>
						if CounterIsNew then
                            if CounterResult = CR_DATA then
                                 state := READ_DATA_CR;
                                -- Shift register, which loads in the received data each time a bit is received.
                                -- data are transmitted for LSB to MSB, so, we shift right
                                received_bits   <= CounterData & received_bits(32 downto 1);
						    else 
                                 state := IDLE;
                            end if;
                            CounterClearNew <= true;
                        end if;
                    when READ_DATA_CR =>
                        CounterClearNew <= true;
                       if not CounterIsNew then
                            CounterClearNew <= false;
                            if received_bits(0) = '1' then
                                  state := PROCESS_PACKET;
                            else
                               state  := READ_DATA;
                            end if;
                        end if;

                    -- Finally, once the packet is complete, we have enough information
                    -- to extract the full message. We'll extract the message, and then
                    -- wait for the line to return to idle-- which will take another half
                    -- of a ms, or eighteen thousand clock cycles.
                    -- 
                    when PROCESS_PACKET =>
                        resetDelay<=true; 
								if not doneDelay then state:= SEND_PACKET; end if; -- wait for accepting resetDelay
						  when SEND_PACKET=>
                        resetDelay<=false; 
								packetEndSignal <= '1'; --Indicate that we've received a full packet.
                        CounterClearNew <= true; 
						     if not CounterIsNew then
                            CounterClearNew <= false;
                            state           := WAIT_FOR_CONFIRM;
                        end if;
                     --TWe wait for RDY-ACK module to confirm.
                    when WAIT_FOR_CONFIRM =>
                        packetEndSignal <= '1';
                        if confirm = '1' then
                            state := IDLE;
                        end if;
                 end case;
                 last_state:=state;
             end if;
        end if;
    end process;
	 
	 -- The count time for temporary insensitivity for remote control key repeats
iRepeat : process(LCD_DCLK) 
  constant WAIT_TIME : natural := IRDA_REPEAT_WAIT_MS*33000; -- delay ms/33 MHz
  variable delay : integer range 0 to WAIT_TIME := 0;
begin
  if falling_edge(LCD_DCLK) then
    doneDelay<=false; 
    if resetDelay then delay:=0; 
	 elsif delay<WAIT_TIME then delay:=delay+1; 
    else doneDelay<=true;
    end if;
  end if;
end process;	 

end architecture;

