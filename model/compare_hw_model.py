"""Compares the output of sim/tb_check.vhd against the bit-exact model.
   Usage: python3 model/compare_hw_model.py data/<dataset>/dataset.json test_evals.txt"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tm_model import train

d = json.load(open(sys.argv[1]))
res = train(d["S"], d["C"], d["n_train"], d["target"], d["seeds"], epochs=d["max_updates"])
n = d["n_train"]
hw, hw_hits = {}, None
for l in open(sys.argv[2]):
    parts = l.split()
    if parts[0] == "hits":
        hw_hits = int(parts[1])
    else:
        hw[int(parts[0])] = tuple(int(b) for b in parts[1])
diff = [n + i for i in range(len(res)) if hw.get(n + i) != res[i][0]]
model_hits = sum(pred == d["C"][n + i] for i, (_, pred) in enumerate(res))
print(f"{d['name']}: {len(hw)} test samples, {len(diff)} with eval different from the model")
print(f"correct predictions: hardware {hw_hits}/{len(res)}, model {model_hits}/{len(res)}")
ok = not diff and hw_hits == model_hits
print("BIT-EXACT MATCH" if ok else f"MISMATCH in samples {diff[:10]}")
sys.exit(0 if ok else 1)
