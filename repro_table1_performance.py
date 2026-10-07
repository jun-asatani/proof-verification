"""
Reproduces Table 1 in the paper (Section 5): mean number of successful
writes over 10^4 independent trials per condition, k=4 (n=16, m=4),
proposed scheme (with E2c) vs. CIL-ILIFC, at q in {4, 6, 8}, with
Welch's two-sample t-statistic (unequal variance).

Uses core_encoder.py's FlashSim (a direct port of the original pLay.c
implementation, verified to reproduce the conference version's reported
means to within 0.2%; see the smoke test in core_encoder.py's own
__main__) for the proposed scheme, and cil_ilifc_baseline.py's CILSim
(the same implementation with the multi-index phases disabled) for
CIL-ILIFC.

Appendix A.5 records seed 42 for the proposed scheme and seed 142 for
CIL-ILIFC as the primary results, with an independent check at seeds
9001/9002.
"""
import statistics
from core_encoder import simulate
from cil_ilifc_baseline import simulate_cil


def welch_t(a, b):
    n1, n2 = len(a), len(b)
    m1, m2 = statistics.mean(a), statistics.mean(b)
    v1, v2 = statistics.variance(a), statistics.variance(b)
    se = (v1 / n1 + v2 / n2) ** 0.5
    return (m1 - m2) / se


def run(seed_proposed=42, seed_cil=142, n_sim=10000):
    print(f"{'q':>3} {'proposed (E2c)':>18} {'CIL-ILIFC':>14} {'%improvement':>14} {'t':>8}")
    for q in [4, 6, 8]:
        proposed = simulate(n=16, k=4, q=q, num_sim=n_sim, seed=seed_proposed)
        cil = simulate_cil(n=16, k=4, q=q, num_sim=n_sim, seed=seed_cil)
        m_p, sd_p = statistics.mean(proposed), statistics.stdev(proposed)
        m_c, sd_c = statistics.mean(cil), statistics.stdev(cil)
        pct = 100 * (m_p - m_c) / m_c
        t = welch_t(proposed, cil)
        print(f"{q:>3} {m_p:>10.2f} ({sd_p:>4.2f}) {m_c:>7.2f} ({sd_c:>4.2f}) "
              f"{pct:>13.1f}% {t:>8.1f}")


if __name__ == "__main__":
    print(f"=== Table 1: N=10000 trials/condition, seeds 42 (proposed) / 142 (CIL-ILIFC) ===")
    run(seed_proposed=42, seed_cil=142, n_sim=10000)
    print()
    print(f"=== Independent-seed check: seeds 9001 (proposed) / 9002 (CIL-ILIFC) ===")
    run(seed_proposed=9001, seed_cil=9002, n_sim=10000)
