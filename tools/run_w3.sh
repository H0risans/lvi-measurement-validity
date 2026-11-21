#!/usr/bin/env bash
# W3 acceptance: replay the recorded W16 state machine and compare with the
# rel_state column written online.  No ROS, estimator or GPU is needed.
#
# Usage:
#   ./run_w3.sh [DATA_DIR] [OUT_DIR]
# If DATA_DIR is omitted, the repository layout is used.
set -euo pipefail
export PYTHONIOENCODING="${PYTHONIOENCODING:-utf-8}"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
DATA="${1:-$ROOT/../第4-5章_判别与恢复/m12_stage}"
OUT="${2:-$ROOT/evidence/w3}"
PY="${PYTHON:-python3}"

mkdir -p "$OUT"

# exp15 run recorded with the old p25 resume rule: p50=67 reproduces its
# rel_state labels exactly.
"$PY" "$HERE/replay_w16.py" "$DATA/m12e1_safety.csv" --p50 67 \
  --expect-mismatch 0 --json > "$OUT/m12e1_p25.json"

# exp15 run recorded with the v2 p50 rule; no output recovery, mismatch 0.
"$PY" "$HERE/replay_w16.py" "$DATA/m12c1/m12c1_safety.csv" --p50 1406.5 \
  --expect-mismatch 0 --json > "$OUT/m12c1_p50.json"

# Clean exp14 reference: no non-OK frame, no state column in this CSV.
"$PY" "$HERE/replay_w16.py" "$DATA/m12r1_safety.csv" --p50 1406.5 \
  --expect-non-ok 0 --json > "$OUT/m12r1_clean.json"

echo "W3 PASS: all three replays within tolerance"
echo "results: $OUT"
