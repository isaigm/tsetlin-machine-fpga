#!/usr/bin/env bash
# Simulates with GHDL and compares against the bit-exact model.
# Usage: sim/run_sim.sh xor | breast_cancer
set -euo pipefail
DATASET=${1:-breast_cancer}
ROOT=$(cd "$(dirname "$0")/.." && pwd)
BUILD="$ROOT/sim/build_$DATASET"
mkdir -p "$BUILD" && cd "$BUILD"
rm -f *.cf

FILES="$ROOT/data/$DATASET/dataset_pkg.vhd $ROOT/rtl/lfsr16.vhd $ROOT/rtl/rule.vhd $ROOT/rtl/tsetlin_machine.vhd"
ghdl -a --std=08 $FILES "$ROOT/sim/tb_tsetlin_machine.vhd" "$ROOT/sim/tb_check.vhd"

echo "== tb_tsetlin_machine"
ghdl -e --std=08 tb_tsetlin_machine
ghdl -r --std=08 tb_tsetlin_machine 2>&1 | grep -oE "(Finished|Correct).*"

echo "== tb_check + comparison against the model"
ghdl -e --std=08 tb_check
ghdl -r --std=08 tb_check > /dev/null
python3 "$ROOT/model/compare_hw_model.py" "$ROOT/data/$DATASET/dataset.json" test_evals.txt
