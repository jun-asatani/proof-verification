# Code for "On the Decoding Uniqueness of a Multi-Index Extension of Layered Index-less Indexed Flash Codes"

This repository contains the implementation and verification code behind
the results in the paper (IEICE Transactions, manuscript 2026EAP1131,
revised submission). It is a curated subset of the project's working
code, limited to what the paper actually cites: everything here
reproduces a specific table, lemma, or appendix claim in the manuscript.
Exploratory and superseded scripts from the development process are not
included.

Requires Python 3.9+ and the standard library only (no third-party
dependencies).

## What reproduces what

| Script | Reproduces |
|---|---|
| `core_encoder.py` | The proposed scheme's encoder/decoder (`FlashSim`), a direct port of the original ISITA 2014 implementation (`pLay.c`). Running it standalone sanity-checks against the conference version's reported means at `k=4`. |
| `cil_ilifc_baseline.py` | CIL-ILIFC, obtained from `core_encoder.py` by disabling the multi-index phases. Used as the baseline in Table 2. |
| `repro_table1_performance.py` | **Table 2** (Section 5): mean writes, proposed scheme vs. CIL-ILIFC, `k=4`, `q ∈ {4,6,8}`, `N=10^4` trials/condition, Welch's t-statistic. Also runs the independent-seed check described in Appendix A.5. (~2 min) |
| `exhaustive_primitives.py` | Shared state predicates and the decoding map `D2` (Section 3.2–3.3), parametrized by `(k, q, l)`. Imported by `exhaustive_verify.py`; not run standalone. |
| `exhaustive_verify.py` | **Algorithm 3** (Appendix A.2): exhaustive breadth-first-search verification, parametrized by the multi-index design (`design="pair"` or `"all"`, Section 6). Running it standalone reproduces both **Table 1** (Theorem 1: `k=4` is decoding-unique for every tested `q`) and **Table 4** / Appendix Table A·1 (Proposition 1: every tested `k>4` configuration fails in the large majority of reachable states, under both designs wherever the reachable state space fits in memory). (~2 min, a few GB of RAM) |
| `repro_appendix_tiebreak.py` | **Appendix A.4**: characterizes how often the `read_index` and `read_maxi` tie-breaking rules are actually exercised across the `k=4` reachable state space, and verifies the parity-invariance argument. (~10 s) |
| `repro_table_genfail_mc.py` | **Table 3** (Section 7.2): Monte Carlo decode-mismatch rate, 200 trials/condition, for every `(k,l,p)` generalization tested. (~1 min) |
| `cross_check_encoder.py` | The hand-traced example from Section 4.2 (i = [1,1,4] on a single `k=4` sub-block), run against the real encoder to confirm the phase-by-phase state transitions cited in the text. |
| `roundtrip_verify_k4.py` | The round-trip Monte Carlo checker described in Section 4.1 (`k=4`, 200 trials, decode-after-every-write comparison against the true information vector). |
| `equivalence_check_k4.py` | **Section 8.5 (Limitations)**: at `k=4`, compares the exhaustive verifier's encoder (`exhaustive_verify.apply_op`) with `core_encoder.py` on all 2008 transitions (`q ∈ {2,3,4,5,6,8,12}`) and on 385,404 writes of simulated runs with `m=4` sub-blocks (`q ∈ {3,4,6,8}`); also confirms that the verifier's cell-full guard never triggers. (~1 min) |
| `c_check/run_c_check.sh` | **Sections 5.2-5.3 and 8.5**: builds the C program `c_check/ilifc_core.c` (same logic as the conference-version `ilifc.c`, December 2013) and (i) reproduces the averages printed in Figs. 5-7 of the conference paper (proposed 44.195 / 76.015 / 107.982; CIL-ILIFC 41.554 / 72.637 / 104.177, the latter equal to the program with E2c removed), (ii) runs the ablations without E2c, without E2a, and with E2c after E2d, and (iii) checks all 769,687 writes of the C program (`q ∈ {3,4,6,8}`, 3000 trials each) against `exhaustive_verify.apply_op`. Needs `gcc` and `python3`; `c_check/mt.h` is a reference MT19937 implementation. (~1 min) |

## Notes on the generalization to k>4

Section 6 of the paper defines the generalized construction by two
governing choices that are easy to get wrong when reimplementing it (the
paper discusses this explicitly, since an earlier stage of this project
implemented both incorrectly):

1. `write_alone` uses a **global** cyclic-shift formula over all `k`
   cells, not a formula restricted to the section containing the target
   index.
2. The PAIR multi-index design checks **every** pair of sections, not
   only adjacent ones.

`exhaustive_primitives.py`, `exhaustive_verify.py`, and
`repro_table_genfail_mc.py` all implement both of these correctly; they
are the versions used to produce every k>4 result reported in the paper.

## Reproducibility / seeds

- Table 2: seeds 42 (proposed scheme) and 142 (CIL-ILIFC); independent
  check at seeds 9001/9002.
- Table 3: seeds 0–199 (one per trial).
- Table 1 and Table 4 (exhaustive), and Appendix A.4: deterministic
  given `(k, l, q)`; no seed involved.

## A note on the numbers in Appendix A.4

While assembling this repository we re-ran the tie-breaking
characterization end to end and found that the manuscript's working
draft had understated the single-index state count (it read 540 states
out of 700 total; the correct figures, consistent with the same
per-`q` counting convention used for Table 1, are 960 out of 1120). The
qualitative claims — `read_index` is never tied, `read_maxi` is always
tied but the choice is parity-invariant — are unaffected and were
independently reconfirmed by `repro_appendix_tiebreak.py`; only the
raw counts were corrected, before submission, once this discrepancy was
caught by rebuilding this reproduction package.

## Changes in v1.1.0

- `exhaustive_primitives.py` / `exhaustive_verify.py` now take a
  `design` argument (`"pair"`, the default and the only behavior of
  v1.0.0, or `"all"`), and the standalone run reports the exhaustive
  rows of Table 4 under both designs. The `"pair"` results are
  identical to v1.0.0. Two combinations (`PAIR` at `(k,l,q)=(8,2,4,4)` and
  `(12,2,6,3)`) exceed ~6 GB of RAM in this pure-Python
  implementation and are not enumerated.
- Table/theorem numbering in the documentation now matches the revised
  manuscript (Theorem 1; Tables 1-4; Algorithm 3).

## Changes in v1.1.1

- Added `equivalence_check_k4.py` and the `c_check/` directory (C program,
  ablation variants, and the comparison against the exhaustive verifier),
  which back the new Limitations subsection (Section 8.5) and the ablation
  statements in Section 5.3 of the revised manuscript.
- README: corrected the identification of the two PAIR runs that exceed
  the memory limit (`(8,2,4,4)` and `(12,2,6,3)`).
- No change to any previously released script or result.
