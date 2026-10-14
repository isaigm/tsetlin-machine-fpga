library ieee;
  use ieee.std_logic_1164.all;
  use ieee.numeric_std.all;
  use ieee.math_real.all;

entity rule is
  generic (
    SEED: std_logic_vector(15 downto 0) := x"ACE1";
    N_ATTRIBUTES: integer := 2;
    MEM_PROB:     integer := integer(0.7 * 65535);
    FORGET_PROB:  integer := integer(0.3 * 65535)
  );
  port (
    clk:       in std_logic;
    rst:       in std_logic;
    en_update: in std_logic;
    en_erase:  in std_logic;
    en_reject: in std_logic;
    sample:    in std_logic_vector(N_ATTRIBUTES - 1 downto 0);
    done:      out std_logic;
    eval:      out std_logic
  );
end entity;

architecture Behavioral of rule is
    type states_t is array (0 to 2 * N_ATTRIBUTES - 1) of unsigned(3 downto 0);
    type status_t is (IDLE, UPDATE_STATE, ERASE_STATE, REJECT_STATE);
    signal curr_status: status_t := IDLE;
    signal states: states_t := (others => (to_unsigned(5, 4)));
    signal next_states: states_t; 
    signal rand: std_logic_vector(15 downto 0);
    signal lfsr_en: std_logic;
    signal sample_idx: integer range 0 to N_ATTRIBUTES - 1 := 0;
    signal sample_r:  std_logic_vector(N_ATTRIBUTES - 1 downto 0);
    signal state_idx:  integer range 0 to 1 := 0;
    signal states_idx: integer range 0 to 2 * N_ATTRIBUTES - 1 := 0;
    signal s_done: std_logic := '0';
begin
    done <= s_done;
    lfsr_en <= '1' when curr_status = UPDATE_STATE or curr_status = ERASE_STATE else '0';
    lfsr16_inst: entity work.lfsr16
    generic map (
        SEED => SEED
    )
    port map (
      clk  => clk,
      rst  => rst,
      en  => lfsr_en,
      rand => rand
    );
    
    process(clk)
        variable temp: std_logic;
    begin
        if rising_edge(clk) then
            if rst = '1' then
                s_done      <= '0';
                state_idx   <= 0;
                sample_idx  <= 0;
                states_idx  <= 0;
                states      <= (others => (to_unsigned(5, 4)));
                sample_r    <= sample;
                curr_status <= IDLE;
            else
                s_done <= '0';
                case (curr_status) is
                    when IDLE => 
                        sample_r <= sample;
                        if en_update = '1' then
                            curr_status <= UPDATE_STATE;
                        elsif en_reject = '1' then
                            curr_status <= REJECT_STATE;
                        elsif en_erase = '1' then
                            curr_status <= ERASE_STATE;
                        end if;
                    when UPDATE_STATE =>
                        if state_idx = 0 then
                            temp := sample_r(sample_idx);
                        else
                            temp := not sample_r(sample_idx);
                        end if;

                        if temp = '1' then
                            if unsigned(rand) <= MEM_PROB then
                                if states(2 * sample_idx + state_idx) < 10 then
                                    states(2 * sample_idx + state_idx) <= states(2 * sample_idx + state_idx) + 1;
                                end if;
                            end if;
                        else 
                            if unsigned(rand) <= FORGET_PROB then
                                if states(2 * sample_idx + state_idx) > 1 then
                                    states(2 * sample_idx + state_idx) <= states(2 * sample_idx + state_idx) - 1;
                                end if;
                            end if;                        
                                
                        end if;
                        if state_idx = 1 then
                            state_idx <= 0;
                            if sample_idx = N_ATTRIBUTES - 1 then
                                sample_idx  <= 0;
                                curr_status <= IDLE;
                                s_done      <= '1';
                            else 
                                sample_idx <= sample_idx + 1;
                            end if;
                        else
                            state_idx <= state_idx + 1;
                        end if; 
                    when ERASE_STATE =>
                        if unsigned(rand) <= FORGET_PROB then
                            if states(states_idx) > 1 then
                                states(states_idx) <= states(states_idx) - 1;
                            end if;
                        end if;
                        if states_idx =  2 * N_ATTRIBUTES - 1 then
                            states_idx  <= 0;
                            curr_status <= IDLE;
                            s_done      <= '1';
                        else 
                            states_idx <= states_idx + 1;
                        end if; 
                    when REJECT_STATE =>
                        states      <= next_states;
                        curr_status <= IDLE;
                        s_done      <= '1';
                    when others =>
                
                end case ;
            end if;
        end if;
    end process;
     
    eval_rule: 
    process(sample_r, states)
        variable ev: std_logic;
    begin
        ev := '1';
        for i in 0 to N_ATTRIBUTES - 1 loop
            if not sample_r(i) = '1' and states(2 * i) >= 6 then
                ev := '0';
            end if;
            if sample_r(i) = '1' and states(2 * i + 1) >= 6 then
                ev := '0';
            end if;
        end loop;
        eval <= ev;
    end process;

    reject_rule:
    process(sample_r, states)
        variable next_st: states_t;
    begin
        next_st := states;
        for i in 0 to N_ATTRIBUTES - 1 loop
            if not sample_r(i) = '1' and states(2 * i) <= 5 then
                next_st(2 * i) := next_st(2 * i) + 1;
            end if;
            if sample_r(i) = '1' and states(2 * i + 1) <= 5 then
                next_st(2 * i + 1) := next_st(2 * i + 1) + 1;
            end if;
        end loop;
        next_states <= next_st;
    end process;
   
end architecture;
