#!/bin/sh
# Run from the repository root:  sh c_check/run_c_check.sh
# Needs gcc and python3. Takes about a minute.
set -e
cd c_check
python3 make_variants.py
for v in noE2c noE2a E2clast log; do gcc -O2 -I. -o build/$v build/ilifc_$v.c; done
gcc -O2 -I. -o build/core ilifc_core.c
echo "Mean writes between erasures (n=16, k=4, 10^4 trials, seed 1):"
printf "%-4s %-10s %-10s %-10s %-10s\n" q full noE2c noE2a E2c_last
for q in 4 6 8; do
  printf "%-4s %-10s %-10s %-10s %-10s\n" $q \
    "$(build/core 16 4 $q 10000 /dev/null)" "$(build/noE2c 16 4 $q 10000 /dev/null)" \
    "$(build/noE2a 16 4 $q 10000 /dev/null)" "$(build/E2clast 16 4 $q 10000 /dev/null)"
done
echo "(conference Figs. 5-7: proposed 44.195 / 76.015 / 107.982; CIL-ILIFC 41.554 / 72.637 / 104.177)"
for q in 3 4 6 8; do LOGF=build/log_q$q.txt build/log 16 4 $q 3000 /dev/null >/dev/null; done
cd ..
python3 c_check/compare_c_log.py
