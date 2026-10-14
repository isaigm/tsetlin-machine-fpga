"""Writes dataset_pkg.vhd (for the hardware) and dataset.json (for the Python model)."""
import json, os

def slv(bits):
    """List of bits -> VHDL literal for an (N-1 downto 0) vector: bit i ends up at position i."""
    return '"' + "".join(str(b) for b in reversed(bits)) + '"'

def write_dataset(out_dir, name, samples, classes, n_train, target, seeds, top_seed, max_updates, notes=""):
    os.makedirs(out_dir, exist_ok=True)
    n_attr, n_all = len(samples[0]), len(samples)
    with open(os.path.join(out_dir, "dataset_pkg.vhd"), "w") as f:
        f.write(f"""-- Automatically generated: {name}
{notes}-- Samples 0..{n_train-1}: training. Samples {n_train}..{n_all-1}: test.
library ieee;
  use ieee.std_logic_1164.all;

package dataset_pkg is
    constant N_ATTRIBUTES: integer := {n_attr};
    constant N_TRAIN:      integer := {n_train};
    constant N_TEST:       integer := {n_all - n_train};
    constant N_SAMPLES:    integer := {n_all};
    constant N_RULES:      integer := {len(target)};
    constant MAX_UPDATES:  integer := {max_updates};   -- training epochs

    type samples_t is array (0 to N_SAMPLES - 1) of std_logic_vector(N_ATTRIBUTES - 1 downto 0);
    type seeds_t   is array (0 to N_RULES - 1) of std_logic_vector(15 downto 0);

    -- bit i = class of sample i
    constant CLASSES: std_logic_vector(N_SAMPLES - 1 downto 0) :=
        {slv(classes)};
    -- bit i = class of rule i
    constant TARGET_CLASSES: std_logic_vector(N_RULES - 1 downto 0) := {slv(target)};
    constant SEEDS: seeds_t := ({", ".join(f'x"{s:04X}"' for s in seeds)});
    constant TOP_SEED: std_logic_vector(15 downto 0) := x"{top_seed:04X}";

    constant SAMPLES: samples_t := (
""")
        for i, s in enumerate(samples):
            f.write(f"        {slv(s)}{',' if i < n_all - 1 else ''}\n")
        f.write("    );\nend package;\n")
    json.dump({"name": name, "S": samples, "C": classes, "n_train": n_train, "target": target,
               "seeds": seeds, "top_seed": top_seed, "max_updates": max_updates},
              open(os.path.join(out_dir, "dataset.json"), "w"))
    print(f"{name}: {n_attr} attributes, {n_train} training, {n_all - n_train} test, "
          f"{len(target)} rules, {max_updates} epochs -> {out_dir}")
