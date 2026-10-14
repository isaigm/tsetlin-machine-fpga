"""2-bit XOR. Generates data/xor/dataset_pkg.vhd and dataset.json.
   The 4 samples are used for training, and the same 4 for testing."""
import os
from dataset_tools import write_dataset

HERE = os.path.dirname(os.path.abspath(__file__))
samples = [[0, 0], [1, 0], [0, 1], [1, 1]]         # bit 0 first: "00", "01", "10", "11"
classes = [a ^ b for a, b in samples]
target = [1, 1, 0, 0]                              # rules 0, 1 -> class 1; rules 2, 3 -> class 0
seeds = [0xACE1, 0xE255, 0xACCB, 0xE512]

write_dataset(os.path.join(HERE, "xor"), "2-bit XOR", samples + samples, classes + classes, 4,
              target, seeds, 0xACC1, 100)
