#!/usr/bin/env bash
# Clean build for the safety_supervisor research snapshot.
#
#   ./build_clean.sh              # core library + 3 no-ROS tests
#   ./build_clean.sh --with-ros   # also build the ROS 1 node in a temp catkin ws
#
# No estimator is started and no bag is played.  The ROS build only compiles
# supervisor_node.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD="${BUILD_DIR:-$ROOT/build}"
JOBS="${JOBS:-2}"
WITH_ROS=0
for arg in "$@"; do
  case "$arg" in
    --with-ros) WITH_ROS=1 ;;
    -h|--help) sed -n '1,12p' "$0"; exit 0 ;;
    *) echo "unknown argument: $arg" >&2; exit 2 ;;
  esac
done

need() { command -v "$1" >/dev/null 2>&1 || { echo "missing: $1" >&2; exit 1; }; }
need cmake
need g++

echo "[1/2] safety_core"
cmake -S "$ROOT/safety_core" -B "$BUILD/core" -DCMAKE_BUILD_TYPE=Release
cmake --build "$BUILD/core" -j "$JOBS"
( cd "$BUILD/core" && ctest --output-on-failure )

if [[ "$WITH_ROS" == "1" ]]; then
  echo "[2/2] safety_ros (catkin)"
  # ROS setup scripts are not set -u clean.
  set +u
  # shellcheck disable=SC1091
  source /opt/ros/noetic/setup.bash
  set -u
  need catkin_make
  rm -rf "$BUILD/ws"
  mkdir -p "$BUILD/ws/src"
  cp -a "$ROOT/safety_core" "$BUILD/ws/src/"
  cp -a "$ROOT/safety_ros" "$BUILD/ws/src/"
  ( cd "$BUILD/ws" && catkin_make -j "$JOBS" )
  test -x "$BUILD/ws/devel/lib/safety_supervisor/supervisor_node"
  echo "ROS node: $BUILD/ws/devel/lib/safety_supervisor/supervisor_node"
else
  echo "[2/2] ROS build skipped (pass --with-ros to enable)"
fi

echo "build OK"
