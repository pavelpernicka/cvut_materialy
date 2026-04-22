library ieee; use ieee.std_logic_1164.all; use ieee.numeric_std.all;
library work;
entity testbench_MY is end entity;

architecture rtl of testbench_MY is
signal x:unsigned(5 downto 0):=(others=>'0');
signal y, stop : std_logic:='0';

begin
   imy : entity work.MorseMY port map (x,y,stop);
   x<= x+1 after 10 ns;
end architecture;
