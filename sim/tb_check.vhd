-- Verification testbench: writes the eval output of every rule for every test sample
library ieee;
  use ieee.std_logic_1164.all;
  use ieee.numeric_std.all;
  use std.textio.all;
  use work.dataset_pkg.all;

entity tb_check is
end entity;

architecture sim of tb_check is
    constant CLK_PERIOD: time := 10 ns;
    signal clk:      std_logic := '0';
    signal rst:      std_logic := '1';
    signal LED:      std_logic_vector(15 downto 0);
    signal sim_done: boolean := false;
begin
    dut: entity work.tsetlin_machine port map (clk => clk, rst => rst, LED => LED);

    clk_gen: process
    begin
        while not sim_done loop
            clk <= '0'; wait for CLK_PERIOD / 2;
            clk <= '1'; wait for CLK_PERIOD / 2;
        end loop;
        wait;
    end process;

    stim: process
        alias sample_idx is << signal .tb_check.dut.sample_idx : integer range 0 to N_SAMPLES - 1 >>;
        alias eval       is << signal .tb_check.dut.eval : std_logic_vector(N_RULES - 1 downto 0) >>;
        file f: text open write_mode is "test_evals.txt";
        variable l: line;
    begin
        rst <= '1';
        wait for 5 * CLK_PERIOD;
        wait until rising_edge(clk);
        rst <= '0';
        loop
            wait until falling_edge(clk);
            if sample_idx >= N_TRAIN and LED(15) = '0' then     -- TEST state
                write(l, integer'image(sample_idx) & " ");
                for i in 0 to N_RULES - 1 loop                  -- rule 0 first
                    write(l, std_logic'image(eval(i))(2));
                end loop;
                writeline(f, l);
            end if;
            exit when LED(15) = '1';
        end loop;
        report "cycles: " & integer'image(now / CLK_PERIOD);
        write(l, "hits " & integer'image(to_integer(unsigned(LED(7 downto 0)))));
        writeline(f, l);
        sim_done <= true;
        wait;
    end process;
end architecture;
