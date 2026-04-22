-------------------------------------------------------------
-- LCD image created by logic
-------------------------------------------------------------

library ieee, work; use ieee.std_logic_1164.all;
use ieee.numeric_std.all; -- for integer and unsigned types
use work.LCDpackV2.all;

entity LCDlogicMy is
    port(xcolumn, yrow  : in  xy_t  := XY_ZERO; -- x, y-coordinate of pixel (column, row indexes)
           XEND_N   : in  std_logic := '0'; -- 32.2 kHz'; '0' only when xcolumn=XCOLUMN_MAX, otherwise '1;
           YEND_N   : in  std_logic := '0'; -- 61.4 Hz; '0' only when max yrow=YROW_MAX, otherwise '1',
           LCD_DE   : in  std_logic := '0'; -- DataEnable indicates the visible part of LCD
           LCD_DCLK : in  std_logic := '0'; -- 33 MHz exactly; LCD data clock
          RGBcolor : out RGB_t); --  defined in LCDpackV2; RGB_t = std_logic_vector(23 downto 0)
end entity;

architecture behavioral of LCDlogicMy is
    -- 103 barev z vygenerovane palety napred typ
    type palette103_t is array (0 to 102) of RGB_t;

    -- barvy
    constant FRAME_DARK     : RGB_t := ToRGB(2, 10, 34);
    constant FRAME_PATTERN  : RGB_t := ToRGB(8, 25, 60);
    constant FRAME_LINE     : RGB_t := ToRGB(20, 43, 80);
    constant SKY_TOP        : RGB_t := ToRGB(74, 174, 226);
    constant SKY_LOW        : RGB_t := ToRGB(82, 178, 220);
    constant CLOUD          : RGB_t := ToRGB(246, 250, 250);
    constant CLOUD_SHADE    : RGB_t := ToRGB(222, 236, 241);
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

    -- velikosti
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

    -- obsah palety
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

begin

    iBalonRom : entity work.balon_noshadow_white_opt port map(balon_addr, LCD_DCLK, balon_q);

    LSPimage : process(xcolumn, yrow, LCD_DE, balon_q)
        variable RGB       : RGB_t := BLACK;
        variable x         : integer range 0 to XCOLUMN_MAX := 0;
        variable y         : integer range 0 to YROW_MAX := 0;
        variable dx        : integer range -800 to 1000 := 0;
        variable dy        : integer range -500 to 500 := 0;
        variable x32       : integer range 0 to 31 := 0;
        variable y32       : integer range 0 to 31 := 0;
        variable arc       : integer range 0 to 6000000 := 0;
        variable skyOn     : boolean := false;
        variable imgRect   : integer range 0 to 3 := 0;
        variable imgColor  : integer range 0 to 127 := 0;
        variable rgbSrc    : RGB_t := BLACK;
        variable red8      : unsigned(7 downto 0) := (others => '0');
        variable green8    : unsigned(7 downto 0) := (others => '0');
        variable blue8     : unsigned(7 downto 0) := (others => '0');
        variable gray10    : unsigned(9 downto 0) := (others => '0');
        variable gray8     : std_logic_vector(7 downto 0) := (others => '0');
    begin
        x := to_integer(xcolumn);
        y := to_integer(yrow);
        x32 := to_integer(xcolumn(4 downto 0));
        y32 := to_integer(yrow(4 downto 0));
        imgRect := 0;
        imgColor := 0;
        rgbSrc := BLACK;
        red8 := (others => '0');
        green8 := (others => '0');
        blue8 := (others => '0');
        gray10 := (others => '0');
        gray8 := (others => '0');
        balon_addr <= (others => '0');

        -- ZACATEK VYKRESLOVACI LOGIKY
        -- tmave pozadi a opakovany ctvercovy vzor ramecku
        RGB := FRAME_DARK; -- def. barva
        if x32 < 2 or y32 < 2 then
            RGB := FRAME_LINE;
        elsif (x32 < 13 and y32 < 13) or (x32 >= 20 and y32 >= 20) then
            RGB := FRAME_PATTERN;
        end if;

        -- velka elipsa oblohy
        skyOn := false;
        dx := x - 400;
        dy := y - 214;
        arc := 2*dx*dx + 9*dy*dy;
        if arc < 304000 then
            skyOn := true;
            RGB := SKY_TOP;
            if y > 170 then RGB := SKY_LOW; end if;
        end if;

        -- oblouk duhy v obloze
        dx := x - 400;
        dy := y - 400;
        arc := dx*dx + 2*dy*dy;
        if skyOn and y > 142 and y < 342 and arc < 90000 and arc > 48000 then
            if arc > 83000 then
                RGB := RAINBOW_RED;
            elsif arc > 76000 then
                RGB := RAINBOW_ORANGE;
            elsif arc > 69000 then
                RGB := RAINBOW_YELLOW;
            elsif arc > 62000 then
                RGB := RAINBOW_GREEN;
            elsif arc > 55000 then
                RGB := RAINBOW_BLUE;
            else
                RGB := RAINBOW_PURPLE;
            end if;
        end if;

        if skyOn then
            -- levy dolni sedy mrak: levy lalok
            dx := x - 96; dy := y - 252; arc := 5*dx*dx + 12*dy*dy;
            if arc < 10200 then RGB := CLOUD_SHADE; end if;
            -- levy dolni sedy mrak: prostredni lalok
            dx := x - 134; dy := y - 238; arc := 5*dx*dx + 12*dy*dy;
            if arc < 9200 then RGB := CLOUD_SHADE; end if;
            -- levy dolni sedy mrak: pravy lalok
            dx := x - 162; dy := y - 250; arc := 5*dx*dx + 12*dy*dy;
            if arc < 7000 then
                RGB := CLOUD_SHADE;
            end if;

            -- levy horni bily mrak: lalok 1
            dx := x - 126; dy := y - 142; arc := 4*dx*dx + 9*dy*dy;
            if arc < 11600 then RGB := CLOUD; end if;
            -- levy horni bily mrak: lalok 2
            dx := x - 172; dy := y - 128; arc := 4*dx*dx + 9*dy*dy;
            if arc < 14000 then RGB := CLOUD; end if;
            -- levy horni bily mrak: lalok 3
            dx := x - 224; dy := y - 144; arc := 4*dx*dx + 9*dy*dy;
            if arc < 11800 then RGB := CLOUD; end if;
            -- levy horni bily mrak: lalok 4
            dx := x - 256; dy := y - 126; arc := 5*dx*dx + 10*dy*dy;
            if arc < 9000 then RGB := CLOUD; end if;
            -- levy horni bily mrak: levy spodni lalok
            dx := x - 94; dy := y - 164; arc := 5*dx*dx + 12*dy*dy;
            if arc < 6600 then RGB := CLOUD; end if;

            -- pravy horni bily mrak: lalok 1
            dx := x - 570; dy := y - 148; arc := 4*dx*dx + 9*dy*dy;
            if arc < 10800 then RGB := CLOUD; end if;
            -- pravy horni bily mrak: lalok 2
            dx := x - 620; dy := y - 126; arc := 4*dx*dx + 9*dy*dy;
            if arc < 14200 then RGB := CLOUD; end if;
            -- pravy horni bily mrak: lalok 3
            dx := x - 676; dy := y - 146; arc := 4*dx*dx + 9*dy*dy;
            if arc < 11600 then RGB := CLOUD; end if;
            -- pravy horni bily mrak: lalok 4
            dx := x - 708; dy := y - 124; arc := 5*dx*dx + 10*dy*dy;
            if arc < 9000 then RGB := CLOUD; end if;
            -- pravy horni bily mrak: pravy spodni lalok
            dx := x - 746; dy := y - 166; arc := 5*dx*dx + 12*dy*dy;
            if arc < 6900 then RGB := CLOUD; end if;

            -- maly prostredni bily mrak: levy lalok
            dx := x - 366; dy := y - 126; arc := 5*dx*dx + 11*dy*dy;
            if arc < 3200 then RGB := CLOUD; end if;
            -- maly prostredni bily mrak: prostredni lalok
            dx := x - 388; dy := y - 116; arc := 5*dx*dx + 11*dy*dy;
            if arc < 3900 then RGB := CLOUD; end if;
            -- maly prostredni bily mrak: pravy lalok
            dx := x - 412; dy := y - 128; arc := 5*dx*dx + 11*dy*dy;
            if arc < 3200 then RGB := CLOUD; end if;

            -- ptak vlevo
            dx := x - 306; dy := y - 87; arc := 3*dx*dx + 10*dy*dy;
            if x >= 278 and x <= 334 and y >= 75 and y <= 87 and arc > 920 and arc < 1420 then RGB := BIRD; end if;
            -- ptak uprostred
            dx := x - 476; dy := y - 111; arc := 3*dx*dx + 10*dy*dy;
            if x >= 448 and x <= 504 and y >= 99 and y <= 111 and arc > 920 and arc < 1420 then RGB := BIRD; end if;
            -- ptak vpravo
            dx := x - 514; dy := y - 65; arc := 3*dx*dx + 10*dy*dy;
            if x >= 486 and x <= 542 and y >= 53 and y <= 65 and arc > 920 and arc < 1420 then RGB := BIRD; end if;
        end if;

        -- zadni svetly kopec
        dx := x - 400; dy := y - 438; arc := dx*dx + 8*dy*dy;
        if arc < 160000 then RGB := HILL_BACK; end if;
        -- levy stredni kopec
        dx := x - 255; dy := y - 430; arc := dx*dx + 8*dy*dy;
        if arc < 106000 then RGB := HILL_MID; end if;
        -- pravy stredni kopec
        dx := x - 520; dy := y - 428; arc := dx*dx + 8*dy*dy;
        if arc < 106000 then RGB := HILL_MID; end if;
        -- predni tmavy kopec
        dx := x - 400; dy := y - 474; arc := dx*dx + 7*dy*dy;
        if arc < 180000 then RGB := HILL_FRONT; end if;

        -- tmavy strom1
        dx := x - 282; if dx < 0 then dx := -dx; end if;
        dy := y - 306; if dy >= 0 and dy <= 20 and dx*20 < dy*9 then RGB := TREE_DARK; end if;
        dy := y - 322; if dy >= 0 and dy <= 24 and dx*24 < dy*14 then RGB := TREE_DARK; end if;
        dy := y - 340; if dy >= 0 and dy <= 30 and dx*30 < dy*19 then RGB := TREE_DARK; end if;

        -- tmavy strom2
        dx := x - 402; if dx < 0 then dx := -dx; end if;
        dy := y - 304; if dy >= 0 and dy <= 20 and dx*20 < dy*9 then RGB := TREE_DARK; end if;
        dy := y - 320; if dy >= 0 and dy <= 24 and dx*24 < dy*14 then RGB := TREE_DARK; end if;
        dy := y - 338; if dy >= 0 and dy <= 30 and dx*30 < dy*19 then RGB := TREE_DARK; end if;

        -- tmavy strom vpravo3
        dx := x - 522; if dx < 0 then dx := -dx; end if;
        dy := y - 306; if dy >= 0 and dy <= 20 and dx*20 < dy*9 then RGB := TREE_DARK; end if;
        dy := y - 322; if dy >= 0 and dy <= 24 and dx*24 < dy*14 then RGB := TREE_DARK; end if;
        dy := y - 340; if dy >= 0 and dy <= 30 and dx*30 < dy*19 then RGB := TREE_DARK; end if;

        -- svetly strom vlevo1
        dx := x - 342; if dx < 0 then dx := -dx; end if;
        dy := y - 286; if dy >= 0 and dy <= 28 and dx*28 < dy*17 then RGB := TREE_LIGHT; end if;
        dy := y - 302; if dy >= 0 and dy <= 32 and dx*32 < dy*22 then RGB := TREE_LIGHT; end if;
        dy := y - 320; if dy >= 0 and dy <= 38 and dx*38 < dy*27 then RGB := TREE_LIGHT; end if;

        -- svetly strom vpravo2
        dx := x - 466; if dx < 0 then dx := -dx; end if;
        dy := y - 286; if dy >= 0 and dy <= 28 and dx*28 < dy*17 then RGB := TREE_LIGHT; end if;
        dy := y - 302; if dy >= 0 and dy <= 32 and dx*32 < dy*22 then RGB := TREE_LIGHT; end if;
        dy := y - 320; if dy >= 0 and dy <= 38 and dx*38 < dy*27 then RGB := TREE_LIGHT; end if;

        -- volby typu balonu v zavislosti na souradnicich
        -- velky barevny balon zvetseny ctenim ROM po blocich 4x4 px
        if x >= BALON_BIG_X and x < BALON_BIG_X + BALON_BIG_W and y >= BALON_BIG_Y and y < BALON_BIG_Y + BALON_BIG_H then
            imgRect := 1;
        -- mensi otoceny balon, ktery se dale vykresli sedou paletou
        elsif x >= BALON_GRAY_X and x < BALON_GRAY_X + BALON_W and y >= BALON_GRAY_Y and y < BALON_GRAY_Y + BALON_H then
            imgRect := 2;
        -- mensi balon vykresleny 1:1
        elsif x >= BALON_PLAIN_X and x < BALON_PLAIN_X + BALON_W and y >= BALON_PLAIN_Y and y < BALON_PLAIN_Y + BALON_H then
            imgRect := 3;
        end if;

        -- barva pixelu nacteneho z ROM balonu
        imgColor := to_integer(unsigned(balon_q));
        if imgRect > 0 and imgColor /= BALON_TRANSPARENT and imgColor <= 102 then
            rgbSrc := BALON_PALETTE(imgColor);
            -- prevod otoceneho balonu do sede
            if imgRect = 2 then
                red8 := unsigned(rgbSrc(23 downto 16));
                green8 := unsigned(rgbSrc(15 downto 8));
                blue8 := unsigned(rgbSrc(7 downto 0));
                gray10 := shift_right(resize(red8, 10), 2) + shift_right(resize(red8, 10), 5)
                        + shift_right(resize(green8, 10), 1) + shift_right(resize(green8, 10), 4)
                        + shift_right(resize(blue8, 10), 4) + shift_right(resize(blue8, 10), 5);
                gray8 := std_logic_vector(gray10(7 downto 0));
                RGB := RGB_t'(gray8 & gray8 & gray8);
            else
                RGB := rgbSrc;
            end if;
        end if;

        -- adresa do jedine ROM pro zvoleny balon
        case imgRect is
            when 1 =>
                -- adresa pro velky balon: zmenseni souradnic vyberem hornich bitu
                balon_addr <= std_logic_vector(to_unsigned((to_integer(yrow(9 downto 2)) - BALON_BIG_Y4)*BALON_W
                    + (to_integer(xcolumn(9 downto 2)) - BALON_BIG_X4), balon_addr'LENGTH));
            when 2 =>
                -- adresa pro otoceny sedy balon
                balon_addr <= std_logic_vector(to_unsigned((BALON_H - 1 - (x - BALON_GRAY_X))*BALON_W
                    + (y - BALON_GRAY_Y), balon_addr'LENGTH));
            when 3 =>
                -- adresa pro balon beze zmeny
                balon_addr <= std_logic_vector(to_unsigned((y - BALON_PLAIN_Y)*BALON_W
                    + (x - BALON_PLAIN_X), balon_addr'LENGTH));
            when others =>
                balon_addr <= (others => '0');
        end case;
        -----------------------------------------------------

        if LCD_DE = '0' then RGB := BLACK; end if;
        RGBcolor <= RGB;
    end process;

end architecture;
