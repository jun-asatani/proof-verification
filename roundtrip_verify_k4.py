"""
Decode-uniqueness round-trip checker built directly on the REAL C-ported
encoder (flash_sim_c_port.FlashSim), not a reinvented generalization.

Implements the decoder D2 as described in the manuscript Section 3.3:
  - if a sub-block is active and NOT in the multi-index state (read_alone==0):
      decode via read_index / parity (single index, single bit).
  - if a sub-block IS in the multi-index state (read_alone==1, k=4 hardcoded
    "mirror pair" check exactly as in the C code):
      decode each of its 2 sections independently: local index via the same
      cyclic-difference rule restricted to the section, bit = parity of the
      section's l=2 cells.
  - a sub-block that is clear (or full) contributes no (index,bit) claim.
  - overall v_hat[idx] = bit reported by whichever active sub-block currently
    claims idx (if any), else 0 (ILIFC-family convention: no active claim = 0).

True v is tracked directly: every loop iteration in sim() picks index i and
attempts to flip v[i]; if a write phase succeeds, v[i] ^= 1 and we compare
D2(x) against v. If no phase succeeds, that's block erasure (i's flip is not
applied, loop ends).
"""
from core_encoder import FlashSim


def decode_subblock_k4(xj, k, q):
    """Return set of (index, bit) pairs this sub-block currently claims,
    using EXACTLY the C code's read_alone/read_index logic for k=4."""
    assert k == 4
    x1, x2, x3, x4 = xj[1], xj[2], xj[3], xj[4]

    # read_alone, verbatim from C
    read_alone = 0
    if x1 != x2 and x3 != x4:
        if x1 == x3 and x2 == x4:
            read_alone = 1

    if read_alone:
        # multi-index state: decode each l=2 section independently
        claims = set()
        for sec_idx, (a, b) in enumerate([(x1, x2), (x3, x4)]):
            # local cyclic diff for a length-2 section: pos1: a-b, pos2: b-a
            d1 = a - b
            d2 = b - a
            if d1 >= d2:
                local_pos = 1
            else:
                local_pos = 2
            global_pos = sec_idx * 2 + local_pos
            bit = (a + b) % 2
            claims.add((global_pos, bit))
        return claims
    else:
        # single-index decode via read_index (0 if clear/full -> no claim)
        total_charge = x1 + x2 + x3 + x4
        flag_clear = not (x1 == x2 == x3 == x4)
        if total_charge == k * (q - 1) or not flag_clear:
            return set()  # full or clear: no active claim
        # cyclic diff, C-faithful (1-indexed, position k wraps to position 1's predecessor)
        vec = [None, x1, x2, x3, x4]
        max_diff = vec[1] - vec[4]
        index = 1
        for n in range(2, 5):
            diff = vec[n] - vec[n - 1]
            if max_diff < diff:
                max_diff = diff
                index = n
        bit = total_charge % 2
        return {(index, bit)}


def decode_full(sim):
    """Decode the whole flash memory state into v_hat (dict idx->bit, default 0)."""
    v_hat = {i: 0 for i in range(1, sim.k + 1)}
    conflicts = []
    for j in range(1, sim.m + 1):
        claims = decode_subblock_k4(sim.x[j], sim.k, sim.q)
        for (idx, bit) in claims:
            if idx in v_hat and v_hat[idx] != 0 and v_hat[idx] != bit:
                conflicts.append((j, idx, bit, v_hat[idx]))
            v_hat[idx] = bit if bit == 1 else v_hat[idx]
            # NOTE: only overwrite when bit==1 would lose info if two claims disagree;
            # let's just record last-writer for now and flag conflicts separately.
            v_hat[idx] = bit
    return v_hat, conflicts


def run_trial_with_decode_check(m, k, q, rng_seed, trial_id, verbose_first_fail=False):
    sim = FlashSim(m, k, q, seed=rng_seed)
    sim.x = [[0] * (k + 1) for _ in range(m + 1)]
    v_true = {i: 0 for i in range(1, k + 1)}
    write_num = 0
    mismatch_found = False
    first_mismatch_step = None

    while True:
        a = 0
        i = int(k * sim.rng.random()) + 1
        if i > k:
            i = k

        # Phase 0
        for j in range(1, m + 1):
            if sim.read_alone(j) and (sim.read_maxi(j) % 2) == (i % 2):
                sim.write_alone(j, i)
                write_num += 1
                a = 1
                break
        if a == 1:
            v_true[i] ^= 1
            v_hat, conflicts = decode_full(sim)
            if v_hat != v_true:
                mismatch_found = True
                if first_mismatch_step is None:
                    first_mismatch_step = (write_num, 'phase0', i, dict(v_true), dict(v_hat))
            continue

        # Phase 1
        for j in range(1, m + 1):
            if sim.active(j) and sim.read_index(j) == i and sim.read_alone(j) == 0:
                sim.write(j, i)
                write_num += 1
                a = 1
                break
        if a == 1:
            v_true[i] ^= 1
            v_hat, conflicts = decode_full(sim)
            if v_hat != v_true:
                mismatch_found = True
                if first_mismatch_step is None:
                    first_mismatch_step = (write_num, 'phase1', i, dict(v_true), dict(v_hat))
            continue

        # Phase 2
        for j in range(1, m + 1):
            if (sim.read_index(j) == ((i % k) + 1) and sim.parity(j) == 0
                    and sim.read_alone(j) == 0):
                sim.write_change(j, i)
                write_num += 1
                a = 1
                break
        if a == 1:
            v_true[i] ^= 1
            v_hat, conflicts = decode_full(sim)
            if v_hat != v_true:
                mismatch_found = True
                if first_mismatch_step is None:
                    first_mismatch_step = (write_num, 'phase2', i, dict(v_true), dict(v_hat))
            continue

        # Phase 3 (E2c / write_max)
        for j in range(1, m + 1):
            if sim.read_maxnum(j) and sim.read_maxi(j) == i:
                sim.write_max(j, i)
                write_num += 1
                a = 1
                break
        if a == 1:
            v_true[i] ^= 1
            v_hat, conflicts = decode_full(sim)
            if v_hat != v_true:
                mismatch_found = True
                if first_mismatch_step is None:
                    first_mismatch_step = (write_num, 'phase3', i, dict(v_true), dict(v_hat))
            continue

        # Phase 4
        found = False
        for l in range(0, q):
            for j in range(1, m + 1):
                if sim.clear(j) and sim.read_layer(j) == l:
                    sim.write_new(j, i)
                    write_num += 1
                    a = 1
                    found = True
                    break
            if found:
                break
        if a == 1:
            v_true[i] ^= 1
            v_hat, conflicts = decode_full(sim)
            if v_hat != v_true:
                mismatch_found = True
                if first_mismatch_step is None:
                    first_mismatch_step = (write_num, 'phase4', i, dict(v_true), dict(v_hat))
            continue

        break  # erasure

    return write_num, mismatch_found, first_mismatch_step


if __name__ == "__main__":
    import sys
    k = 4
    m = 4  # n=16, k=4
    q = 4
    num_trials = 200

    fail_count = 0
    phase_fail_counter = {}
    for t in range(num_trials):
        wn, mismatch, first_fail = run_trial_with_decode_check(m, k, q, rng_seed=1000 + t, trial_id=t)
        if mismatch:
            fail_count += 1
            phase = first_fail[1]
            phase_fail_counter[phase] = phase_fail_counter.get(phase, 0) + 1

    print(f"k={k}, q={q}, m={m}: {fail_count}/{num_trials} trials had a decode mismatch "
          f"({100*fail_count/num_trials:.1f}%)")
    print("First-mismatch phase breakdown:", phase_fail_counter)

    # show one concrete example
    for t in range(num_trials):
        wn, mismatch, first_fail = run_trial_with_decode_check(m, k, q, rng_seed=1000 + t, trial_id=t)
        if mismatch:
            print("\nExample first mismatch:")
            print("  write_num, phase, flipped_i, v_true, v_hat =", first_fail)
            break
