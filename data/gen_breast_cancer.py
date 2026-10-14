"""Breast Cancer Wisconsin (Original), UCI. Generates data/breast_cancer/dataset_pkg.vhd and dataset.json.
   - Drops the 16 rows with '?' (683 remain)
   - Thermometer encoding with thresholds 3, 6, 9: each attribute (1..10) -> 3 bits (x>=3, x>=6, x>=9) -> 27 bits
   - Shuffles once with a fixed seed and splits 70% training / 30% test"""
import os, random
from dataset_tools import write_dataset

HERE = os.path.dirname(os.path.abspath(__file__))
THRESHOLDS = [3, 6, 9]
RULES_PER_CLASS = 10
MAX_UPDATES = 50
SPLIT_SEED = 2026
SEED_SEED = 7

rows = [l.strip().split(",") for l in open(os.path.join(HERE, "breast-cancer-wisconsin.csv"))
        if l.strip() and "?" not in l]
X = [[int(v) for v in r[:-1]] for r in rows]
Y = [0 if r[-1] == "2" else 1 for r in rows]                       # 0 = benign, 1 = malignant
bits = [[1 if x[a] >= t else 0 for a in range(9) for t in THRESHOLDS] for x in X]   # bit a*3+k

idx = list(range(len(Y)))
random.Random(SPLIT_SEED).shuffle(idx)
n_train = round(0.7 * len(Y))
rng = random.Random(SEED_SEED)
target = [0] * RULES_PER_CLASS + [1] * RULES_PER_CLASS            # rules 0..9 -> class 0, rules 10..19 -> class 1
seeds = [rng.randrange(1, 65536) for _ in target]

write_dataset(os.path.join(HERE, "breast_cancer"), "Breast Cancer Wisconsin (Original), UCI",
              [bits[i] for i in idx], [Y[i] for i in idx], n_train, target, seeds, 0xACC1, MAX_UPDATES,
              notes="-- Attribute a (0..8), threshold k (3, 6, 9) -> bit a*3+k: '1' if value >= threshold.\n"
                    "-- Class 0 = benign, 1 = malignant.\n")
