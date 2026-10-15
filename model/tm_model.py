"""Bit-exact model of the hardware: same decisions, same LFSRs, same order of random-number consumption.

For each training sample:
  1. Every rule is evaluated with the current states.
  2. p is computed once from the rules of the sample's class: v = (rules that output 1) - (rules that output 0),
     clamped to [-T, T], p = (T - v) * 65535 / (2T).
  3. All rules decide in parallel, each one with its own LFSR. In SELECT_NEXT_OP a rule takes one random
     number u; it uses p if it belongs to the sample's class and 0.5 (32767) otherwise. If u <= p_rule:
       - rule of the sample's class that outputs 1 -> UPDATE (one random number per automaton)
       - rule of the sample's class that outputs 0 -> ERASE  (one random number per automaton)
       - rule of the other class that outputs 1    -> REJECT (no random numbers)"""

MEM_PROB, FORGET_PROB = 45875, 19661           # integer(0.7*65535), integer(0.3*65535) as rounded by GHDL


def lfsr_next(s):
    """16 steps of the Fibonacci LFSR x^16 + x^14 + x^13 + x^11 + 1, as in rtl/lfsr16.vhd."""
    for _ in range(16):
        fb = (s ^ (s >> 2) ^ (s >> 3) ^ (s >> 5)) & 1
        s = (s >> 1) | (fb << 15)
    return s


_NEXT = None


class LFSR:
    def __init__(self, seed):
        global _NEXT
        if _NEXT is None:                      # table of the 16-step jump (only to speed things up)
            _NEXT = [lfsr_next(s) for s in range(65536)]
        self.s = seed

    def take(self):                            # use the current value and advance (en = '1')
        v = self.s
        self.s = _NEXT[v]
        return v


def literals(x):                               # index 2i -> x_i, 2i+1 -> not x_i
    L = []
    for b in x:
        L += [b, 1 - b]
    return L


def train(S, C, n_train, target, seeds, T=2, epochs=50):
    """Trains on samples 0..n_train-1 and returns, for each test sample, (rule outputs, predicted class)."""
    R = len(target)
    N2 = 2 * len(S[0])
    st = [[5] * N2 for _ in range(R)]
    lfsr = [LFSR(sd) for sd in seeds]
    Ls = [literals(x) for x in S]

    def evaluate(r, L):
        for j in range(N2):
            if st[r][j] >= 6 and L[j] == 0:
                return 0
        return 1

    for _ in range(epochs):
        for s in range(n_train):
            L, y = Ls[s], C[s]
            ev = [evaluate(r, L) for r in range(R)]
            fire = sum(ev[r] for r in range(R) if target[r] == y)
            miss = sum(1 - ev[r] for r in range(R) if target[r] == y)
            vc = max(-T, min(T, fire - miss))
            p = ((T - vc) * 65535) // (2 * T)
            for k in range(R):
                u = lfsr[k].take()                              # SELECT_NEXT_OP
                p_rule = p if target[k] == y else 32767
                if u > p_rule:
                    continue
                sk = st[k]
                if target[k] == y:
                    if ev[k]:                                   # UPDATE
                        for j in range(N2):
                            u2 = lfsr[k].take()
                            if L[j]:
                                if u2 <= MEM_PROB and sk[j] < 10:
                                    sk[j] += 1
                            elif u2 <= FORGET_PROB and sk[j] > 1:
                                sk[j] -= 1
                    else:                                       # ERASE
                        for j in range(N2):
                            if lfsr[k].take() <= FORGET_PROB and sk[j] > 1:
                                sk[j] -= 1
                elif ev[k]:                                     # REJECT
                    for j in range(N2):
                        if L[j] == 0 and sk[j] <= 5:
                            sk[j] += 1

    out = []
    for s in range(n_train, len(S)):
        ev = [evaluate(r, Ls[s]) for r in range(R)]
        v0 = sum(ev[r] for r in range(R) if target[r] == 0)
        v1 = sum(ev[r] for r in range(R) if target[r] == 1)
        out.append((tuple(ev), 0 if v0 > v1 else 1))
    return out
