#!/usr/bin/env bash
# Offline acceptance for the released supervisor:
#   1) build core + 3 unit tests
#   2) replay the W16 state machine on the bundled CSVs
# No ROS, no estimator, no bag.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD="${BUILD_DIR:-$ROOT/build}"
OUT="${OUT_DIR:-$BUILD/w3}"

if [[ "${SKIP_BUILD:-0}" != "1" ]]; then
  BUILD_DIR="$BUILD" "$ROOT/build_clean.sh"
fi

echo "== W3 offline equivalence =="
mkdir -p "$OUT"
"$ROOT/tools/run_w3.sh" "$ROOT/data/w3" "$OUT" | tee "$OUT/run_stdout.txt"
grep -q "W3 PASS" "$OUT/run_stdout.txt"
echo "offline smoke PASS"
