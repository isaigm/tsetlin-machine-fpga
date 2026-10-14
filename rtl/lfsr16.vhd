library ieee;
  use ieee.std_logic_1164.all;

entity lfsr16 is
  generic (
    SEED  : std_logic_vector(15 downto 0) := x"ACE1";
    STEPS : natural := 16                       -- steps per clock cycle
  );
  port (
    clk  : in  std_logic;
    rst  : in  std_logic;
    en   : in  std_logic;                       -- advances only when a value is consumed
    rand : out std_logic_vector(15 downto 0)
  );
end entity lfsr16;

architecture rtl of lfsr16 is
  signal lfsr : std_logic_vector(15 downto 0) := SEED;
begin
  process(clk)
    variable s  : std_logic_vector(15 downto 0);
    variable fb : std_logic;
  begin
    if rising_edge(clk) then
      if rst = '1' then
        lfsr <= SEED;
      elsif en = '1' then
        s := lfsr;
        for i in 1 to STEPS loop                -- unrolled into combinational logic, not a loop in time
          fb := s(0) xor s(2) xor s(3) xor s(5);
          s  := fb & s(15 downto 1);
        end loop;
        lfsr <= s;
      end if;
    end if;
  end process;
  rand <= lfsr;
end architecture rtl;
