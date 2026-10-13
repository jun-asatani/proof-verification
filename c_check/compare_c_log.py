"""Compare every write logged by build/ilifc_log.c with exhaustive_verify.apply_op
on the touched sub-block (run from the repository root; see run_c_check.sh)."""
import sys, collections
sys.path.insert(0, ".")
from exhaustive_verify import apply_op
tot = bad = 0
kinds = collections.Counter()
for q in [3, 4, 6, 8]:
    for line in open(f"c_check/build/log_q{q}.txt"):
        c, i, pre, post = line.split()
        pre = tuple(map(int, pre)); post = tuple(map(int, post))
        tot += 1; kinds[c] += 1
        if apply_op(pre, int(i), 4, q, 2) != post:
            bad += 1
print(f"C writes compared: {tot}; mismatches: {bad}; by kind (A=write_alone, W=write, C=change_index, M=write_max, N=write_new): {dict(kinds)}")
