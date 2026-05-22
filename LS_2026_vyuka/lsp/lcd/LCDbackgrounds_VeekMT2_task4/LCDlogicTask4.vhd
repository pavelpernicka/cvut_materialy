-------------------------------------------------------------
-- CTU-FFE Prague, Dept. of Control Eng. [Richard Susta], Published under GNU General Public License
-------------------------------------------------------------

library ieee, work;
use ieee.std_logic_1164.all; use ieee.numeric_std.all;  -- for integer and unsigned types
use work.LCDpackV2.all;       -- its version 2.1 and higher
use work.TouchIRDApackV2.all; --defined TouchDataSlv_t 
use work.UIpack.all; 

entity LCDlogicTask4 is
    generic(IsTestbench:boolean:=FALSE); -- in testbench, we decrease frequency
    port( touchCoordinates : in   TouchDataSlv_t := (others => '0'); -- packet with coordinates 
         commandStop        : in  std_logic:='0'; -- '1' if stopped
         morseBit           : in  std_logic:='0';
         morseDash          : in  std_logic:='0';
         morseStop          : in  std_logic:='0';
         morseIndex         : in  unsigned(5 downto 0):=(others=>'0');
         xcolumn  : in  xy_t      := XY_ZERO; -- x-coordinate of pixel (column index)
         yrow     : in  xy_t      := XY_ZERO; -- y-coordinate of pixel (row index)
         XEND_N   : in  std_logic := '0'; -- '0' only when xcolumn=1023, otherwise '1', f=32227 Hz= 33e6/1024 
         YEND_N   : in  std_logic := '0'; -- '0' only when yrow=524, otherwise '1', f=61.384 Hz = 33e6/(1024*525)
         LCD_DE   : in  std_logic := '0'; -- DataEnable control signal of LCD controller
         LCD_DCLK : in  std_logic := '0'; -- LCD data clock, exactly 33 MHz
         pauseCountdown     : in  unsigned(PAUSE_LEVEL_BITS-1 downto 0):=(others=>'0');
         pauseLevel         : in  unsigned(PAUSE_LEVEL_BITS-1 downto 0):=(others=>'0');
         speedLevel         : in  unsigned(SPEED_LEVEL_BITS-1 downto 0):=(others=>'0');
			RGBcolor : out RGB_t:=BLACK);
end entity;

-- Basic LCD
architecture rtl of LCDlogicTask4 is
    type palette103_t is array (0 to 102) of RGB_t;
    type ray_array_t is array (0 to SPEED_LEVELS-2) of integer;
    type seg_coord_array_t is array (0 to 6) of integer;
    type morse_edge_array_t is array (0 to 55) of integer;
    type morse_index_array_t is array (0 to 54) of integer;

    -- barvicky
    constant FRAME_DARK     : RGB_t := ToRGB(2, 10, 34);
    constant FRAME_PATTERN  : RGB_t := ToRGB(8, 25, 60);
    constant FRAME_LINE     : RGB_t := ToRGB(20, 43, 80);
    constant SKY_TOP        : RGB_t := ToRGB(74, 174, 226);
    constant SKY_LOW        : RGB_t := ToRGB(82, 178, 220);
    constant CLOUD          : RGB_t := ToRGB(246, 250, 250);
    constant CLOUD_SHADE    : RGB_t := ToRGB(222, 236, 241);
    constant CLOUD_DARK       : RGB_t := ToRGB(110, 126, 140);
    constant CLOUD_SHADE_DARK : RGB_t := ToRGB(84, 98, 112);
    constant CLOUD_SYMBOL     : RGB_t := ToRGB(36, 52, 74);
    constant BIRD           : RGB_t := ToRGB(238, 246, 246);
    constant RAINBOW_RED    : RGB_t := ToRGB(226, 67, 38);
    constant RAINBOW_ORANGE : RGB_t := ToRGB(246, 136, 36);
    constant RAINBOW_YELLOW : RGB_t := ToRGB(249, 219, 59);
    constant RAINBOW_GREEN  : RGB_t := ToRGB(120, 195, 59);
    constant RAINBOW_BLUE   : RGB_t := ToRGB(37, 123, 197);
    constant RAINBOW_PURPLE : RGB_t := ToRGB(106, 74, 178);
    constant HILL_BACK      : RGB_t := ToRGB(138, 195, 46);
    constant HILL_MID       : RGB_t := ToRGB(50, 142, 57);
    constant HILL_FRONT     : RGB_t := ToRGB(22, 96, 45);
    constant TREE_DARK      : RGB_t := ToRGB(10, 82, 48);
    constant TREE_LIGHT     : RGB_t := ToRGB(34, 132, 72);
    constant MORSE_STRIP_BG : RGB_t := ToRGB(10, 18, 56);
    constant MORSE_STRIP_LINE : RGB_t := ToRGB(54, 82, 148);
    constant MORSE_DOT_COLOR : RGB_t := ToRGB(106, 236, 198);
    constant MORSE_DASH_COLOR : RGB_t := ToRGB(246, 152, 58);
    constant MORSE_GAP_COLOR : RGB_t := ToRGB(34, 44, 88);
    constant MORSE_ACTIVE_COLOR : RGB_t := ToRGB(255, 242, 126);
    constant MORSE_POINTER_IDLE : RGB_t := ToRGB(154, 166, 186);
    constant LETTER_ACTIVE_RED  : RGB_t := ToRGB(214, 42, 32);
    constant PLAY_ICON          : RGB_t := ToRGB(34, 212, 52);
    constant STOP_ICON          : RGB_t := ToRGB(228, 44, 42);
    constant PLAY_BUTTON_FILL   : RGB_t := ToRGB(250, 250, 252);
    constant PLAY_BUTTON_EDGE   : RGB_t := ToRGB(148, 160, 182);
    constant SPEED_BUTTON_FILL  : RGB_t := ToRGB(246, 248, 252);
    constant SPEED_BUTTON_EDGE  : RGB_t := ToRGB(130, 144, 170);
    constant SPEED_SYMBOL       : RGB_t := ToRGB(26, 60, 114);
    constant PAUSE_BUTTON_FILL  : RGB_t := ToRGB(252, 244, 232);
    constant PAUSE_BUTTON_EDGE  : RGB_t := ToRGB(174, 134, 92);
    constant PAUSE_SYMBOL       : RGB_t := ToRGB(124, 64, 22);
    constant PAUSE_BAR_ON       : RGB_t := ToRGB(220, 112, 36);
    constant PAUSE_BAR_OFF      : RGB_t := ToRGB(160, 134, 110);
    constant PAUSE_COUNTDOWN    : RGB_t := ToRGB(238, 58, 44);
    constant PAUSE_DIGIT_OFF    : RGB_t := ToRGB(124, 104, 96);
    constant SPEED_DIGIT_ON     : RGB_t := ToRGB(230, 44, 36);
    constant SPEED_DIGIT_OFF    : RGB_t := ToRGB(122, 130, 154);

    constant MORSE_STEPS : integer := 55;
    constant MORSE_XLEFT : integer := 44;
    constant MORSE_XRIGHT: integer := 756;
    constant MORSE_YTOP  : integer := 404;
    constant MORSE_YBASE : integer := 446;
    constant MORSE_TRACK_BOTTOM : integer := 462;
    constant MORSE_SYMBOL_TOP : integer := 424;
    constant WORD_XLEFT : integer := 208;
    constant WORD_YTOP  : integer := 328;
    constant WORD_SCALE : integer := 2;
    constant LETTER_W   : integer := 32;
    constant LETTER_H   : integer := 32;
    constant LETTERS_COUNT : integer := 6;
    constant DIGIT_XCENTER : integer := 400;
    constant DIGIT_YCENTER : integer := 287;
    constant DIGIT_HALF_W  : integer := 16;
    constant DIGIT_HALF_H  : integer := 26;
    constant DIGIT_SEG_T   : integer := 4;
    constant DIGIT_SEG_L   : integer := 22;
    constant PAUSE_DIGIT_XCENTER : integer := 106;
    constant PAUSE_DIGIT_YCENTER : integer := 36;

    constant BALON_W       : integer := 32;
    constant BALON_H       : integer := 32;
    constant BALON_BIG_X   : integer := 352;
    constant BALON_BIG_Y   : integer := 40;
    constant BALON_BIG_W   : integer := 128;
    constant BALON_BIG_H   : integer := 128;
    constant BALON_BIG_X4  : integer := 88;
    constant BALON_BIG_Y4  : integer := 10;
    constant BALON_PLAIN_X : integer := 650;
    constant BALON_PLAIN_Y : integer := 258;
    constant BALON_GRAY_X  : integer := 130;
    constant BALON_GRAY_Y  : integer := 306;
    constant BALON_TRANSPARENT : integer := 2;
    constant RAINBOW_RAY_DX : ray_array_t := (-216, -144, -72, 0, 72, 144, 216);
    constant RAINBOW_RAY_DY : ray_array_t := (-147, -186, -206, -212, -206, -186, -147);
    constant SEG_X1 : seg_coord_array_t := (-DIGIT_HALF_W, DIGIT_HALF_W, DIGIT_HALF_W, -DIGIT_HALF_W,
                                            -DIGIT_HALF_W-DIGIT_SEG_T, -DIGIT_HALF_W-DIGIT_SEG_T, -DIGIT_HALF_W);
    constant SEG_X2 : seg_coord_array_t := ( DIGIT_HALF_W, DIGIT_HALF_W+DIGIT_SEG_T, DIGIT_HALF_W+DIGIT_SEG_T, DIGIT_HALF_W,
                                            -DIGIT_HALF_W, -DIGIT_HALF_W, DIGIT_HALF_W);
    constant SEG_Y1 : seg_coord_array_t := (-DIGIT_HALF_H-DIGIT_SEG_T, -DIGIT_HALF_H, DIGIT_HALF_H-DIGIT_SEG_L,
                                             DIGIT_HALF_H, DIGIT_HALF_H-DIGIT_SEG_L, -DIGIT_HALF_H, -DIGIT_SEG_T/2);
    constant SEG_Y2 : seg_coord_array_t := (-DIGIT_HALF_H, -DIGIT_HALF_H + DIGIT_SEG_L, DIGIT_HALF_H,
                                             DIGIT_HALF_H + DIGIT_SEG_T, DIGIT_HALF_H, -DIGIT_HALF_H + DIGIT_SEG_L, DIGIT_SEG_T/2);

    constant BALON_PALETTE : palette103_t := (
        X"000000", X"4B4C4C", X"FFFFFF", X"D3311E", X"D13521", X"E53724", X"E63A25", X"E93C25",
        X"E93C28", X"B33119", X"E54021", X"E8441B", X"E7461E", X"EC4A21", X"EA4C1D", X"845A36",
        X"F3881B", X"512C03", X"EE881A", X"AD6606", X"AD6709", X"BB6F08", X"BE720A", X"C17207",
        X"F89815", X"7F4C03", X"C37608", X"C87908", X"C47C0F", X"F4A516", X"C8930F", X"F6B90F",
        X"FABC13", X"FBC312", X"FCC60F", X"FDCB11", X"FECE0F", X"CDAB0E", X"FED10E", X"FED112",
        X"C0A614", X"C1AA13", X"EECF1B", X"EFD01C", X"F0D01B", X"55A93E", X"428532", X"3F852F",
        X"51A73E", X"55A942", X"428936", X"4EA63D", X"4DA540", X"52A448", X"4DA14D", X"4B9C52",
        X"3E954B", X"47955A", X"3B814F", X"4A9963", X"489763", X"4EA36D", X"4FA271", X"418D66",
        X"4E9F75", X"36796E", X"39838B", X"2E7D89", X"30809D", X"2A586B", X"196385", X"267099",
        X"206899", X"2874A8", X"1C5F8F", X"2A75B2", X"2D83C7", X"205E95", X"226BAD", X"297DCB",
        X"2D81CE", X"2D84D5", X"2C85D4", X"2E85D3", X"2C85D6", X"3085D3", X"2F86D6", X"2D87D6",
        X"3087D4", X"184570", X"175087", X"1F578D", X"22619E", X"2367A9", X"226CB1", X"2674BD",
        X"3075B8", X"2E76BF", X"2B7FD2", X"3184D6", X"2973C1", X"4D6C95", X"466FA2"
    );

    signal balon_addr : std_logic_vector(9 downto 0) := (others => '0');
    signal balon_q    : std_logic_vector(6 downto 0) := (others => '0');
    signal pernic_addr : std_logic_vector(12 downto 0) := (others => '0');
    signal pernic_q    : std_logic_vector(1 downto 0) := (others => '0');

    -- color modifiers
    function toGray(rgb : RGB_t) return RGB_t is
        variable red8   : unsigned(7 downto 0) := (others => '0');
        variable green8 : unsigned(7 downto 0) := (others => '0');
        variable blue8  : unsigned(7 downto 0) := (others => '0');
        variable gray10 : unsigned(9 downto 0) := (others => '0');
        variable gray8  : std_logic_vector(7 downto 0) := (others => '0');
    begin
        red8 := unsigned(rgb(23 downto 16));
        green8 := unsigned(rgb(15 downto 8));
        blue8 := unsigned(rgb(7 downto 0));
        gray10 := shift_right(resize(red8, 10), 2) + shift_right(resize(red8, 10), 5)
                + shift_right(resize(green8, 10), 1) + shift_right(resize(green8, 10), 4)
                + shift_right(resize(blue8, 10), 4) + shift_right(resize(blue8, 10), 5);
        gray8 := std_logic_vector(gray10(7 downto 0));
        return RGB_t'(gray8 & gray8 & gray8);
    end function;

    function fadedColor(rgb : RGB_t) return RGB_t is
        variable red8   : integer range 0 to 255 := 0;
        variable green8 : integer range 0 to 255 := 0;
        variable blue8  : integer range 0 to 255 := 0;
    begin
        red8 := 110 + to_integer(unsigned(rgb(23 downto 16))) / 2;
        green8 := 110 + to_integer(unsigned(rgb(15 downto 8))) / 2;
        blue8 := 110 + to_integer(unsigned(rgb(7 downto 0))) / 2;
        if red8 > 255 then red8 := 255; end if;
        if green8 > 255 then green8 := 255; end if;
        if blue8 > 255 then blue8 := 255; end if;
        return ToRGB(red8, green8, blue8);
    end function;

    -- deleni mocninou dvojky pomocí shiftovani, abych se vyhnul delickam
    function shiftDiv(n : integer; bits : natural) return integer is
    begin
        return to_integer(shift_right(to_unsigned(n, 24), bits));
    end function;

    -- deleni pomoci kombinace deleni druhou mocninou
    -- n/2^11 + n/2^15 = n/1800. zhruba, stejne je to od oka, aby to vypadalo dobre
    function approxDiv1800(n : integer) return integer is
    begin
        return shiftDiv(n, 11) + shiftDiv(n, 15);
    end function;

    -- n/2^12 + n/2^13 = n/2600
    function approxDiv2600(n : integer) return integer is
    begin
        return shiftDiv(n, 12) + shiftDiv(n, 13);
    end function;

    -- n/2^13 + n/2^16 ~= n/6500
    function approxDiv6500(n : integer) return integer is
    begin
        return shiftDiv(n, 13) + shiftDiv(n, 16);
    end function;

    -- tady se delicky neudelaji, protoze pracuji s konstantnimi vecmi
    function morseEdges return morse_edge_array_t is
        variable res : morse_edge_array_t := (others => 0);
        constant WIDTH_C : integer := MORSE_XRIGHT - MORSE_XLEFT + 1;
    begin
        for i in 0 to MORSE_STEPS loop
            res(i) := (i * WIDTH_C) / MORSE_STEPS;
        end loop;
        return res;
    end function;

    function morsePointers return morse_index_array_t is
        variable res : morse_index_array_t := (others => 0);
        constant WIDTH_C : integer := MORSE_XRIGHT - MORSE_XLEFT + 1;
    begin
        for i in 0 to MORSE_STEPS-1 loop
            res(i) := MORSE_XLEFT + ((2*i + 1) * WIDTH_C) / (2 * MORSE_STEPS);
        end loop;
        return res;
    end function;

    function rainbowSector(dx, dy : integer) return integer is
        variable seg : integer range 0 to SPEED_LEVELS-1 := 0;
        variable cross : integer := 0;
    begin
        for i in 0 to SPEED_LEVELS-2 loop
            cross := RAINBOW_RAY_DX(i) * dy - RAINBOW_RAY_DY(i) * dx;
            if cross >= 0 then
                seg := seg + 1;
            else
                exit;
            end if;
        end loop;
        return seg;
    end function;

    function sevenSegMask(digit : integer) return std_logic_vector is
    begin
        -- cislovani: zhora doprava dolů, zleva nahoru, prostredek
        case digit is
            when 0 => return "1111110";
            when 1 => return "0110000";
            when 2 => return "1101101";
            when 3 => return "1111001";
            when 4 => return "0110011";
            when 5 => return "1011011";
            when 6 => return "1011111";
            when 7 => return "1110000";
            when others => return "1111111";
        end case;
    end function;

    -- toto muzu realtimove ziskavat z morse bloku, ale potrebuji to predem vykreslovat jako celek
    function isDashStep(ix : integer) return boolean is
    begin
        case ix is
            when 3 | 4 | 5 | 7 | 8 | 9 | 21 | 22 | 23
               | 29 | 30 | 31 | 43 | 44 | 45 | 49 | 50 | 51 =>
                return true;
            when others =>
                return false;
        end case;
    end function;

    function isMorseLit(ix : integer) return boolean is
    begin
        case ix is
            when 1 | 3 | 4 | 5 | 7 | 8 | 9 | 11 | 15 | 19
               | 21 | 22 | 23 | 25 | 29 | 30 | 31 | 33
               | 37 | 39 | 43 | 44 | 45 | 47 | 49 | 50 | 51 | 53 =>
                return true;
            when others =>
                return false;
        end case;
    end function;

    function letterIndexFromMorse(ix : integer) return integer is
    begin
        case ix is
            when 0 to 12  => return 0; -- P
            when 13 to 16 => return 1; -- E
            when 17 to 26 => return 2; -- R
            when 27 to 34 => return 3; -- N
            when 35 to 40 => return 4; -- I
            when others   => return 5; -- C
        end case;
    end function;
    
    constant MORSE_EDGE_X : morse_edge_array_t := morseEdges;
    constant MORSE_POINTER_X : morse_index_array_t := morsePointers;
begin 
    iBalonRom : entity work.balon_noshadow_white_opt
        port map(address => balon_addr, clock => LCD_DCLK, q => balon_q);
    iPernicRom : entity work.PERNIC
        port map(address => pernic_addr, clock => LCD_DCLK, q => pernic_q);

	 LSPimage : process(all)
        variable RGB       : RGB_t := BLACK;
        variable x         : integer range 0 to XCOLUMN_MAX := 0;
        variable y         : integer range 0 to YROW_MAX := 0;
        variable dx        : integer range -800 to 1000 := 0;
        variable dy        : integer range -500 to 500 := 0;
        variable x32       : integer range 0 to 31 := 0;
        variable y32       : integer range 0 to 31 := 0;
        variable arc       : integer range 0 to 6000000 := 0;
        variable skyOn     : boolean := false;
        variable dotActive : boolean := false;
        variable dashActive: boolean := false;
        variable leftCloudOn : boolean := false;
        variable rightCloudOn: boolean := false;
        variable imgRect   : integer range 0 to 3 := 0;
        variable imgColor  : integer range 0 to 127 := 0;
        variable rgbSrc    : RGB_t := BLACK;
        variable blueLevel : integer range 0 to 255 := 0;
        variable tintLevel : integer range 0 to 255 := 0;
        variable stripWidth : integer range 1 to LCD_WIDTH := 1;
        variable localX    : integer range -1 to LCD_WIDTH := -1;
        variable mappedIx  : integer range 0 to MORSE_STEPS := 0;
        variable pointerX  : integer range -1 to LCD_WIDTH := 0;
        variable currentIx : integer range 0 to MORSE_STEPS := 0;
        variable activeLetter : integer range 0 to LETTERS_COUNT - 1 := 0;
        variable letterX : integer range -1 to LCD_WIDTH := -1;
        variable letterY : integer range -1 to LCD_HEIGHT := -1;
        variable letterIx : integer range 0 to LETTERS_COUNT - 1 := 0;
        variable pixIdx : integer range 0 to 3 := 0;
        variable speedIx : integer range 0 to SPEED_LEVELS-1 := 0;
        variable pauseIx : integer range 0 to PAUSE_LEVELS-1 := 0;
        variable pauseCountIx : integer range 0 to PAUSE_LEVELS-1 := 0;
        variable rainbowSeg : integer range 0 to SPEED_LEVELS-1 := 0;
        variable rainbowColor : RGB_t := BLACK;
        variable digitMask : std_logic_vector(6 downto 0) := (others => '0');
        variable showPauseIcon : boolean := false;
     begin
        x := to_integer(xcolumn);
        y := to_integer(yrow);
        x32 := to_integer(xcolumn(4 downto 0));
        y32 := to_integer(yrow(4 downto 0));
        imgRect := 0;
        imgColor := 0;
        rgbSrc := BLACK;
        blueLevel := 0;
        tintLevel := 0;
        dotActive := (morseBit = '1' and morseDash = '0');
        dashActive := (morseBit = '1' and morseDash = '1');
        leftCloudOn := false;
        rightCloudOn := false;
        currentIx := to_integer(morseIndex);
        if currentIx > MORSE_STEPS - 1 then
            currentIx := MORSE_STEPS - 1;
        end if;
        activeLetter := letterIndexFromMorse(currentIx);
        speedIx := to_integer(speedLevel);
        pauseIx := to_integer(pauseLevel);
        pauseCountIx := to_integer(pauseCountdown);
        showPauseIcon := (commandStop = '1') or (pauseCountIx > 0);
        rainbowSeg := 0;
        rainbowColor := BLACK;
        digitMask := sevenSegMask(speedIx + 1);
        stripWidth := MORSE_XRIGHT - MORSE_XLEFT + 1;
        balon_addr <= (others => '0');
        pernic_addr <= (others => '0');

        -- frame and background
        RGB := FRAME_DARK;
        if x32 < 2 or y32 < 2 then
            RGB := FRAME_LINE;
        elsif (x32 < 13 and y32 < 13) or (x32 >= 20 and y32 >= 20) then
            RGB := FRAME_PATTERN;
        end if;

        -- sky ellipse, dark = no morse, light = morse transmitted
        skyOn := false;
        -- rainbow as play speed indicator
        dx := x - 400;
        dy := y - 214;
        arc := 2*dx*dx + 9*dy*dy;
        if arc < 304000 then
            skyOn := true;
            if morseBit = '1' then
                blueLevel := 255 - approxDiv1800(arc);
                if blueLevel < 150 then
                    blueLevel := 150;
                end if;
                tintLevel := 225 - approxDiv2600(arc);
                if tintLevel < 110 then
                    tintLevel := 110;
                end if;
                RGB := ToRGB(shiftDiv(tintLevel * 171, 9), shiftDiv(tintLevel, 1), blueLevel);
            else
                blueLevel := 176 - approxDiv6500(arc);
                if blueLevel < 108 then
                    blueLevel := 108;
                end if;
                tintLevel := 176 - approxDiv6500(arc);
                if tintLevel < 108 then
                    tintLevel := 108;
                end if;
                RGB := ToRGB(tintLevel, tintLevel, blueLevel);
            end if;
            if y > 170 and morseBit = '0' then
                RGB := ToRGB(tintLevel - 10, tintLevel - 10, blueLevel - 10);
            end if;
        end if;

        dx := x - 400;
        dy := y - 400;
        arc := dx*dx + 2*dy*dy;
        if skyOn and y > 142 and y < 342 and arc < 90000 and arc > 48000 then
            rainbowSeg := rainbowSector(dx, dy);
            if arc > 83000 then
                rainbowColor := RAINBOW_RED;
            elsif arc > 76000 then
                rainbowColor := RAINBOW_ORANGE;
            elsif arc > 69000 then
                rainbowColor := RAINBOW_YELLOW;
            elsif arc > 62000 then
                rainbowColor := RAINBOW_GREEN;
            elsif arc > 55000 then
                rainbowColor := RAINBOW_BLUE;
            else
                rainbowColor := RAINBOW_PURPLE;
            end if;
            if rainbowSeg <= speedIx then
                RGB := rainbowColor;
            else
                RGB := fadedColor(rainbowColor);
            end if;
        end if;

        -- mracky a ptaci
        if skyOn then
            dx := x - 96; dy := y - 252; arc := 5*dx*dx + 12*dy*dy;
            if arc < 10200 then RGB := assignIf(dotActive, CLOUD_SHADE_DARK, CLOUD_SHADE); end if;
            dx := x - 134; dy := y - 238; arc := 5*dx*dx + 12*dy*dy;
            if arc < 9200 then RGB := assignIf(dotActive, CLOUD_SHADE_DARK, CLOUD_SHADE); end if;
            dx := x - 162; dy := y - 250; arc := 5*dx*dx + 12*dy*dy;
            if arc < 7000 then RGB := assignIf(dotActive, CLOUD_SHADE_DARK, CLOUD_SHADE); end if;

            dx := x - 126; dy := y - 142; arc := 4*dx*dx + 9*dy*dy;
            if arc < 11600 then RGB := assignIf(dotActive, CLOUD_DARK, CLOUD); end if;
            dx := x - 172; dy := y - 128; arc := 4*dx*dx + 9*dy*dy;
            if arc < 14000 then RGB := assignIf(dotActive, CLOUD_DARK, CLOUD); end if;
            dx := x - 224; dy := y - 144; arc := 4*dx*dx + 9*dy*dy;
            if arc < 11800 then RGB := assignIf(dotActive, CLOUD_DARK, CLOUD); end if;
            dx := x - 256; dy := y - 126; arc := 5*dx*dx + 10*dy*dy;
            if arc < 9000 then RGB := assignIf(dotActive, CLOUD_DARK, CLOUD); end if;
            dx := x - 94; dy := y - 164; arc := 5*dx*dx + 12*dy*dy;
            if arc < 6600 then RGB := assignIf(dotActive, CLOUD_DARK, CLOUD); end if;
            leftCloudOn := (x >= 78 and x <= 266 and y >= 112 and y <= 274);

            dx := x - 570; dy := y - 148; arc := 4*dx*dx + 9*dy*dy;
            if arc < 10800 then RGB := assignIf(dashActive, CLOUD_DARK, CLOUD); end if;
            dx := x - 620; dy := y - 126; arc := 4*dx*dx + 9*dy*dy;
            if arc < 14200 then RGB := assignIf(dashActive, CLOUD_DARK, CLOUD); end if;
            dx := x - 676; dy := y - 146; arc := 4*dx*dx + 9*dy*dy;
            if arc < 11600 then RGB := assignIf(dashActive, CLOUD_DARK, CLOUD); end if;
            dx := x - 708; dy := y - 124; arc := 5*dx*dx + 10*dy*dy;
            if arc < 9000 then RGB := assignIf(dashActive, CLOUD_DARK, CLOUD); end if;
            dx := x - 746; dy := y - 166; arc := 5*dx*dx + 12*dy*dy;
            if arc < 6900 then RGB := assignIf(dashActive, CLOUD_DARK, CLOUD); end if;
            rightCloudOn := (x >= 548 and x <= 764 and y >= 110 and y <= 176);

            dx := x - 366; dy := y - 126; arc := 5*dx*dx + 11*dy*dy; if arc < 3200 then RGB := CLOUD; end if;
            dx := x - 388; dy := y - 116; arc := 5*dx*dx + 11*dy*dy; if arc < 3900 then RGB := CLOUD; end if;
            dx := x - 412; dy := y - 128; arc := 5*dx*dx + 11*dy*dy; if arc < 3200 then RGB := CLOUD; end if;

            dx := x - 306; dy := y - 87; arc := 3*dx*dx + 10*dy*dy;
            if x >= 278 and x <= 334 and y >= 75 and y <= 87 and arc > 920 and arc < 1420 then RGB := BIRD; end if;
            dx := x - 476; dy := y - 111; arc := 3*dx*dx + 10*dy*dy;
            if x >= 448 and x <= 504 and y >= 99 and y <= 111 and arc > 920 and arc < 1420 then RGB := BIRD; end if;
            dx := x - 514; dy := y - 65; arc := 3*dx*dx + 10*dy*dy;
            if x >= 486 and x <= 542 and y >= 53 and y <= 65 and arc > 920 and arc < 1420 then RGB := BIRD; end if;
        end if;

        -- according to currently played symbol, showing dot or dash symbol in the clouds 
        if dotActive and leftCloudOn then
            dx := x - 176;
            dy := y - 137;
            if dx*dx + dy*dy < 13*13 then
                RGB := CLOUD_SYMBOL;
            end if;
        end if;

        if dashActive and rightCloudOn then
            if x >= 614 and x <= 692 and y >= 130 and y <= 142 then
                RGB := CLOUD_SYMBOL;
            end if;
            dx := x - 614;
            dy := y - 136;
            if dx*dx + dy*dy < 6*6 then
                RGB := CLOUD_SYMBOL;
            end if;
            dx := x - 692;
            dy := y - 136;
            if dx*dx + dy*dy < 6*6 then
                RGB := CLOUD_SYMBOL;
            end if;
        end if;

        -- hills
        dx := x - 400; dy := y - 438; arc := dx*dx + 8*dy*dy; if arc < 160000 then RGB := HILL_BACK; end if;
        dx := x - 255; dy := y - 430; arc := dx*dx + 8*dy*dy; if arc < 106000 then RGB := HILL_MID; end if;
        dx := x - 520; dy := y - 428; arc := dx*dx + 8*dy*dy; if arc < 106000 then RGB := HILL_MID; end if;
        dx := x - 400; dy := y - 474; arc := dx*dx + 7*dy*dy; if arc < 180000 then RGB := HILL_FRONT; end if;

        -- trees -- maybe add ass bitmap
        dx := x - 282; if dx < 0 then dx := -dx; end if;
        dy := y - 306; if dy >= 0 and dy <= 20 and dx*20 < dy*9 then RGB := TREE_DARK; end if;
        dy := y - 322; if dy >= 0 and dy <= 24 and dx*24 < dy*14 then RGB := TREE_DARK; end if;
        dy := y - 340; if dy >= 0 and dy <= 30 and dx*30 < dy*19 then RGB := TREE_DARK; end if;

        dx := x - 402; if dx < 0 then dx := -dx; end if;
        dy := y - 304; if dy >= 0 and dy <= 20 and dx*20 < dy*9 then RGB := TREE_DARK; end if;
        dy := y - 320; if dy >= 0 and dy <= 24 and dx*24 < dy*14 then RGB := TREE_DARK; end if;
        dy := y - 338; if dy >= 0 and dy <= 30 and dx*30 < dy*19 then RGB := TREE_DARK; end if;

        dx := x - 522; if dx < 0 then dx := -dx; end if;
        dy := y - 306; if dy >= 0 and dy <= 20 and dx*20 < dy*9 then RGB := TREE_DARK; end if;
        dy := y - 322; if dy >= 0 and dy <= 24 and dx*24 < dy*14 then RGB := TREE_DARK; end if;
        dy := y - 340; if dy >= 0 and dy <= 30 and dx*30 < dy*19 then RGB := TREE_DARK; end if;

        dx := x - 342; if dx < 0 then dx := -dx; end if;
        dy := y - 286; if dy >= 0 and dy <= 28 and dx*28 < dy*17 then RGB := TREE_LIGHT; end if;
        dy := y - 302; if dy >= 0 and dy <= 32 and dx*32 < dy*22 then RGB := TREE_LIGHT; end if;
        dy := y - 320; if dy >= 0 and dy <= 38 and dx*38 < dy*27 then RGB := TREE_LIGHT; end if;

        dx := x - 466; if dx < 0 then dx := -dx; end if;
        dy := y - 286; if dy >= 0 and dy <= 28 and dx*28 < dy*17 then RGB := TREE_LIGHT; end if;
        dy := y - 302; if dy >= 0 and dy <= 32 and dx*32 < dy*22 then RGB := TREE_LIGHT; end if;
        dy := y - 320; if dy >= 0 and dy <= 38 and dx*38 < dy*27 then RGB := TREE_LIGHT; end if;

        -- balony
        if x >= BALON_BIG_X and x < BALON_BIG_X + BALON_BIG_W and y >= BALON_BIG_Y and y < BALON_BIG_Y + BALON_BIG_H then
            imgRect := 1;
        elsif x >= BALON_GRAY_X and x < BALON_GRAY_X + BALON_W and y >= BALON_GRAY_Y and y < BALON_GRAY_Y + BALON_H then
            imgRect := 2;
        elsif x >= BALON_PLAIN_X and x < BALON_PLAIN_X + BALON_W and y >= BALON_PLAIN_Y and y < BALON_PLAIN_Y + BALON_H then
            imgRect := 3;
        end if;

        -- prebarveni balonu
        imgColor := to_integer(unsigned(balon_q));
        if imgRect > 0 and imgColor /= BALON_TRANSPARENT and imgColor <= 102 then
            rgbSrc := BALON_PALETTE(imgColor);
            if imgRect = 2 or (imgRect = 1 and morseBit = '0') then
                RGB := toGray(rgbSrc);
            else
                RGB := rgbSrc;
            end if;
        end if;

        case imgRect is
            when 1 =>
                balon_addr <= std_logic_vector(to_unsigned((to_integer(yrow(9 downto 2)) - BALON_BIG_Y4)*BALON_W
                    + (to_integer(xcolumn(9 downto 2)) - BALON_BIG_X4), balon_addr'LENGTH));
            when 2 =>
                balon_addr <= std_logic_vector(to_unsigned((BALON_H - 1 - (x - BALON_GRAY_X))*BALON_W
                    + (y - BALON_GRAY_Y), balon_addr'LENGTH));
            when 3 =>
                balon_addr <= std_logic_vector(to_unsigned((y - BALON_PLAIN_Y)*BALON_W
                    + (x - BALON_PLAIN_X), balon_addr'LENGTH));
            when others =>
                balon_addr <= (others => '0');
        end case;

        -- letters of morse from bitmap with highlighting of current letter
        if x >= WORD_XLEFT and x < WORD_XLEFT + LETTERS_COUNT*LETTER_W*WORD_SCALE and
           y >= WORD_YTOP and y < WORD_YTOP + LETTER_H*WORD_SCALE then
            letterX := (x - WORD_XLEFT) / WORD_SCALE;
            letterY := (y - WORD_YTOP) / WORD_SCALE;
            letterIx := letterX / LETTER_W;
            pernic_addr <= std_logic_vector(to_unsigned(letterY * (LETTER_W * LETTERS_COUNT) + letterX, pernic_addr'length));
            pixIdx := to_integer(unsigned(pernic_q));
            if pixIdx = 0 then
                if letterIx = activeLetter then
                    RGB := ToRGB(232, 36, 28);
                else
                    RGB := BLACK;
                end if;
            elsif pixIdx = 2 then
                RGB := WHITE;
            end if;
        end if;

        -- speed buttons under the rainbow
        dx := x - SPEED_MINUS_XCENTER;
        dy := y - SPEED_MINUS_YCENTER;
        arc := dx*dx + dy*dy;
        if arc <= SPEED_TOUCH_RADIUS*SPEED_TOUCH_RADIUS then
            RGB := SPEED_BUTTON_FILL;
        elsif arc <= (SPEED_TOUCH_RADIUS + 2)*(SPEED_TOUCH_RADIUS + 2) then
            RGB := SPEED_BUTTON_EDGE;
        end if;
        if x >= SPEED_MINUS_XCENTER - 8 and x <= SPEED_MINUS_XCENTER + 8 and
           y >= SPEED_MINUS_YCENTER - 2 and y <= SPEED_MINUS_YCENTER + 2 then
            RGB := SPEED_SYMBOL;
        end if;

        dx := x - SPEED_PLUS_XCENTER;
        dy := y - SPEED_PLUS_YCENTER;
        arc := dx*dx + dy*dy;
        if arc <= SPEED_TOUCH_RADIUS*SPEED_TOUCH_RADIUS then
            RGB := SPEED_BUTTON_FILL;
        elsif arc <= (SPEED_TOUCH_RADIUS + 2)*(SPEED_TOUCH_RADIUS + 2) then
            RGB := SPEED_BUTTON_EDGE;
        end if;
        if ((x >= SPEED_PLUS_XCENTER - 8 and x <= SPEED_PLUS_XCENTER + 8 and
             y >= SPEED_PLUS_YCENTER - 2 and y <= SPEED_PLUS_YCENTER + 2) or
            (x >= SPEED_PLUS_XCENTER - 2 and x <= SPEED_PLUS_XCENTER + 2 and
             y >= SPEED_PLUS_YCENTER - 8 and y <= SPEED_PLUS_YCENTER + 8)) then
            RGB := SPEED_SYMBOL;
        end if;

        -- delay buttons and bar indicator
        dx := x - PAUSE_MINUS_XCENTER;
        dy := y - PAUSE_MINUS_YCENTER;
        arc := dx*dx + dy*dy;
        if arc <= PAUSE_TOUCH_RADIUS*PAUSE_TOUCH_RADIUS then
            RGB := PAUSE_BUTTON_FILL;
        elsif arc <= (PAUSE_TOUCH_RADIUS + 2)*(PAUSE_TOUCH_RADIUS + 2) then
            RGB := PAUSE_BUTTON_EDGE;
        end if;
        if x >= PAUSE_MINUS_XCENTER - 8 and x <= PAUSE_MINUS_XCENTER + 8 and
           y >= PAUSE_MINUS_YCENTER - 2 and y <= PAUSE_MINUS_YCENTER + 2 then
            RGB := PAUSE_SYMBOL;
        end if;

        dx := x - PAUSE_PLUS_XCENTER;
        dy := y - PAUSE_PLUS_YCENTER;
        arc := dx*dx + dy*dy;
        if arc <= PAUSE_TOUCH_RADIUS*PAUSE_TOUCH_RADIUS then
            RGB := PAUSE_BUTTON_FILL;
        elsif arc <= (PAUSE_TOUCH_RADIUS + 2)*(PAUSE_TOUCH_RADIUS + 2) then
            RGB := PAUSE_BUTTON_EDGE;
        end if;
        if ((x >= PAUSE_PLUS_XCENTER - 8 and x <= PAUSE_PLUS_XCENTER + 8 and
             y >= PAUSE_PLUS_YCENTER - 2 and y <= PAUSE_PLUS_YCENTER + 2) or
            (x >= PAUSE_PLUS_XCENTER - 2 and x <= PAUSE_PLUS_XCENTER + 2 and
             y >= PAUSE_PLUS_YCENTER - 8 and y <= PAUSE_PLUS_YCENTER + 8)) then
            RGB := PAUSE_SYMBOL;
        end if;

        for i in 0 to PAUSE_LEVELS - 1 loop
            if x >= 584 + i*10 and x < 592 + i*10 and y >= 30 and y < 40 then
                RGB := assignIf(i <= pauseIx, PAUSE_BAR_ON, PAUSE_BAR_OFF);
            end if;
        end loop;

        -- 7-segment countdown of delay, next to play/pause button
        if commandStop = '0' and pauseCountIx > 0 and
           x >= PAUSE_DIGIT_XCENTER - DIGIT_HALF_W - DIGIT_SEG_T and
           x <= PAUSE_DIGIT_XCENTER + DIGIT_HALF_W + DIGIT_SEG_T and
           y >= PAUSE_DIGIT_YCENTER - DIGIT_HALF_H - DIGIT_SEG_T and
           y <= PAUSE_DIGIT_YCENTER + DIGIT_HALF_H + DIGIT_SEG_T then
            digitMask := sevenSegMask(pauseCountIx - 1);
            for seg in 0 to 6 loop -- snad mozu pouzivat loop
                if x >= PAUSE_DIGIT_XCENTER + SEG_X1(seg) and x <= PAUSE_DIGIT_XCENTER + SEG_X2(seg) and
                   y >= PAUSE_DIGIT_YCENTER + SEG_Y1(seg) and y <= PAUSE_DIGIT_YCENTER + SEG_Y2(seg) then
                    RGB := assignIf(digitMask(6-seg) = '1', PAUSE_COUNTDOWN, PAUSE_DIGIT_OFF);
                end if;
            end loop;
            digitMask := sevenSegMask(speedIx + 1);
        end if;

        -- speed 7-segment
        if x >= DIGIT_XCENTER - DIGIT_HALF_W - DIGIT_SEG_T and
           x <= DIGIT_XCENTER + DIGIT_HALF_W + DIGIT_SEG_T and
           y >= DIGIT_YCENTER - DIGIT_HALF_H - DIGIT_SEG_T and
           y <= DIGIT_YCENTER + DIGIT_HALF_H + DIGIT_SEG_T then
            for seg in 0 to 6 loop
                if x >= DIGIT_XCENTER + SEG_X1(seg) and x <= DIGIT_XCENTER + SEG_X2(seg) and
                   y >= DIGIT_YCENTER + SEG_Y1(seg) and y <= DIGIT_YCENTER + SEG_Y2(seg) then
                    RGB := assignIf(digitMask(6-seg) = '1', SPEED_DIGIT_ON, SPEED_DIGIT_OFF);
                end if;
            end loop;
        end if;

        -- play/pause button
        dx := x - PLAY_TOUCH_XCENTER;
        dy := y - PLAY_TOUCH_YCENTER;
        arc := dx*dx + dy*dy;
        if arc <= PLAY_TOUCH_RADIUS*PLAY_TOUCH_RADIUS then
            RGB := PLAY_BUTTON_FILL;
        elsif arc <= (PLAY_TOUCH_RADIUS + 2)*(PLAY_TOUCH_RADIUS + 2) then
            RGB := PLAY_BUTTON_EDGE;
        end if;

        if showPauseIcon then
            if (x >= PLAY_TOUCH_XCENTER - 8 and x < PLAY_TOUCH_XCENTER - 3 and
                y >= PLAY_TOUCH_YCENTER - 9 and y < PLAY_TOUCH_YCENTER + 9) or
               (x >= PLAY_TOUCH_XCENTER + 3 and x < PLAY_TOUCH_XCENTER + 8 and
                y >= PLAY_TOUCH_YCENTER - 9 and y < PLAY_TOUCH_YCENTER + 9) then
                RGB := STOP_ICON;
            end if;
        else
            if x >= PLAY_TOUCH_XCENTER - 6 and x <= PLAY_TOUCH_XCENTER + 6 and
               y >= PLAY_TOUCH_YCENTER - 6 and y <= PLAY_TOUCH_YCENTER + 6 and
               abs(y - PLAY_TOUCH_YCENTER) * 2 <= 12 - (x - (PLAY_TOUCH_XCENTER - 6)) then
                RGB := PLAY_ICON;
            end if;
        end if;

        -- roztahly morse dole
        if x >= MORSE_XLEFT and x <= MORSE_XRIGHT and y >= MORSE_YTOP and y <= MORSE_TRACK_BOTTOM then
            RGB := MORSE_STRIP_BG;
            if x = MORSE_XLEFT or x = MORSE_XRIGHT or y = MORSE_YTOP or y = MORSE_TRACK_BOTTOM then
                RGB := MORSE_STRIP_LINE;
            elsif y >= MORSE_YBASE and y <= MORSE_YBASE + 1 then
                RGB := MORSE_STRIP_LINE;
            elsif y >= MORSE_YBASE - 4 and y <= MORSE_YBASE - 2 then
                RGB := MORSE_GAP_COLOR;
            end if;

            localX := x - MORSE_XLEFT;
            mappedIx := MORSE_STEPS - 1;
            for i in 0 to MORSE_STEPS - 1 loop
                if localX >= MORSE_EDGE_X(i) and localX < MORSE_EDGE_X(i + 1) then
                    mappedIx := i;
                end if;
            end loop;
            if localX < MORSE_EDGE_X(0) then
                mappedIx := 0;
            end if;

            if isMorseLit(mappedIx) and y >= MORSE_SYMBOL_TOP and y <= MORSE_YBASE - 3 then
                if isDashStep(mappedIx) then
                    RGB := MORSE_DASH_COLOR;
                else
                    RGB := MORSE_DOT_COLOR;
                end if;
                if mappedIx = currentIx then
                    RGB := MORSE_ACTIVE_COLOR;
                end if;
            end if;
        end if;

        -- morse pointer
        pointerX := MORSE_POINTER_X(currentIx);
        dx := x - pointerX;
        dy := y - (MORSE_YBASE + 8);
        if dx*dx + dy*dy < 7*7 then
            if morseBit = '1' then
                RGB := MORSE_ACTIVE_COLOR;
            else
                RGB := MORSE_POINTER_IDLE;
            end if;
        end if;

        -- Outside the visible LCD area we always output black.
        if LCD_DE = '0' then RGB := BLACK; end if;
        RGBcolor <= RGB;
    end process;

end architecture;
