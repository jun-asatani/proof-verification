"""
Reproduces the Monte Carlo generalization-failure table (Table 3 in the
paper, \\label{tab:genfail-mc}): decode-mismatch rate over 200 independent
trials per (k, l, design, q) condition, up to 2000 writes per trial,
uniform random bit flips -- the same protocol as the k=4 performance
comparison (Section 5). Appendix A.5 records seeds 0-199 for these
results.

Each trial simulates m = k sub-blocks (matching the memory-wide protocol
of Section 5, not a single isolated sub-block), applying the encoding
map's four branches in priority order at each step -- Phase 0
(write_alone, gated by read_alone), Phase 1 (write / change_index),
Phase 2 (write_max), Phase 3 (write_new) -- exactly as in
exhaustive_verify.apply_op, but searching across all m sub-blocks for
the first one where a given phase fires, before moving to the next
phase. This mirrors the real memory-wide simulator's structure
(core_encoder.py's FlashSim.run_once, generalized_sectioned to
arbitrary k) rather than reinventing it.

The two designs of Section 6 differ only in how read_alone is evaluated:
PAIR (used by exhaustive_verify.py's primitives) treats a sub-block as
multi-index as soon as ANY pair of its sections match; ALL requires
EVERY section to match. Both use the identical, corrected GLOBAL
write_alone formula ((i-2) mod k)+1 -- Section 6 emphasizes that this
global (not section-local) formula is itself a source of the
generalization's failure for p >= 3.
"""
import random
from exhaustive_primitives import (active, clear, read_layer, read_index_c,
    parity, read_maxi, read_maxnum, decode)

CONDITIONS = [
    # (k, l, p)
    (6, 2, 3),
    (8, 2, 4),
    (8, 4, 2),
    (12, 2, 6),
    (12, 4, 3),
    (12, 6, 2),
]
DESIGNS = ["all", "pair"]


def read_alone(x, k, l, design):
    p = k // l
    secs = [tuple(x[t * l:(t + 1) * l]) for t in range(p)]
    actives = [len(set(s)) != 1 for s in secs]
    if design == "all":
        return all(actives) and len(set(secs)) == 1
    # pair (any two sections, not only adjacent -- Section 6's corrected test)
    for t in range(p):
        for t2 in range(t + 1, p):
            if actives[t] and actives[t2] and secs[t] == secs[t2]:
                return True
    return False


def decode_block(x, k, q, l, design):
    if read_alone(x, k, l, design):
        p = k // l
        claims = {}
        for t in range(p):
            sec = x[t * l:(t + 1) * l]
            if len(set(sec)) == 1:
                continue
            max_diff = sec[0] - sec[l - 1]
            local_index = 0
            for n in range(1, l):
                diff = sec[n] - sec[n - 1]
                if max_diff < diff:
                    max_diff = diff
                    local_index = n
            claims[t * l + local_index + 1] = sum(sec) % 2
        return claims
    ri = read_index_c(x, k, q)
    if ri != 0:
        return {ri: parity(x)}
    return {}


def run_trial(k, l, design, q, m, seed, max_writes=2000):
    rng = random.Random(seed)
    blocks = [[0] * k for _ in range(m)]
    true_v = {idx: 0 for idx in range(1, k + 1)}
    mismatch = False

    for _ in range(max_writes):
        i = rng.randint(1, k)
        fired = False

        # Phase 0: write_alone (global shift formula, gated by read_alone)
        for x in blocks:
            if read_alone(x, k, l, design):
                rmi = read_maxi(x, k)
                if (rmi % 2) == (i % 2):
                    pos = ((i - 2) % k) + 1
                    if x[pos - 1] <= q - 2:
                        x[pos - 1] += 1
                        fired = True
                        break
        if fired:
            true_v[i] ^= 1
        else:
            # Phase 1: write (single active index match)
            for x in blocks:
                if active(x, k, q) and not read_alone(x, k, l, design):
                    ri = read_index_c(x, k, q)
                    if ri == i:
                        wt = sum(x)
                        pos = (i + wt) % k
                        if pos == 0:
                            pos = k
                        if x[pos - 1] <= q - 2:
                            x[pos - 1] += 1
                            fired = True
                            break
            if fired:
                true_v[i] ^= 1
            else:
                # Phase 1b: change_index (direct increment at i)
                for x in blocks:
                    if not read_alone(x, k, l, design):
                        ri = read_index_c(x, k, q)
                        c = ((i % k) + 1)
                        if ri == c and parity(x) == 0:
                            if x[i - 1] <= q - 2:
                                x[i - 1] += 1
                                fired = True
                                break
                if fired:
                    true_v[i] ^= 1
                else:
                    # Phase 2: write_max (E2c)
                    for x in blocks:
                        if read_maxnum(x) and read_maxi(x, k) == i:
                            if x[i - 1] <= q - 2:
                                x[i - 1] += 1
                                fired = True
                                break
                    if fired:
                        true_v[i] ^= 1
                    else:
                        # Phase 3: write_new into the lowest-layer clear block
                        for layer in range(q):
                            found = False
                            for x in blocks:
                                if clear(x, k, q) and read_layer(x) == layer:
                                    x[i - 1] += 1
                                    found = True
                                    break
                            if found:
                                fired = True
                                break
                        if fired:
                            true_v[i] ^= 1

        if not fired:
            break  # erasure

        v_hat = {idx: 0 for idx in range(1, k + 1)}
        for x in blocks:
            for idx, bit in decode_block(x, k, q, l, design).items():
                v_hat[idx] = bit
        if v_hat != true_v:
            mismatch = True

    return mismatch


if __name__ == "__main__":
    print(f"{'k':>3} {'l':>3} {'p':>3} {'design':>7} {'q=4':>8} {'q=8':>8}")
    for (k, l, p) in CONDITIONS:
        for design in DESIGNS:
            rates = []
            for q in [4, 8]:
                fails = sum(1 for t in range(200)
                            if run_trial(k, l, design, q, m=k, seed=t))
                rates.append(100 * fails / 200)
            print(f"{k:>3} {l:>3} {p:>3} {design:>7} {rates[0]:>7.1f}% {rates[1]:>7.1f}%")
