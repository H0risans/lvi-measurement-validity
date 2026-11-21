#!/usr/bin/env bash
# W2 acceptance: synthetic ROS bag -> supervisor_node -> /safety/state.
# Requires ROS Noetic and a catkin workspace containing safety_supervisor.
# The script starts its own roscore on port 11312, so it does not touch a
# running system.
set -eo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROS_PORT="${ROS_PORT:-11312}"
export ROS_MASTER_URI="http://127.0.0.1:${ROS_PORT}"
export ROS_HOME="${ROS_HOME:-/tmp/safety_ros_home}"
mkdir -p "$ROS_HOME"

source /opt/ros/noetic/setup.bash
if [ -f "$HOME/catkin_ws_safety/devel/setup.bash" ]; then
  source "$HOME/catkin_ws_safety/devel/setup.bash"
fi

CORE_PID=""
NODE_PID=""
REC_PID=""
cleanup() {
  for pid in "$REC_PID" "$NODE_PID" "$CORE_PID"; do
    [ -n "$pid" ] && kill "$pid" 2>/dev/null || true
  done
}
trap cleanup EXIT

roscore -p "$ROS_PORT" >/tmp/synth_roscore.log 2>&1 &
CORE_PID=$!
sleep 2

rosrun safety_supervisor supervisor_node \
  _hold_output:=true \
  _image_topic:=/fault_injector/image_raw \
  _lidar_topic:=/livox/lidar \
  _odom_topic:=/aft_mapped_to_init \
  >/tmp/synth_node.log 2>&1 &
NODE_PID=$!
sleep 1

rosbag record -O /tmp/safety_state.bag /safety/state /safety/odom \
  >/tmp/synth_record.log 2>&1 &
REC_PID=$!
sleep 2

python3 "$HERE/make_synth_bag.py" >/tmp/synth_bag.log 2>&1
rosbag play /tmp/safety_synth.bag -r 2 >/tmp/synth_play.log 2>&1
sleep 2

kill "$REC_PID" "$NODE_PID" 2>/dev/null || true
sleep 1
python3 "$HERE/check_synth_state.py" /tmp/safety_state.bag
