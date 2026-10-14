library ieee;
  use ieee.std_logic_1164.all;
  use ieee.numeric_std.all;
  use work.dataset_pkg.all;

entity tb_tsetlin_machine is
end entity;

architecture sim of tb_tsetlin_machine is
    constant CLK_PERIOD: time := 10 ns;          -- 100 MHz, same as the Basys 3
    signal clk:      std_logic := '0';
    signal rst:      std_logic := '1';
    signal LED:      std_logic_vector(15 downto 0);
    signal sim_done: boolean := false;
begin
    dut: entity work.tsetlin_machine
        port map (
            clk => clk,
            rst => rst,
            LED => LED
        );

    clk_gen: process
    begin
        while not sim_done loop
            clk <= '0';
            wait for CLK_PERIOD / 2;
            clk <= '1';
            wait for CLK_PERIOD / 2;
        end loop;
        wait;
    end process;

    stim: process
        variable hits: integer;
    begin
        rst <= '1';
        wait for 5 * CLK_PERIOD;
        wait until rising_edge(clk);
        rst <= '0';

        -- wait until LED(15) signals that training and test are finished
        wait until LED(15) = '1' for 50_000_000 * CLK_PERIOD;
        assert LED(15) = '1' report "did not finish within 50 million cycles" severity failure;

        hits := to_integer(unsigned(LED(7 downto 0)));
        report "Finished after " & integer'image(now / CLK_PERIOD) & " cycles";
        report "Correct test predictions: " & integer'image(hits) & " of " & integer'image(N_TEST)
             & " (" & integer'image((1000 * hits / N_TEST) / 10) & "." & integer'image((1000 * hits / N_TEST) mod 10) & "%)";

        wait for 10 * CLK_PERIOD;
        sim_done <= true;
        wait;
    end process;
end architecture;
