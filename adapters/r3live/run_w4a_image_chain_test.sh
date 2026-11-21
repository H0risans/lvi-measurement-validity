#!/usr/bin/env bash
# W4a 0-P0 image-chain test: injector (passthrough + 4:1 select) + adapter,
# deliberately NO r3live_mapping.  Proves the adapter sees ~10 Hz selected
# frames, matching the P2 protocol, before any estimator run is requested.
set -euo pipefail

BAG="${BAG:?set BAG to the exp18 bag}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${OUT:-$HOME/experiments/w4a_image_chain_$(date +%Y%m%d_%H%M%S)}"
INJECTOR_CONFIG="${INJECTOR_CONFIG:-$HOME/catkin_ws/src/camera_fault_injector/config/hilti22_select10.yaml}"
PORT="${PORT:-11321}"
mkdir -p "$OUT"

set +u
source /opt/ros/noetic/setup.bash
source "$HOME/catkin_ws_safety/devel/setup.bash"
source "$HOME/catkin_r3live_ws/devel/setup.bash"
source "$HOME/catkin_ws/devel/setup.bash"
set -u
export CMAKE_PREFIX_PATH="$HOME/catkin_ws_safety/devel:$HOME/catkin_r3live_ws/devel:$HOME/catkin_ws/devel:$CMAKE_PREFIX_PATH"
export LD_LIBRARY_PATH="$HOME/catkin_ws_safety/devel/lib:$HOME/catkin_r3live_ws/devel/lib:$HOME/catkin_ws/devel/lib:$LD_LIBRARY_PATH"
export PATH="$HOME/catkin_ws_safety/devel/bin:$HOME/catkin_r3live_ws/devel/bin:$HOME/catkin_ws/devel/bin:$PATH"
export ROS_PACKAGE_PATH="$HOME/catkin_ws_safety/src:$HOME/catkin_r3live_ws/src:$HOME/catkin_ws/src:$ROS_PACKAGE_PATH"
export ROS_MASTER_URI="http://localhost:$PORT"
export ROS_HOSTNAME=localhost

CORE_PID=""; LAUNCH_PID=""
cleanup() {
  set +e
  [[ -n "$LAUNCH_PID" ]] && kill "$LAUNCH_PID" 2>/dev/null
  [[ -n "$CORE_PID" ]] && kill "$CORE_PID" 2>/dev/null
  wait 2>/dev/null
}
trap cleanup EXIT INT TERM

roscore -p "$PORT" > "$OUT/roscore.log" 2>&1 &
CORE_PID=$!
sleep 3
roslaunch "$HERE/test_w4a_image_chain.launch" \
  audit_path:="$OUT/adapter_audit.jsonl" \
  injector_config:="$INJECTOR_CONFIG" \
  > "$OUT/launch.log" 2>&1 &
LAUNCH_PID=$!

# Wait for the injector output topic to exist.
for _ in $(seq 1 30); do
  if rostopic list 2>/dev/null | grep -qx /fault_injector/image_raw; then break; fi
  sleep 1
done
sleep 2
rosbag play "$BAG" > "$OUT/play.log" 2>&1
sleep 3

python3 - "$OUT/adapter_audit.jsonl" <<'PY' | tee "$OUT/chain_summary.txt"
import json, sys
imgs=[]; clouds=[]
for line in open(sys.argv[1], encoding='utf-8'):
    r=json.loads(line)
    if r.get('kind')=='image': imgs.append(r['stamp_ns']/1e9)
    elif r.get('kind')=='cloud': clouds.append(r['stamp_ns']/1e9)
print(f"images={len(imgs)} clouds={len(clouds)}")
if imgs and clouds:
    print(f"image_span={imgs[-1]-imgs[0]:.3f}s cloud_span={clouds[-1]-clouds[0]:.3f}s")
    # Each cloud should pair with the selected image nearest in time.
    import bisect
    cs=sorted(clouds); ds=[]
    for t in imgs:
        i=bisect.bisect_left(cs,t)
        cand=cs[max(0,i-1):i+1]
        ds.append(min(abs(t-c) for c in cand))
    ds.sort()
    print(f"img-cloud nearest |dt| p50={ds[len(ds)//2]*1000:.1f}ms p95={ds[int(len(ds)*0.95)]*1000:.1f}ms")
print("EXPECT images~1094 clouds~1094 (raw 4376 images decimated 4:1)")
PY

echo "out=$OUT"
