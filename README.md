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
| `cil_ilifc_baseline.py` | CIL-ILIFC, obtained from `core_encoder.py` by disabling the multi-index phases. Used as the baseline in Table 1. |
| `repro_table1_performance.py` | **Table 1** (Section 5): mean writes, proposed scheme vs. CIL-ILIFC, `k=4`, `q ∈ {4,6,8}`, `N=10^4` trials/condition, Welch's t-statistic. Also runs the independent-seed check described in Appendix A.5. (~2 min) |
| `exhaustive_primitives.py` | Shared state predicates and the decoding map `D2` (Section 3.2–3.3), parametrized by `(k, q, l)`. Imported by `exhaustive_verify.py`; not run standalone. |
| `exhaustive_verify.py` | **Algorithm 1** (Appendix A.2): exhaustive breadth-first-search verification. Running it standalone reproduces both **Table 2** (Lemma 1: `k=4` is decoding-unique for every tested `q`) and the exhaustive rows of **Table 4** / Appendix Table A·1 (Proposition 1: every tested `k>4` configuration fails in the large majority of reachable states). (~2 min) |
| `repro_appendix_tiebreak.py` | **Appendix A.4**: characterizes how often the `read_index` and `read_maxi` tie-breaking rules are actually exercised across the `k=4` reachable state space, and verifies the parity-invariance argument. (~10 s) |
| `repro_table_genfail_mc.py` | **Table 3** (Section 7.2): Monte Carlo decode-mismatch rate, 200 trials/condition, for every `(k,l,p)` generalization tested. (~1 min) |
| `cross_check_encoder.py` | The hand-traced example from Section 4.2 (i = [1,1,4] on a single `k=4` sub-block), run against the real encoder to confirm the phase-by-phase state transitions cited in the text. |
| `roundtrip_verify_k4.py` | The round-trip Monte Carlo checker described in Section 4.1 (`k=4`, 200 trials, decode-after-every-write comparison against the true information vector). |

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

- Table 1: seeds 42 (proposed scheme) and 142 (CIL-ILIFC); independent
  check at seeds 9001/9002.
- Table 3: seeds 0–199 (one per trial).
- Table 2 and Table 4's exhaustive rows, and Appendix A.4: deterministic
  given `(k, l, q)`; no seed involved.

## A note on the numbers in Appendix A.4

While assembling this repository we re-ran the tie-breaking
characterization end to end and found that the manuscript's working
draft had understated the single-index state count (it read 540 states
out of 700 total; the correct figures, consistent with the same
per-`q` counting convention used for Table 2, are 960 out of 1120). The
qualitative claims — `read_index` is never tied, `read_maxi` is always
tied but the choice is parity-invariant — are unaffected and were
independently reconfirmed by `repro_appendix_tiebreak.py`; only the
raw counts were corrected, before submission, once this discrepancy was
caught by rebuilding this reproduction package.
