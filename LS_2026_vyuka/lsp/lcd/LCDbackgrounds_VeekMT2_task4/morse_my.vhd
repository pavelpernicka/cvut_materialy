library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity MorseMY is
port (
    X : in unsigned(5 downto 0) := (others => '0');
    Y, STOP : out std_logic := '0'
);
end entity;

architecture behavioral of MorseMY is
signal a, b, c, d, e, f : std_logic := '0';
signal Y00, Y01, Y10, Y11 : std_logic := '0';
begin
-- PERNIC
a <= X(5);
b <= X(4);
c <= X(3);
d <= X(2);
e <= X(1);
f <= X(0);

Y00 <= (e and f)
    or (f and not c)
    or (c and not d and not e)
    or (d and not c and not e);

Y01 <= (d and e)
    or (d and f)
    or (c and f and not e)
    or (e and f and not c);

Y10 <= (d and f)
    or (c and e and f)
    or (c and d and not e)
    or (f and not c and not e);

Y11 <= (e and not d)
    or (f and not e);

with X(5 downto 4) select
    Y <= Y00 when "00",
         Y01 when "01",
         Y10 when "10",
         Y11 when others;

STOP <= a and b and d and e and f; -- 55 = 110111
end architecture;
