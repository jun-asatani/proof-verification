"""
Reproduces Appendix A.4's tie-breaking characterization: over every state
reachable at k=4 (Table 2's q values), how often is each tie-breaking
rule of Section 3.2 actually exercised?

- read_index (single-index regime): checked on every active,
  non-multi-index state. The paper reports this is NEVER tied across
  540 such states (q in {3,4,5,6,8,12,20,30}).
- read_maxi's underlying max-cell search (multi-index regime): checked
  on every multi-index state. The paper reports this is ALWAYS tied
  (160 states), always between exactly two positions exactly k/2 apart,
  and that read_maxi(x) mod 2 -- the only property E2a's firing
  condition actually consumes -- is invariant to which tied position is
  chosen (parity invariance).

This reuses exhaustive_verify.exhaustive_check to enumerate the
reachable state space (so it is guaranteed to walk exactly the same
states as Table 2), then re-examines each visited state's cyclic-
difference vector for ties using exhaustive_primitives.read_index_all_ties.
"""
from exhaustive_verify import exhaustive_check
from exhaustive_primitives import read_index_all_ties, read_alone, active

K, L = 4, 2
Q_VALUES = [3, 4, 5, 6, 8, 12, 20, 30]


def reachable_states(k, q, l):
    """Re-run the same BFS as exhaustive_check, but return the set of
    distinct cell-state vectors x visited (ignoring the true-v label)."""
    result = exhaustive_check(k, q, l)
    # exhaustive_check doesn't return the visited x's directly, so we
    # recover them by re-deriving from the same reachability relation.
    from exhaustive_verify import apply_op
    seen_x = {tuple([0] * k)}
    frontier = [tuple([0] * k)]
    while frontier:
        new_frontier = []
        for x in frontier:
            for i in range(1, k + 1):
                x2 = apply_op(x, i, k, q, l)
                if x2 is not None and x2 not in seen_x:
                    seen_x.add(x2)
                    new_frontier.append(x2)
        frontier = new_frontier
    assert len(seen_x) == result['nodes_explored'], \
        "state count mismatch vs exhaustive_check -- reachability logic diverged"
    return seen_x


def main():
    total_single_index_states = 0
    single_index_ties = 0
    total_multi_index_states = 0
    multi_index_ties = 0
    parity_violations = 0

    for q in Q_VALUES:
        states = reachable_states(K, q, L)
        for x in states:
            x = list(x)
            if read_alone(x, K, L):
                total_multi_index_states += 1
                m = max(x)
                tied_positions = [n + 1 for n in range(K) if x[n] == m]
                if len(tied_positions) > 1:
                    multi_index_ties += 1
                    assert len(tied_positions) == 2, "expected exactly 2 tied positions"
                    p1, p2 = tied_positions
                    assert abs(p1 - p2) == K // 2, "tied positions should be k/2 apart"
                    # parity invariance check: read_maxi mod 2 same for
                    # either choice of tied position
                    rmi_1 = ((p1 - 1 + 2) % K) + 1
                    rmi_2 = ((p2 - 1 + 2) % K) + 1
                    if (rmi_1 % 2) != (rmi_2 % 2):
                        parity_violations += 1
            elif active(x, K, q):
                total_single_index_states += 1
                ties = read_index_all_ties(x, K, q)
                if len(ties) > 1:
                    single_index_ties += 1

    print(f"read_index (single-index regime): {total_single_index_states} active, "
          f"non-multi-index states checked; {single_index_ties} had a tie.")
    print(f"read_maxi (multi-index regime): {total_multi_index_states} multi-index states "
          f"checked; {multi_index_ties} had a tie (raw max-cell value).")
    print(f"Parity-invariance violations among tied read_maxi states: {parity_violations} "
          f"(expected 0: the tie-break choice never affects read_maxi(x) mod 2).")


if __name__ == "__main__":
    main()
