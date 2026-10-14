"""Bit-exact model of the hardware: same decisions, same LFSRs, same order of random-number consumption.
   For each sample and each rule, p is computed from the rules of the sample's class (rules that output 1
   minus rules that output 0); rules of the other class use p = 0.5. Then UPDATE, ERASE or REJECT is applied."""
import json, sys

MEM_PROB, FORGET_PROB = 45875, 19661           # integer(0.7*65535), integer(0.3*65535) as rounded by GHDL

def lfsr_next(s):
    for _ in range(16):
        fb = (s ^ (s >> 2) ^ (s >> 3) ^ (s >> 5)) & 1
        s = (s >> 1) | (fb << 15)
    return s
NEXT = [lfsr_next(s) for s in range(65536)]

def literals(x):                               # index 2i -> x_i, 2i+1 -> not x_i
    L = []
    for b in x:
        L += [b, 1 - b]
    return L

def train(S, C, n_train, target, seeds, top_seed, T=2, epochs=50, checkpoints=()):
    R = len(target); N2 = 2 * len(S[0])
    st = [[5] * N2 for _ in range(R)]
    lfsr = list(seeds); top = top_seed
    Ls = [literals(x) for x in S]
    zmask = [sum(1 << j for j in range(N2) if L[j] == 0) for L in Ls]   # literals whose value is 0
    incl = [0] * R                                                     # bit j = state >= 6 (literal included)
    def recompute(r):
        incl[r] = sum(1 << j for j in range(N2) if st[r][j] >= 6)
    own = {0: [r for r in range(R) if target[r] == 0], 1: [r for r in range(R) if target[r] == 1]}
    def test():
        out = []
        for s in range(n_train, len(S)):
            ev = [1 if incl[r] & zmask[s] == 0 else 0 for r in range(R)]
            v0 = sum(ev[r] for r in own[0]); v1 = sum(ev[r] for r in own[1])
            out.append((tuple(ev), 0 if v0 > v1 else 1))
        return out
    snaps = {}
    for e in range(epochs):
        for s in range(n_train):
            L, zm, y = Ls[s], zmask[s], C[s]
            for k in range(R):
                fire = sum(1 for r in own[y] if incl[r] & zm == 0)
                miss = len(own[y]) - fire
                vc = max(-T, min(T, fire - miss))
                p = ((T - vc) * 65535) // (2 * T)
                p_rule = p if target[k] == y else 32767
                u = top; top = NEXT[top]
                if u > p_rule:
                    continue
                evk = incl[k] & zm == 0
                sk = st[k]
                if target[k] == y:
                    a = lfsr[k]
                    if evk:                                     # UPDATE
                        for j in range(N2):
                            u2 = a; a = NEXT[a]
                            if L[j]:
                                if u2 <= MEM_PROB and sk[j] < 10: sk[j] += 1
                            elif u2 <= FORGET_PROB and sk[j] > 1: sk[j] -= 1
                    else:                                       # ERASE
                        for j in range(N2):
                            u2 = a; a = NEXT[a]
                            if u2 <= FORGET_PROB and sk[j] > 1: sk[j] -= 1
                    lfsr[k] = a
                elif evk:                                       # REJECT
                    for j in range(N2):
                        if L[j] == 0 and sk[j] <= 5: sk[j] += 1
                else:
                    continue
                recompute(k)
        if e + 1 in checkpoints:
            snaps[e + 1] = test()
    return test(), snaps

def accuracy(res, C, n_train):
    return sum(pred == C[n_train + i] for i, (_, pred) in enumerate(res)) / len(res)
