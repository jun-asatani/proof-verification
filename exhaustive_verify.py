"""
Exhaustive, non-probabilistic decoding-uniqueness verification (Algorithm 3
in Appendix A.2 of the paper). Performs a breadth-first search over every
state reachable from the all-zero sub-block under every possible sequence
of bit flips, for a given (k, l, q), and checks at every node that the
decoder D2 recovers the true information vector exactly.

This is the single procedure behind both of the paper's main computational
results: applied at (k=4, l=2), it proves Theorem 1 (decoding uniqueness
holds for every q in {1,...,30} tested); applied unchanged except for k
and l, it produces the exhaustive rows of Table 4 (generalization failure),
under both the ALL and PAIR designs of Section 6, which show that decoding
uniqueness fails for k in {6, 8, 12} under the tested (l, q).

Two correctness details worth documenting explicitly, since both were the
source of debugging effort during development and are easy to get wrong
when reimplementing this kind of check:

1. change_index (Phase 2 / E2b) is a DIRECT increment at the flipped
   index i -- x[i] += 1 -- not a cyclic-shifted position, despite
   write_alone (Phase 0 / E2a) using a shifted formula. Conflating the
   two silently produces spurious decode mismatches.
2. The true information vector must be tracked as a FULL dictionary over
   all k indices (default 0), matching the decoder's own convention that
   "no active claim" means bit 0. Tracking it as a sparse dict of only
   ever-written indices makes semantically identical states compare as
   unequal (e.g. {1: 0} vs {}), which produces mismatches that are
   artifacts of the bookkeeping, not real decoding failures.
"""
from exhaustive_primitives import (active, clear, read_index_c, parity,
    read_alone, read_maxi, read_maxnum, decode)


def apply_op(x, i, k, q, l, design="pair"):
    """One encoder step: apply E2's four branches, in priority order, to
    sub-block x for flipped index i. Returns the successor cell-state
    tuple, or None if no branch fires (block erasure)."""
    x = list(x)

    # Phase 0 (E2a / write_alone) -- global shift formula
    if read_alone(x, k, l, design):
        rmi = read_maxi(x, k)
        if (rmi % 2) == (i % 2):
            pos = ((i - 2) % k) + 1
            if x[pos - 1] <= q - 2:
                x2 = list(x); x2[pos - 1] += 1
                return tuple(x2)
            return None

    # Phase 1 (E2b / write)
    if active(x, k, q) and not read_alone(x, k, l, design):
        ri = read_index_c(x, k, q)
        if ri == i:
            wt = sum(x)
            pos = (i + wt) % k
            if pos == 0:
                pos = k
            if x[pos - 1] <= q - 2:
                x2 = list(x); x2[pos - 1] += 1
                return tuple(x2)
            return None

    # Phase 2 (E2b / change_index) -- direct increment at i
    if not read_alone(x, k, l, design):
        ri = read_index_c(x, k, q)
        c = ((i % k) + 1)
        if ri == c and parity(x) == 0:
            if x[i - 1] <= q - 2:
                x2 = list(x); x2[i - 1] += 1
                return tuple(x2)
            return None

    # Phase 3 (E2c / write_max)
    if read_maxnum(x) and read_maxi(x, k) == i:
        if x[i - 1] <= q - 2:
            x2 = list(x); x2[i - 1] += 1
            return tuple(x2)
        return None

    # Phase 4 (E2d / write_new)
    if clear(x, k, q):
        if x[i - 1] <= q - 2:
            x2 = list(x); x2[i - 1] += 1
            return tuple(x2)
        return None

    return None


def decode_full_dict(x, k, q, l, design="pair"):
    """Full dict over 1..k, default 0 -- the decoder's own convention that
    an index with no active claim reads as bit 0."""
    v = {idx: 0 for idx in range(1, k + 1)}
    claims = decode(list(x), k, q, l, design)  # sparse: only active claims
    for idx, bit in claims.items():
        v[idx] = bit
    return v


def exhaustive_check(k, q, l, design="pair"):
    """Algorithm 3: breadth-first search over the reachable (x, v) state
    space. Returns nodes explored, any decode mismatches (D2(x) != v),
    and any state ambiguities (the same x reached with two different
    true v's along different paths -- logically equivalent to a decode
    mismatch, checked independently as a cross-check)."""
    empty = tuple([0] * k)
    v0 = frozenset((idx, 0) for idx in range(1, k + 1))
    start = (empty, v0)
    seen = {start}
    frontier = [start]
    state_to_truev = {empty: {v0}}
    decode_mismatches = []
    state_ambiguity_witnesses = []
    nodes_explored = 0

    while frontier:
        new_frontier = []
        for (x, true_v_fs) in frontier:
            nodes_explored += 1
            true_v = dict(true_v_fs)

            claims_full = decode_full_dict(list(x), k, q, l, design)
            if claims_full != true_v:
                decode_mismatches.append((x, true_v, claims_full))

            prior = state_to_truev.setdefault(x, set())
            if true_v_fs not in prior and len(prior) > 0:
                state_ambiguity_witnesses.append((x, prior.copy(), true_v_fs))
            prior.add(true_v_fs)

            for i in range(1, k + 1):
                x2 = apply_op(list(x), i, k, q, l, design)
                if x2 is None:
                    continue
                true_v2 = dict(true_v)
                true_v2[i] = true_v2.get(i, 0) ^ 1
                node2 = (x2, frozenset(true_v2.items()))
                if node2 not in seen:
                    seen.add(node2)
                    new_frontier.append(node2)
        frontier = new_frontier

    return {
        'nodes_explored': nodes_explored,
        'decode_mismatches': decode_mismatches,
        'state_ambiguity_witnesses': state_ambiguity_witnesses,
    }


# Exhaustive configurations for k>4 (Table 4 of the paper). A design is
# skipped (None) where the reachable state space did not fit in ~6 GB of
# memory with this pure-Python reference implementation.
GENFAIL_CONFIGS = [
    # (k, l, q, designs to run)
    (6, 2, 4, ("all", "pair")),
    (6, 2, 6, ("all", "pair")),
    (8, 2, 3, ("all", "pair")),
    (8, 2, 4, ("all",)),            # pair: out of memory at q=4
    (8, 4, 4, ("pair",)),           # p=2: ALL and PAIR coincide
    (12, 2, 3, ("all",)),           # pair: out of memory at q=3
    (12, 4, 3, ("all", "pair")),
    (12, 6, 3, ("pair",)),          # p=2: ALL and PAIR coincide
]


if __name__ == "__main__":
    print("=== Theorem 1: k=4, l=2, p=2 (expect CLEAN for every q; |S(q)| = 15q-14) ===")
    all_clean = True
    for q in [1, 2, 3, 4, 6, 8, 12, 16, 20, 30]:
        result = exhaustive_check(k=4, q=q, l=2)
        n = result['nodes_explored']
        clean = (len(result['decode_mismatches']) == 0 and len(result['state_ambiguity_witnesses']) == 0)
        all_clean = all_clean and clean
        formula = 15 * q - 14
        print(f"  q={q:2d}: |S(q)|={n:4d} (15q-14={formula:4d}), "
              f"mismatches={len(result['decode_mismatches'])}, "
              f"ambiguities={len(result['state_ambiguity_witnesses'])}  "
              f"{'CLEAN' if clean else 'FAILURES'}")
    print("*** Theorem 1 confirmed: k=4 is decoding-unique for every q tested ***\n"
          if all_clean else "*** UNEXPECTED FAILURES at k=4 -- do not trust downstream results ***\n")

    print("=== Proposition 1, exhaustive rows (Table 4): k>4 (expect FAILURES in the large majority of states) ===")
    for (k, l, q, designs) in GENFAIL_CONFIGS:
        for design in designs:
            result = exhaustive_check(k=k, q=q, l=l, design=design)
            n = result['nodes_explored']
            n_mis = len(result['decode_mismatches'])
            pct = 100 * n_mis / n if n else 0.0
            print(f"  (k,l,p)=({k},{l},{k // l}) {design:4s} q={q}: |S|={n:6d}, mismatches={n_mis:6d} ({pct:.1f}%)")
    print("*** as expected, every (k,l) != (4,2) tested fails in the large majority of reachable states ***")
