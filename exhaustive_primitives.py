"""
Shared primitives for the exhaustive decoding-uniqueness verification
(Appendix A of the paper): the state predicates and the decoding map D2,
parametrized by (k, q, l) so the same functions serve both the k=4 case
(Theorem 1) and the k>4 generalizations (Proposition 1).

read_index_c implements the manuscript's explicit first-occurrence
tie-breaking rule (Section 3.2): a single deterministic index, never a
set of tied candidates -- this matches both the encoder's own
phase-selection logic and the decoder.

read_alone(x, k, l, design) implements the multi-index condition of
Section 6 under either of its two designs:
  "pair" (default): True as soon as ANY two distinct sections are both
      active and hold identical cell-value patterns (not requiring every
      section in the sub-block to match);
  "all": True only if EVERY section is active and all sections hold the
      identical cell-value pattern.
At p=2 (k=2l, e.g. k=4) the two designs coincide.

These functions are pure and stateless; they are imported by
exhaustive_verify.py, which supplies the encoding step (apply_op) and
the BFS driver.
"""


def active(x, k, q):
    total = sum(x)
    flag_clear = len(set(x)) != 1
    if total == k * (q - 1) or not flag_clear:
        return False
    return True


def clear(x, k, q):
    if len(set(x)) != 1:
        return False
    if sum(x) == k * (q - 1):
        return False
    return True


def read_layer(x):
    return max(x)


def read_index_c(x, k, q):
    """EXACT C semantics: single value, first-occurrence strict tie-break.
    Returns 0 if clear/full (matches C's 'index=0' sentinel)."""
    if not active(x, k, q):
        return 0
    max_diff = x[0] - x[k - 1]
    index = 1
    for n in range(2, k + 1):
        diff = x[n - 1] - x[n - 2]
        if max_diff < diff:
            max_diff = diff
            index = n
    return index


def read_index_all_ties(x, k, q):
    """Diagnostic: ALL positions attaining the maximal cyclic difference
    (used only to characterize when the tie-break rule is exercised;
    see Appendix A.4)."""
    if not active(x, k, q):
        return []
    diffs = [x[n - 1] - x[(n - 2) % k] for n in range(1, k + 1)]
    m = max(diffs)
    return [n + 1 for n in range(k) if diffs[n] == m]


def parity(x):
    return sum(x) % 2


def read_alone(x, k, l, design="pair"):
    p = k // l
    secs = [tuple(x[t * l:(t + 1) * l]) for t in range(p)]
    actives = [len(set(s)) != 1 for s in secs]
    if design == "all":
        return all(actives) and len(set(secs)) == 1
    if design != "pair":
        raise ValueError("design must be 'pair' or 'all'")
    for t in range(p):
        for t2 in range(t + 1, p):
            if actives[t] and actives[t2] and secs[t] == secs[t2]:
                return True
    return False


def read_maxi(x, k):
    """Position of the first-occurrence maximal cell, shifted by 2
    (Eq. for read_maxi in Section 3.2)."""
    m = max(x)
    i_max = x.index(m) + 1  # first occurrence, matches C
    return ((i_max - 1 + 2) % k) + 1


def read_maxnum(x):
    m = max(x)
    return sum(1 for v in x if v == m) == 1


def decode(x, k, q, l, design="pair"):
    """D2 (Section 3.3): section-wise decode if x is in the multi-index
    state (read_alone), else whole-block read_index/parity decode."""
    claims = {}
    if read_alone(x, k, l, design):
        p = k // l
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
            global_pos = t * l + local_index + 1
            bit = sum(sec) % 2
            claims[global_pos] = bit
    else:
        ri = read_index_c(x, k, q)
        if ri != 0:
            claims[ri] = parity(x)
    return claims
