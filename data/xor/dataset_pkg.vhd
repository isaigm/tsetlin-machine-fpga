-- Automatically generated: 2-bit XOR
-- Samples 0..3: training. Samples 4..7: test.
library ieee;
  use ieee.std_logic_1164.all;

package dataset_pkg is
    constant N_ATTRIBUTES: integer := 2;
    constant N_TRAIN:      integer := 4;
    constant N_TEST:       integer := 4;
    constant N_SAMPLES:    integer := 8;
    constant N_RULES:      integer := 4;
    constant MAX_UPDATES:  integer := 100;   -- training epochs

    type samples_t is array (0 to N_SAMPLES - 1) of std_logic_vector(N_ATTRIBUTES - 1 downto 0);
    type seeds_t   is array (0 to N_RULES - 1) of std_logic_vector(15 downto 0);

    -- bit i = class of sample i
    constant CLASSES: std_logic_vector(N_SAMPLES - 1 downto 0) :=
        "01100110";
    -- bit i = class of rule i
    constant TARGET_CLASSES: std_logic_vector(N_RULES - 1 downto 0) := "0011";
    constant SEEDS: seeds_t := (x"ACE1", x"E255", x"ACCB", x"E512");
    constant TOP_SEED: std_logic_vector(15 downto 0) := x"ACC1";

    constant SAMPLES: samples_t := (
        "00",
        "01",
        "10",
        "11",
        "00",
        "01",
        "10",
        "11"
    );
end package;
