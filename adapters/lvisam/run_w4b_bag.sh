#!/usr/bin/env bash
# W4b: one LVI-SAM + external-supervisor clean bag run.  THIS STARTS AN
# ESTIMATOR AND CONSUMES P0.  It refuses to run unless W4B_ALLOW_ESTIMATOR=1
# is set after the W4b pre-registration (§0.7) has been approved.
#
# Usage:
#   W4B_ALLOW_ESTIMATOR=1 BAG=/path/to/exp18.bag \
#     [HOLD=1] [LIDAR_P05=55008] [LIDAR_P50=58931] [PLAY_RATE=1.0] \
#     bash run_w4b_bag.sh
set -euo pipefail

if [[ "${W4B_ALLOW_ESTIMATOR:-0}" != "1" ]]; then
  echo "refusing to start LVI-SAM: set W4B_ALLOW_ESTIMATOR=1 after W4b pre-registration" >&2
  exit 2
fi

BAG="${BAG:?set BAG to a Hilti22 bag}"
HOLD="${HOLD:-1}"
LIDAR_P05="${LIDAR_P05:-55008.0}"
LIDAR_P50="${LIDAR_P50:-58931.0}"
PLAY_RATE="${PLAY_RATE:-1.0}"
INJECTOR_CONFIG="${INJECTOR_CONFIG:-$HOME/catkin_ws/src/camera_fault_injector/config/hilti22_select10.yaml}"
OUT="${OUT:-$HOME/experiments/w4b_$(date +%Y%m%d_%H%M%S)}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -e "$OUT/run.json" ]]; then
  echo "refusing to overwrite existing run: $OUT/run.json" >&2
  exit 5
fi
mkdir -p "$OUT"

# ROS setup scripts reference unset variables; do not run them under -u.
set +u
source /opt/ros/noetic/setup.bash
source "$HOME/catkin_ws/devel/setup.bash"
source "$HOME/catkin_lvisam_ws/devel/setup.bash"
source "$HOME/catkin_r3live_ws/devel/setup.bash"
source "$HOME/catkin_ws_safety/devel/setup.bash"
set -u
export CMAKE_PREFIX_PATH="$HOME/catkin_ws/devel:$HOME/catkin_lvisam_ws/devel:$HOME/catkin_r3live_ws/devel:$HOME/catkin_ws_safety/devel:$CMAKE_PREFIX_PATH"
export LD_LIBRARY_PATH="$HOME/catkin_ws/devel/lib:$HOME/catkin_lvisam_ws/devel/lib:$HOME/catkin_r3live_ws/devel/lib:$HOME/catkin_ws_safety/devel/lib:$LD_LIBRARY_PATH"
export PATH="$HOME/catkin_ws/devel/bin:$HOME/catkin_lvisam_ws/devel/bin:$HOME/catkin_r3live_ws/devel/bin:$HOME/catkin_ws_safety/devel/bin:$PATH"
export ROS_PACKAGE_PATH="$HOME/catkin_ws/src:$HOME/catkin_lvisam_ws/src:$HOME/catkin_r3live_ws/src:$HOME/catkin_ws_safety/src:$ROS_PACKAGE_PATH"

AUDIT="$OUT/adapter_audit.jsonl"
FAULT_LOG="$OUT/fault_events.csv"
LOG="$OUT/run.log"

# LVI-SAM opens OpenCV windows through its feature/odometry nodes; use a private Xvfb.
XVFB_PID=""
for _d in 99 98 97 96 95; do
  Xvfb ":$_d" -screen 0 1280x1024x24 -nolisten tcp > "$OUT/xvfb_$_d.log" 2>&1 &
  XVFB_PID=$!
  sleep 1
  if kill -0 "$XVFB_PID" 2>/dev/null; then
    export DISPLAY=":$_d"
    break
  fi
  XVFB_PID=""
done
if [[ -z "$XVFB_PID" ]]; then
  echo "could not start Xvfb on :99..:95" >&2
  exit 3
fi

cleanup() {
  set +e
  if [[ -n "${REC_PID:-}" ]]; then
    kill -INT "$REC_PID" 2>/dev/null
    wait "$REC_PID" 2>/dev/null
  fi
  if [[ -n "${LAUNCH_PID:-}" ]]; then
    kill -INT "$LAUNCH_PID" 2>/dev/null
    sleep 2
    kill "$LAUNCH_PID" 2>/dev/null
    wait "$LAUNCH_PID" 2>/dev/null
  fi
  [[ -n "${XVFB_PID:-}" ]] && kill "$XVFB_PID" 2>/dev/null
  wait 2>/dev/null
}
trap cleanup EXIT INT TERM

echo "W4b run: bag=$BAG hold=$HOLD p05=$LIDAR_P05 p50=$LIDAR_P50 rate=$PLAY_RATE" | tee "$LOG"
echo "out=$OUT" | tee -a "$LOG"

roslaunch hilti_lvisam_adapter lvisam_hilti_stack.launch \
  injector_config:="$INJECTOR_CONFIG" \
  injector_fault_log:="$FAULT_LOG" \
  audit_path:="$AUDIT" \
  hold_output:="$([[ "$HOLD" == "1" ]] && echo true || echo false)" \
  lidar_p05:="$LIDAR_P05" \
  lidar_p50:="$LIDAR_P50" \
  > "$OUT/launch.log" 2>&1 &
LAUNCH_PID=$!

# Wait for the supervisor and converter to advertise before recording/playing.
UP=0
for _ in $(seq 1 90); do
  if ! kill -0 "$LAUNCH_PID" 2>/dev/null; then
    echo "launch died before topics appeared; see $OUT/launch.log" >&2
    tail -60 "$OUT/launch.log" >&2 || true
    exit 4
  fi
  TOPICS="$(rostopic list 2>/dev/null || true)"
  if grep -qx /safety/state <<<"$TOPICS" && grep -qx /lvisam/points <<<"$TOPICS"; then
    UP=1
    break
  fi
  sleep 1
done
if [[ "$UP" != "1" ]]; then
  echo "supervisor/converter did not advertise; see $OUT/launch.log" >&2
  tail -60 "$OUT/launch.log" >&2 || true
  exit 4
fi

rosbag record -O "$OUT/w4b_topics.bag" \
  /lvi_sam/lidar/mapping/odometry /safety/state /safety/odom /clock \
  > "$OUT/record.log" 2>&1 &
REC_PID=$!
sleep 1

set +e
rosbag play --clock -r "$PLAY_RATE" "$BAG" 2>&1 | tee -a "$LOG"
PLAY_RC=${PIPESTATUS[0]}
set -e

# Give the estimator a short drain window after the last message.
sleep 15

cleanup
trap - EXIT INT TERM

echo "play_rc=$PLAY_RC" | tee -a "$LOG"
rosbag info "$OUT/w4b_topics.bag" | tee -a "$LOG"

set +e
python3 "$HERE/summarize_w4b.py" "$OUT" "$PLAY_RC"
SUM_RC=$?
set -e
echo "summary_rc=$SUM_RC" | tee -a "$LOG"
exit "$SUM_RC"
