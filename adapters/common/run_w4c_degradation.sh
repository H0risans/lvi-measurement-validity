#!/usr/bin/env bash
# W4c degradation run: one estimator arm under a 3 s visual dropout.
# THIS STARTS AN ESTIMATOR AND CONSUMES P0.  It refuses to run unless
# W4C_ALLOW_ESTIMATOR=1 is set after the section 0.9 pre-registration.
#
# Usage:
#   W4C_ALLOW_ESTIMATOR=1 SYSTEM=R3 HOLD=1 REP=1 TAG=w4c_r3_drop_hold1_r1 \
#     BAG=/path/to/exp18.bag bash run_w4c_degradation.sh
set -euo pipefail

if [[ "${W4C_ALLOW_ESTIMATOR:-0}" != "1" ]]; then
  echo "refusing to start: set W4C_ALLOW_ESTIMATOR=1 after W4c pre-registration" >&2
  exit 2
fi

SYSTEM="${SYSTEM:?set SYSTEM=R3 or SYSTEM=LVI}"
HOLD="${HOLD:?set HOLD=0 or HOLD=1}"
REP="${REP:?set REP=1 or REP=2}"
TAG="${TAG:?set TAG}"
BAG="${BAG:?set BAG}"
INJECTOR_CONFIG="${INJECTOR_CONFIG:-$HOME/experiments/w4c_20261119/cfg/inject_drop_30_33.yaml}"
OUT="${OUT:-$HOME/experiments/w4c_20261119/runs/$TAG}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
W4A_RUNNER="${W4A_RUNNER:-$HOME/experiments/w4a_20261119/run_w4a_bag.sh}"
W4B_RUNNER="${W4B_RUNNER:-$HOME/experiments/w4b_20261119/run_w4b_bag.sh}"
SUMMARIZER="${SUMMARIZER:-$HOME/experiments/w4c_20261119/summarize_degradation.py}"

if [[ -e "$OUT" ]]; then
  echo "refusing to overwrite existing run dir: $OUT" >&2
  exit 5
fi
mkdir -p "$OUT"
echo "$TAG system=$SYSTEM hold=$HOLD rep=$REP bag=$BAG" > "$OUT/tag.txt"
echo "injector=$INJECTOR_CONFIG" >> "$OUT/tag.txt"

set +e
if [[ "$SYSTEM" == "R3" ]]; then
  W4A_ALLOW_ESTIMATOR=1 BAG="$BAG" HOLD="$HOLD" LIDAR_P05=55008.0 LIDAR_P50=58931.0 \
    INJECTOR_CONFIG="$INJECTOR_CONFIG" OUT="$OUT" bash "$W4A_RUNNER"
  RUN_RC=$?
  BAGFILE="$OUT/w4a_topics.bag"
  ODOM_TOPIC="/aft_mapped_to_init"
elif [[ "$SYSTEM" == "LVI" ]]; then
  W4B_ALLOW_ESTIMATOR=1 BAG="$BAG" HOLD="$HOLD" LIDAR_P05=55008.0 LIDAR_P50=58931.0 \
    INJECTOR_CONFIG="$INJECTOR_CONFIG" OUT="$OUT" bash "$W4B_RUNNER"
  RUN_RC=$?
  BAGFILE="$OUT/w4b_topics.bag"
  ODOM_TOPIC="/lvi_sam/lidar/mapping/odometry"
else
  echo "SYSTEM must be R3 or LVI" >&2
  exit 2
fi

set +u
source /opt/ros/noetic/setup.bash
set -u

python3 "$SUMMARIZER" "$OUT" --bag "$BAGFILE" --odom-topic "$ODOM_TOPIC" \
  --label "$TAG" --hold-arm "$HOLD" --play-rc "$RUN_RC" \
  > "$OUT/degradation_stdout.txt" 2>&1
SUM_RC=$?
set -e

cat "$OUT/degradation_stdout.txt" || true
echo "run_rc=$RUN_RC summary_rc=$SUM_RC out=$OUT"
exit "$SUM_RC"
