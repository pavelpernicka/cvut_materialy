library ieee, work;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- bude clockované z dipleje
-- prebira stavy z UserInterface a prevadi je na stav morseovky co se bude zobrazovat na displeji
entity MorseEngine is
  generic(IsTestbench : boolean := false);
  port(
    LCD_DCLK   : in  std_logic := '0';
    YEND_N     : in  std_logic := '0';
    commandStop: in  std_logic := '0';
    pauseLevel : in  unsigned(2 downto 0) := (others => '0');
    speedLevel : in  unsigned(2 downto 0) := (others => '0');
    morseBit   : out std_logic := '0'; -- je tecka
    morseDash  : out std_logic := '0'; -- je carka
    morseStop  : out std_logic := '0'; -- stop flag
    morseIndex : out unsigned(5 downto 0) := (others => '0'); -- kolikaty bit se prehrava
    pauseCountdown : out unsigned(2 downto 0) := (others => '0') -- odpocet pred zacatkem dalsiho kola
  );
end entity;

architecture rtl of MorseEngine is
  signal index_s    : unsigned(5 downto 0) := (others => '0');
  signal morseY_s   : std_logic := '0';
  signal morseStop_s: std_logic := '0';
  signal pauseCount_s : unsigned(2 downto 0) := (others => '0');

  function isDashStep(ix : integer) return boolean is
  -- idk, mozna to udelat primo z morse logiky...
  begin
    case ix is
      -- shorthand pro case ... when a ... when b ...
      when 3 | 4 | 5 | 7 | 8 | 9 | 21 | 22 | 23
         | 29 | 30 | 31 | 43 | 44 | 45 | 49 | 50 | 51 =>
        return true;
      when others =>
        return false;
    end case;
  end function;

  function framesPerStep(level : integer; isTb : boolean) return integer is
  begin
    -- mapping framerate to speed level
    -- when using testbench, spped up animation
    if isTb then
      case level is
        when 0 => return 8;
        when 1 => return 7;
        when 2 => return 6;
        when 3 => return 5;
        when 4 => return 4;
        when 5 => return 3;
        when 6 => return 2;
        when others => return 1;
      end case;
    else
      case level is
        when 0 => return 18;
        when 1 => return 16;
        when 2 => return 14;
        when 3 => return 12;
        when 4 => return 10;
        when 5 => return 8;
        when 6 => return 6;
        when others => return 4;
      end case;
    end if;
  end function;

  function pauseFrames(level : integer; isTb : boolean) return integer is
  begin
    -- mapping delay level to frames to wait
    -- also different values for simulation
    if isTb then
      case level is
        when 0 => return 2;
        when 1 => return 4;
        when 2 => return 6;
        when 3 => return 8;
        when 4 => return 10;
        when 5 => return 12;
        when 6 => return 14;
        when others => return 16;
      end case;
    else
      case level is
        when 0 => return 12;   -- 195ms
        when 1 => return 28;   -- 456ms
        when 2 => return 44;   -- 717ms
        when 3 => return 60;   -- 977ms
        when 4 => return 76;   -- 1.24s
        when 5 => return 92;   -- 1.50s
        when 6 => return 108;  -- 1.76s
        when others => return 123; -- 2s
      end case;
    end if;
  end function;

  function pauseDisplay(frameCount : integer; totalFrames : integer) return unsigned is
    variable disp : integer range 0 to 7 := 0;
  begin
    if totalFrames <= 0 or frameCount <= 0 then
      return to_unsigned(0, 3);
    end if;
    for s in 1 to 7 loop
      if frameCount * 8 > totalFrames * s then
        disp := s;
      end if;
    end loop;
    return to_unsigned(disp, 3);
  end function;
begin

  -- z puvodniho morse (morse_my.vhd)
  iMorse : entity work.MorseMY
    port map(X => index_s, Y => morseY_s, STOP => morseStop_s);

  -- casovani co frame
  pStep : process(YEND_N)
    constant MAX_UNIT_FRAMES : integer := 18;
    constant MAX_PAUSE_FRAMES : integer := 123;
    variable frameDiv : integer range 0 to MAX_UNIT_FRAMES := 0;
    variable stepFreq : integer range 1 to MAX_UNIT_FRAMES := 12;
    variable pauseFramesV : integer range 0 to MAX_PAUSE_FRAMES := 0;
    variable pauseFrameCounter : integer range 0 to MAX_PAUSE_FRAMES := 0;
    variable sequenceDone : boolean := false;
  begin
    if falling_edge(YEND_N) then
      stepFreq := framesPerStep(to_integer(speedLevel), IsTestbench);
      pauseFramesV := pauseFrames(to_integer(pauseLevel), IsTestbench);
      sequenceDone := morseStop_s = '1';

      if commandStop = '1' then
        -- rucni pauza tlacitkem
        pauseCount_s <= (others => '0');
      elsif pauseFrameCounter > 0 then
        -- pri pauze na konci si pridrzim counter aby to neposilalo dalsi cast kodu (TODO)
        pauseFrameCounter := pauseFrameCounter - 1;
        index_s <= (others => '0');
        pauseCount_s <= pauseDisplay(pauseFrameCounter, pauseFramesV);
      elsif frameDiv < stepFreq - 1 then
        frameDiv := frameDiv + 1;
      else
        frameDiv := 0;
        if sequenceDone then
          pauseFrameCounter := pauseFramesV;
          index_s <= (others => '0');
          pauseCount_s <= pauseDisplay(pauseFramesV, pauseFramesV);
        else
          index_s <= index_s + 1;
          pauseCount_s <= (others => '0');
        end if;
      end if;
    end if;
  end process;

  morseIndex <= index_s;
  pauseCountdown <= pauseCount_s;
  morseBit <= morseY_s when commandStop = '0' else '0';
  morseStop <= '1' when morseStop_s = '1' or pauseCount_s > 0 else '0';
  morseDash <= '1' when commandStop = '0' and isDashStep(to_integer(index_s)) else '0';

end architecture;
