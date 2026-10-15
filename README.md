# Tsetlin Machine on FPGA

A Tsetlin machine written in VHDL that trains and runs inference entirely on a Basys 3 board (Artix-7 XC7A35T). All rules are updated in parallel. It is tested on XOR and on the Breast Cancer Wisconsin (Original) dataset, and it closes timing at 100 MHz.

## Results

| Dataset | Rules | Epochs | Test accuracy | Training time at 100 MHz |
|---|---|---|---|---|
| XOR | 4 (2 per class) | 100 | 4 / 4 | 4 046 cycles (40 µs) |
| Breast Cancer Wisconsin | 20 (10 per class) | 50 | 204 / 205 (99.5 %) | 628 605 cycles (6.3 ms) |

On breast cancer, the only error is a benign sample classified as malignant; all 58 malignant test samples are detected. This result comes from one fixed 70/30 split and the LFSR seeds in the repository, which are at the top of the range: over 40 different sets of seeds, test accuracy ranged from 95.1 % to 99.5 % (median 98.0 %). Over 5 different splits, the Python reference averaged about 97 %.

## Timing closure

Worst negative slack measured in Vivado after implementation, at 100 MHz:

| Version | WNS | Approx. Fmax |
|---|---|---|
| Parallel update, `p` sent directly to the rules | −1.160 ns | 90 MHz |
| Parallel update, `p` registered (`p_r`) before reaching the rules | +0.365 ns | 104 MHz |

Registering `p` costs no extra cycles: `p` is ready in `UPDATE_RULES`, and the rules only use it two cycles later, in `SELECT_NEXT_OP`.

An earlier version updated one rule at a time. Its timing history shows what each pipeline register added:

| Sequential version | WNS | Approx. Fmax |
|---|---|---|
| No pipeline registers | −15.5 ns | 39 MHz |
| + `sample_r` (sample registered in each rule) | −5.0 ns | 67 MHz |
| + `class_r` (sample class registered in the top) | −6.5 ns | 61 MHz |
| + `eval_r` (rule outputs registered in the top) | +0.692 ns | 107 MHz |

Before `eval_r`, the worst path started at the automaton states of one rule, went through `eval`, the vote count, `p` and the comparison with the LFSR, and ended at the enable registers of all 20 rules: 21 logic levels, with 3.3 ns of logic delay and 12.5 ns of net delay. Registering `eval` split that trip across the chip into two cycles. `class_r` did not shorten the worst path; the small loss is place-and-route variation.

The parallel version trains about 9 times faster than the sequential one (628 605 vs. 5 924 957 cycles).

## Resources (Basys 3, breast cancer version)

After implementation in Vivado:

| LUT | FF | BRAM | DSP | Total power |
|---|---|---|---|---|
| 12 851 (61.8 %) | 5 603 (13.5 %) | 0 | 0 | 0.176 W |

Timing is met for setup (WNS +0.365 ns) and hold (WHS +0.072 ns). Most of the flip-flops are the automaton states: 20 rules × 54 automata × 4 bits = 4 320. The dataset is a combinational ROM, so it is implemented in LUTs, not BRAM.

## Architecture

Top-level state machine:

```
UPDATE_IDX -> WAIT_FOR_SAMPLE_R -> WAIT_FOR_EVAL -> UPDATE_RULES -> WAIT_FOR_DONE -> UPDATE_IDX
After the last epoch: WAIT_FOR_SAMPLE_R -> WAIT_FOR_EVAL -> TEST (one test sample at a time) -> FINISHED
```

Rule state machine:

```
IDLE -> SELECT_NEXT_OP -> UPDATE_STATE | ERASE_STATE | REJECT_STATE | (no feedback) -> IDLE
```

- **`rtl/tsetlin_machine.vhd`**: the top level. For each training sample it waits one cycle for the rules to capture the sample (`WAIT_FOR_SAMPLE_R`), captures every rule's output in `eval_r` (`WAIT_FOR_EVAL`), computes the feedback probability and sends one command to all rules at once (`UPDATE_RULES`). Then it waits until every rule reports `ready` (`WAIT_FOR_DONE`).

  The feedback probability is `p = (T - clamp(v)) / 2T`, where `T = 2` and `v` = (rules of the sample's class that output 1) − (rules of the sample's class that output 0). `p` is computed once per sample, before any rule changes. It comes from a 5-entry table built at elaboration time, so no multiplier or DSP is inferred.

- **`rtl/rule.vhd`**: one rule (clause) with `2 * N_ATTRIBUTES` Tsetlin automata. Each automaton has a 4-bit state from 1 to 10, and its literal is included when the state is 6 or more. Each rule has its own LFSR and decides its own feedback in `SELECT_NEXT_OP`. It uses `p` if it belongs to the sample's class and 0.5 otherwise; this reproduces the Python reference, where each class's rules are updated as a separate group. The possible feedback is:
  - **UPDATE** (the rule outputs 1 for a sample of its class): literals that are 1 are memorized with probability 0.7, and literals that are 0 are forgotten with probability 0.3.
  - **ERASE** (the rule outputs 0 for a sample of its class): every automaton is forgotten with probability 0.3.
  - **REJECT** (the rule outputs 1 for a sample of the other class): excluded literals that are 0 are moved one step toward inclusion.

  Updates process one automaton per clock cycle. `ready` is high only when the rule is in `IDLE` and no command is arriving in that cycle; without the second condition, the top would see every rule as finished in the cycle right after sending the command.

- **`rtl/lfsr16.vhd`**: Fibonacci LFSR with polynomial x^16 + x^14 + x^13 + x^11 + 1. It advances 16 steps per clock through an unrolled XOR network, so consecutive outputs share no bits. It only advances when a value is consumed, which makes the sequence reproducible in software.

## Data encoding (breast cancer)

The 16 rows with missing values are dropped, leaving 683 samples. Each of the 9 attributes (values 1 to 10) becomes 3 bits with thermometer encoding: `x >= 3`, `x >= 6`, `x >= 9`. That gives 27 boolean features. In the Python model, using all 9 thresholds (81 features) gave the same accuracy with three times the hardware.

## Verification

- `model/tm_model.py` is a bit-exact model of the hardware: same LFSRs, same order of random-number consumption, same decisions.
- `sim/tb_check.vhd` writes the output of every rule for every test sample; `model/compare_hw_model.py` checks them against the model. For breast cancer, all 205 × 20 values match, and so does the number of correct predictions. XOR also matches.
- `sim/tb_tsetlin_machine.vhd` runs the design until `LED(15)` turns on and reports the number of correct test predictions.
- `model/reference_xor.py` is the original floating-point Python implementation the hardware is based on.

## How to run

Generate the dataset package (the generated files are already included):

```
python3 data/gen_breast_cancer.py     # or: python3 data/gen_xor.py
```

Simulate with GHDL and compare against the model. Breast cancer takes about 3 minutes; XOR, a few seconds:

```
sim/run_sim.sh breast_cancer          # or: sim/run_sim.sh xor
```

In Vivado, add `rtl/*.vhd`, `data/<dataset>/dataset_pkg.vhd` and `constraints/basys3.xdc`. `tsetlin_machine` is the top level. `sim/tb_check.vhd` uses VHDL-2008 external names.

On the board, press BTNC to reset. Training starts when the button is released. `LED15` turns on when it finishes, and `LED7..0` show the number of correct test predictions in binary (204 = `11001100`).

## Dataset

Wolberg, W. *Breast Cancer Wisconsin (Original)* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5HP4Z. Licensed under CC BY 4.0. The CSV in `data/` is the UCI file without the sample ID column.

## License

MIT
