#!/usr/bin/env bash
# W4a: one R3LIVE + external-supervisor bag run.  THIS STARTS AN ESTIMATOR AND
# CONSUMES P0.  It refuses to run unless W4A_ALLOW_ESTIMATOR=1 is set after the
# W4a pre-registration has been approved.
#
# Usage:
#   W4A_ALLOW_ESTIMATOR=1 BAG=/path/to/exp15.bag [IMAGE_TOPIC=...] \
#     [HOLD=1] [LIDAR_P05=...] [LIDAR_P50=...] bash run_w4a_bag.sh
set -euo pipefail

if [[ "${W4A_ALLOW_ESTIMATOR:-0}" != "1" ]]; then
  echo "refusing to start R3LIVE: set W4A_ALLOW_ESTIMATOR=1 after W4a pre-registration" >&2
  exit 2
fi

BAG="${BAG:?set BAG to a Hilti22 bag}"
HOLD="${HOLD:-1}"
LIDAR_P05="${LIDAR_P05:-55008.0}"
LIDAR_P50="${LIDAR_P50:-58931.0}"
INJECTOR_CONFIG="${INJECTOR_CONFIG:-$HOME/catkin_ws/src/camera_fault_injector/config/hilti22_select10.yaml}"
OUT="${OUT:-$HOME/experiments/w4a_$(date +%Y%m%d_%H%M%S)}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_CONFIG="${BASE_CONFIG:-$HOME/catkin_r3live_ws/src/r3live/config/r3live_config.yaml}"

# ROS profile scripts reference unset variables; do not run them under -u.
set +u
source /opt/ros/noetic/setup.bash
source "$HOME/catkin_ws_safety/devel/setup.bash"
source "$HOME/catkin_r3live_ws/devel/setup.bash"
# Injector lives in the FAST-LIVO2 catkin workspace; source it last, then
# re-add the other two workspaces explicitly (each setup.bash replaces paths).
source "$HOME/catkin_ws/devel/setup.bash"
set -u
export CMAKE_PREFIX_PATH="$HOME/catkin_ws_safety/devel:$HOME/catkin_r3live_ws/devel:$HOME/catkin_ws/devel:$CMAKE_PREFIX_PATH"
export LD_LIBRARY_PATH="$HOME/catkin_ws_safety/devel/lib:$HOME/catkin_r3live_ws/devel/lib:$HOME/catkin_ws/devel/lib:$LD_LIBRARY_PATH"
export PATH="$HOME/catkin_ws_safety/devel/bin:$HOME/catkin_r3live_ws/devel/bin:$HOME/catkin_ws/devel/bin:$PATH"
export ROS_PACKAGE_PATH="$HOME/catkin_ws_safety/src:$HOME/catkin_r3live_ws/src:$HOME/catkin_ws/src:$ROS_PACKAGE_PATH"

mkdir -p "$OUT"
AUDIT="$OUT/adapter_audit.jsonl"
LOG="$OUT/run.log"

# R3LIVE opens a display even in mapping-only mode; use a private Xvfb.
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
  [[ -n "${LAUNCH_PID:-}" ]] && kill "$LAUNCH_PID" 2>/dev/null
  [[ -n "${XVFB_PID:-}" ]] && kill "$XVFB_PID" 2>/dev/null
  wait 2>/dev/null
}
trap cleanup EXIT INT TERM

echo "W4a run: bag=$BAG hold=$HOLD p05=$LIDAR_P05 p50=$LIDAR_P50 injector=$INJECTOR_CONFIG" | tee "$LOG"
echo "out=$OUT" | tee -a "$LOG"

roslaunch "$HERE/r3live_with_supervisor.launch" \
  audit_path:="$AUDIT" \
  out_dir:="$OUT/r3live" \
  base_config:="$BASE_CONFIG" \
  injector_config:="$INJECTOR_CONFIG" \
  injected_image_topic:=/fault_injector/image_raw \
  image_topic:=/r3live_hilti_adapter/image_out \
  hold_output:="$([[ "$HOLD" == "1" ]] && echo true || echo false)" \
  lidar_p05:="$LIDAR_P05" \
  lidar_p50:="$LIDAR_P50" \
  > "$OUT/launch.log" 2>&1 &
LAUNCH_PID=$!

# Wait for the supervisor to advertise before recording/playing.
STATE_UP=0
for _ in $(seq 1 60); do
  if rostopic list 2>/dev/null | grep -qx /safety/state; then STATE_UP=1; break; fi
  sleep 1
done
if [[ "$STATE_UP" != "1" ]]; then
  echo "supervisor did not advertise /safety/state; see $OUT/launch.log" >&2
  exit 4
fi

rosbag record -O "$OUT/w4a_topics.bag" \
  /safety/state /safety/odom /aft_mapped_to_init \
  > "$OUT/record.log" 2>&1 &
REC_PID=$!

sleep 1
rosbag play --clock "$BAG" | tee -a "$LOG"

sleep 2
cleanup
trap - EXIT INT TERM

echo "wrote $OUT/w4a_topics.bag" | tee -a "$LOG"
rosbag info "$OUT/w4a_topics.bag" | tee -a "$LOG"
