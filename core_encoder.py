"""
Faithful Python port of p-Lay.c (the original C simulation for the ISITA2014
paper "An Improvement of Performance to Layered Index-less Indexed Flash
Codes"). This is a 1:1 translation preserving the exact logic, including the
k=4-specific hard-coded sections (read_alone / write_alone / read_maxi),
so we can first validate against the paper's reported numbers before
generalizing to arbitrary k.

Mersenne Twister (mt.h) is replaced with Python's random.Random, which is
also MT19937-based, but the exact stream will differ from the C version.
This means per-run reproducibility against the C binary's exact trace is
not expected -- but the *statistical averages* over many trials should
match closely, which is what the paper reports (Figs. 5-7 show averages
over 10^4 erasures).

Arrays are 1-indexed in the original C code (x[j][i] for j=1..m, i=1..k).
We preserve 1-indexing throughout via (m+1) x (k+1) arrays to minimize
translation errors.
"""

import random


class FlashSim:
    def __init__(self, m, k, q, seed=0):
        self.m = m
        self.k = k
        self.q = q
        self.rng = random.Random(seed)
        # 1-indexed: x[j][i], j=1..m, i=1..k
        self.x = [[0] * (k + 1) for _ in range(m + 1)]

    # ---- direct translations of the C helper functions ----

    def active(self, j):
        """1 if active (not full, not clear), 0 otherwise."""
        k, q, x = self.k, self.q, self.x
        total_charge = sum(x[j][i] for i in range(1, k + 1))
        flag_clear = 0
        for n in range(1, k):
            if x[j][n] != x[j][n + 1]:
                flag_clear = 1
        if total_charge == k * (q - 1) or flag_clear == 0:
            return 0
        return 1

    def read_index(self, j):
        """Recover index via max adjacent-difference (circular), C-faithful."""
        k, q, x = self.k, self.q, self.x
        flag_clear = 0
        for n in range(1, k):
            if x[j][n] != x[j][n + 1]:
                flag_clear = 1
        total_charge = sum(x[j][i] for i in range(1, k + 1))
        if total_charge == k * (q - 1) or flag_clear == 0:
            return 0
        max_diff = x[j][1] - x[j][k]
        index = 1
        for n in range(2, k + 1):
            diff = x[j][n] - x[j][n - 1]
            if max_diff < diff:
                max_diff = diff
                index = n
        return index

    def write(self, j, i):
        """write(): index i, sub-block j -- C: write_num = (i+y)%k, 0->k."""
        k, x = self.k, self.x
        y = sum(x[j][n] for n in range(1, k + 1))
        write_num = (i + y) % k
        if write_num == 0:
            write_num = k
        x[j][write_num] += 1

    def write_new(self, j, i):
        self.x[j][i] += 1

    def clear(self, j):
        k, q, x = self.k, self.q, self.x
        a = 1
        for n in range(1, k):
            if x[j][n] != x[j][n + 1]:
                a = 0
        s = sum(x[j][n] for n in range(1, k + 1))
        if s == k * (q - 1):
            a = 0
        return a

    def read_layer(self, j):
        k, x = self.k, self.x
        return max(x[j][n] for n in range(1, k + 1))

    def read_max(self, j):
        k, x = self.k, self.x
        return max(x[j][n] for n in range(1, k + 1))

    def read_maxi(self, j):
        """Position of the max-valued cell, then mapped via the k=4-specific
        table {1->3, 2->4, 3->1, 4->2} (i.e. +2 mod 4, 1-indexed)."""
        k, x = self.k, self.x
        max_val = self.read_max(j)
        i_max = 0
        for n in range(1, k + 1):
            if x[j][n] == max_val:
                i_max = n
                break
        # C hard-codes this map for k=4 specifically: s = ((i_max - 1 + 2) % 4) + 1
        if k == 4:
            table = {1: 3, 2: 4, 3: 1, 4: 2}
            return table[i_max]
        else:
            # generalization consistent with the same "+2 mod k" pattern
            return ((i_max - 1 + 2) % k) + 1

    def read_maxnum(self, j):
        """1 if exactly one cell attains the max (no tie), else 0."""
        k, x = self.k, self.x
        max_val = self.read_max(j)
        a = sum(1 for n in range(1, k + 1) if x[j][n] == max_val)
        if a > 1:
            a = 0
        else:
            a = 1 if a == 1 else 0
        # NOTE: replicate exact C semantics below instead (see call site)
        return a

    def write_max(self, j, i):
        self.x[j][i] += 1

    def read_alone(self, j):
        """k=4-specific: detects the 'two paired sections' multi-index state."""
        k, x = self.k, self.x
        if k != 4:
            raise NotImplementedError("read_alone is k=4-specific in original C")
        a = 0
        if x[j][1] != x[j][2] and x[j][3] != x[j][4]:
            if x[j][1] == x[j][3] and x[j][2] == x[j][4]:
                a = 1
        return a

    def write_alone(self, j, i):
        k, x = self.k, self.x
        if k != 4:
            raise NotImplementedError("write_alone is k=4-specific in original C")
        if i == 1:
            x[j][4] += 1
        if i == 2:
            x[j][1] += 1
        if i == 3:
            x[j][2] += 1
        if i == 4:
            x[j][3] += 1

    def parity(self, j):
        k, x = self.k, self.x
        return sum(x[j][n] for n in range(1, k + 1)) % 2

    def write_change(self, j, i):
        self.x[j][i] += 1

    # ---- main simulation loop, faithful port of sim() ----

    def run_once(self):
        m, k, q = self.m, self.k, self.q
        # reset cells
        self.x = [[0] * (k + 1) for _ in range(m + 1)]
        write_num = 0

        while True:
            a = 0
            i = int(k * self.rng.random()) + 1
            if i > k:
                i = k  # guard against the rare genrand_real2()==1.0 edge case

            # Phase 0: multi-index "alone" write
            for j in range(1, m + 1):
                if self.read_alone(j) and (self.read_maxi(j) % 2) == (i % 2):
                    self.write_alone(j, i)
                    write_num += 1
                    a = 1
                    break
            if a == 1:
                continue

            # Phase 1: single active index match
            for j in range(1, m + 1):
                if self.active(j) and self.read_index(j) == i and self.read_alone(j) == 0:
                    self.write(j, i)
                    write_num += 1
                    a = 1
                    break
            if a == 1:
                continue

            # Phase 2: change_index (CIL-ILIFC flexibility)
            for j in range(1, m + 1):
                if (self.read_index(j) == ((i % k) + 1) and self.parity(j) == 0
                        and self.read_alone(j) == 0):
                    self.write_change(j, i)
                    write_num += 1
                    a = 1
                    break
            if a == 1:
                continue

            # Phase 3: write_max (tie-breaking / multi-index continuation)
            for j in range(1, m + 1):
                if self.read_maxnum(j) and self.read_maxi(j) == i:
                    self.write_max(j, i)
                    write_num += 1
                    a = 1
                    break
            if a == 1:
                continue

            # Phase 4: write_new into a clear sub-block, lowest layer first
            for l in range(0, q):
                found = False
                for j in range(1, m + 1):
                    if self.clear(j) and self.read_layer(j) == l:
                        self.write_new(j, i)
                        write_num += 1
                        a = 1
                        found = True
                        break
                if found:
                    break
            if a == 1:
                continue

            break  # erasure

        return write_num


def simulate(n, k, q, num_sim, seed=1):
    m = n // k
    sim = FlashSim(m, k, q, seed=seed)
    counts = []
    for _ in range(num_sim):
        counts.append(sim.run_once())
    return counts


if __name__ == "__main__":
    import statistics

    paper_proposed = {4: 44.195, 6: 76.015, 8: 107.982}
    paper_cil = {4: 41.554, 6: 72.637, 8: 104.177}

    print("Reproducing paper Figs. 5-7 (n=16, k=4, m=4), proposed method E2:")
    for q in [4, 6, 8]:
        counts = simulate(n=16, k=4, q=q, num_sim=10000, seed=1)
        mean = statistics.mean(counts)
        print(f"  q={q}: mean={mean:.3f}   paper(proposed)={paper_proposed[q]}   "
              f"diff={mean - paper_proposed[q]:+.3f}")
