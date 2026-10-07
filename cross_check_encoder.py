"""
Cross-check: manually drive the REAL, validated FlashSim (flash_sim_c_port,
faithful C port) through the exact 3-write sequence i=[1,1,4] on a SINGLE
sub-block (m=1), using the SAME phase-priority selection logic as sim(),
and see what physical state results and what the real decoder recovers.
This settles whether the exhaustive-proof's apply_op is faithfully matching
the real encoder for this specific transition sequence.
"""
from core_encoder import FlashSim
from roundtrip_verify_k4 import decode_subblock_k4

k = 4
q = 4
m = 1
sim = FlashSim(m, k, q, seed=0)
sim.x = [[0]*(k+1) for _ in range(m+1)]

def step(i):
    j = 1
    # Phase 0
    if sim.read_alone(j) and (sim.read_maxi(j) % 2) == (i % 2):
        sim.write_alone(j, i); print(f"i={i}: PHASE0 write_alone"); return True
    # Phase 1
    if sim.active(j) and sim.read_index(j) == i and sim.read_alone(j) == 0:
        sim.write(j, i); print(f"i={i}: PHASE1 write"); return True
    # Phase 2
    if (sim.read_index(j) == ((i % k) + 1) and sim.parity(j) == 0 and sim.read_alone(j) == 0):
        sim.write_change(j, i); print(f"i={i}: PHASE2 change_index"); return True
    # Phase 3
    if sim.read_maxnum(j) and sim.read_maxi(j) == i:
        sim.write_max(j, i); print(f"i={i}: PHASE3 write_max"); return True
    # Phase 4
    for layer in range(q):
        if sim.clear(j) and sim.read_layer(j) == layer:
            sim.write_new(j, i); print(f"i={i}: PHASE4 write_new"); return True
    print(f"i={i}: ERASURE (no phase fired)")
    return False

print("x =", sim.x[1][1:5])
for i in [1, 1, 4]:
    ok = step(i)
    print("  -> x =", sim.x[1][1:5])
    if not ok:
        break

claims = decode_subblock_k4(sim.x[1], k, q)
print("\nFinal state x =", sim.x[1][1:5])
print("Decoder claims (index, bit) pairs:", claims)
print("Expected true info (per intended semantics): index1 abandoned (was 0), index4=1")
