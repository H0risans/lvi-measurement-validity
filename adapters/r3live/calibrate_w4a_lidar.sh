#!/usr/bin/env bash
# W4a LiDAR calibration: run the Hilti adapter only (NO estimator, 0 P0) on a
# bag and summarize the point counts that R3LIVE will receive on cloud_out.
#
# Usage: bash calibrate_w4a_lidar.sh <bag> [out_dir]
set -eo pipefail
# ROS's profile scripts reference unset variables; do not run them under -u.
set +u
source /opt/ros/noetic/setup.bash
source "$HOME/catkin_r3live_ws/devel/setup.bash"
set -u

BAG="${1:?usage: calibrate_w4a_lidar.sh <bag> [out_dir]}"
OUT="${2:-$HOME/experiments/w4a_calib_$(date +%Y%m%d_%H%M%S)}"
AUDIT="$OUT/adapter_audit.jsonl"
PORT="${W4A_CALIB_PORT:-11314}"
export ROS_MASTER_URI="http://127.0.0.1:$PORT"

mkdir -p "$OUT"
rm -f "$AUDIT"

cleanup() {
  set +e
  [[ -n "${PLAY_PID:-}" ]] && kill "$PLAY_PID" 2>/dev/null
  [[ -n "${LAUNCH_PID:-}" ]] && kill "$LAUNCH_PID" 2>/dev/null
  [[ -n "${ROSCORE_PID:-}" ]] && kill "$ROSCORE_PID" 2>/dev/null
  wait 2>/dev/null
}
trap cleanup EXIT INT TERM

roscore -p "$PORT" > "$OUT/roscore.log" 2>&1 &
ROSCORE_PID=$!
sleep 2
roslaunch hilti_r3live_adapter test_adapter_only.launch audit_path:="$AUDIT" \
  > "$OUT/adapter.log" 2>&1 &
LAUNCH_PID=$!
sleep 5

# Count only; do not start r3live_mapping.
rosbag play --quiet "$BAG" > "$OUT/play.log" 2>&1
sleep 2
cleanup
trap - EXIT INT TERM

python3 - "$AUDIT" "$OUT/point_counts.csv" <<'PY'
import json, sys
src, dst = sys.argv[1], sys.argv[2]
counts = []
for line in open(src, encoding="utf-8"):
    try:
        r = json.loads(line)
    except json.JSONDecodeError:
        continue
    if r.get("kind") == "cloud":
        counts.append(int(r["points"]))
counts.sort()
n = len(counts)
def q(p):
    if not n: return float("nan")
    i = min(n - 1, max(0, int(round((n - 1) * p))))
    return counts[i]
with open(dst, "w", encoding="utf-8") as f:
    f.write("n,p01,p05,p25,p50,p75,p95,p99,max\n")
    f.write("%d,%.1f,%.1f,%.1f,%.1f,%.1f,%.1f,%.1f,%.1f\n" % (
        n, q(.01), q(.05), q(.25), q(.50), q(.75), q(.95), q(.99), q(1.0)))
print(open(dst, encoding="utf-8").read())
PY

echo "W4a calibration done: $OUT/point_counts.csv"
