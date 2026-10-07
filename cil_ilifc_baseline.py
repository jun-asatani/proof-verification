"""
CIL-ILIFC (E1) only -- derived by disabling the multi-index phases
(Phase 0: write_alone, Phase 3: write_max) from the C-ported simulator.
This isolates exactly what CIL-ILIFC contributes, matching the paper's
"CIL-ILIFC" curve in Figs. 5-7.
"""
import statistics
from core_encoder import FlashSim


class CILSim(FlashSim):
    def run_once(self):
        m, k, q = self.m, self.k, self.q
        self.x = [[0] * (k + 1) for _ in range(m + 1)]
        write_num = 0

        while True:
            a = 0
            i = int(k * self.rng.random()) + 1
            if i > k:
                i = k

            # Phase 1: single active index match
            for j in range(1, m + 1):
                if self.active(j) and self.read_index(j) == i:
                    self.write(j, i)
                    write_num += 1
                    a = 1
                    break
            if a == 1:
                continue

            # Phase 2: change_index (this IS the CIL-ILIFC feature)
            for j in range(1, m + 1):
                if self.read_index(j) == ((i % k) + 1) and self.parity(j) == 0:
                    self.write_change(j, i)
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


def simulate_cil(n, k, q, num_sim, seed=1):
    m = n // k
    sim = CILSim(m, k, q, seed=seed)
    return [sim.run_once() for _ in range(num_sim)]


if __name__ == "__main__":
    paper_cil = {4: 41.554, 6: 72.637, 8: 104.177}
    print("Reproducing paper Figs. 5-7 (n=16, k=4, m=4), CIL-ILIFC:")
    for q in [4, 6, 8]:
        counts = simulate_cil(n=16, k=4, q=q, num_sim=10000, seed=1)
        mean = statistics.mean(counts)
        print(f"  q={q}: mean={mean:.3f}   paper(CIL-ILIFC)={paper_cil[q]}   "
              f"diff={mean - paper_cil[q]:+.3f}")
