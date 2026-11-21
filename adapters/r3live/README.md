# W4a: R3LIVE external-supervisor integration

This directory adds launch/remap files and the 10 Hz image chain. It does not modify R3LIVE source. The goal is to make R3LIVE produce `/safety/state` and `/safety/odom` through the same decision/hold layer used by FAST-LIVO2.

## Topology

```text
camera_fault_injector (40 Hz raw camera -> select_stride=4 -> 10 Hz)
        |  /fault_injector/image_raw
        v
hilti_r3live_adapter -- /r3live_hilti_adapter/image_out --> r3live_mapping
        ^                                      |
        | /hesai/pandar                        +--> safety_supervisor (image)
        | /alphasense/imu                             ^
        +------------------ /r3live_hilti_adapter/cloud_out (lidar)
                            /aft_mapped_to_init          (odom)
```

`safety_supervisor` reads only:

- image: the R3LIVE `Image_topic` (adapter output, default `/r3live_hilti_adapter/image_out`);
- LiDAR: `/r3live_hilti_adapter/cloud_out`;
- odometry: `/aft_mapped_to_init`.

Outputs:

- `/safety/state`: JSON with state/reason/hold/outage_frames;
- `/safety/odom`: `nav_msgs/Odometry`; with `hold_output=true` it keeps the last valid pose while UNKNOWN;
- no TF is broadcast, avoiding a conflict with R3LIVE's `/aft_mapped_to_init` TF.

## Static check (0 P0)

```bash
python3 check_w4a_launch.py r3live_with_supervisor.launch
```

On the VM, parse the launch tree without starting nodes:

```bash
source /opt/ros/noetic/setup.bash
source ~/catkin_ws_safety/devel/setup.bash
source ~/catkin_r3live_ws/devel/setup.bash
export ROS_PACKAGE_PATH=$ROS_PACKAGE_PATH:$HOME/catkin_ws_safety/src
roslaunch --files r3live_with_supervisor.launch audit_path:=/tmp/w4a_audit.jsonl
```

## 10 Hz chain check (0 P0)

`run_w4a_image_chain_test.sh` starts only the injector and adapter, not R3LIVE:

```bash
BAG=/home/nano/datasets/HILTI22/exp18_corridor_lower_gallery_2.bag \
  bash run_w4a_image_chain_test.sh
```

Expected: `images=1094 clouds=1094`, nearest-neighbour |dt| p50 about 6 ms. Evidence: `evidence/w4a/` and `REPRODUCE.md` §5.

## Real run (starts the estimator; counts as P0)

`run_w4a_bag.sh` refuses to start unless `W4A_ALLOW_ESTIMATOR=1` is set. A pre-registration must first record:

- bag, R3LIVE commit, adapter commit, supervisor version;
- calibration source for `lidar_p05/lidar_p50`;
- whether injection is enabled (`injected_image_topic`);
- recorded topics and acceptance criteria.

Example after pre-registration:

```bash
W4A_ALLOW_ESTIMATOR=1 \
BAG=/home/nano/datasets/HILTI22/exp18_corridor_lower_gallery_2.bag \
LIDAR_P05=55008 LIDAR_P50=58931 \
HOLD=1 \
  bash run_w4a_bag.sh
```

The script starts `camera_fault_injector` with `hilti22_select10.yaml` (passthrough + 4:1 selection). The adapter must receive that 10 Hz output; never feed the 40 Hz raw camera directly to the adapter.

2026-11-19 clean exp18 result: `/aft_mapped_to_init`, `/safety/odom` and `/safety/state` each 1033 messages; `state_counts={"OK":1033}`, `hold_frames=0`; R3LIVE VIO received 1094 callbacks and executed 1028 state updates. A clean row does not trigger UNKNOWN, so it validates wiring/recording only, not hold behavior or accuracy.

## exp18 point-count calibration (0 P0)

On 2026-11-19 the adapter alone (`test_adapter_only.launch`) was replayed over exp18; 1094 `cloud_out` frames:

| quantile | p01 | p05 | p25 | p50 | p75 | p95 | p99 | max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| points | 53,781 | 55,008 | 56,461 | 58,931 | 61,003 | 61,790 | 62,457 | 63,013 |

For this sequence use `lidar_p05=55008`, `lidar_p50=58931`. The values 14/1406.5 are FAST-LIVO2 valid-constraint counts and must not be reused for R3LIVE. Raw calibration file: `evidence/w4a/calibration_exp18.csv`.

## Limitations

- `lidar_p05/p50` defaults are Hilti/FAST-LIVO2 valid-constraint counts; R3LIVE `cloud_out` must be calibrated first.
- W4a demonstrates integration and recording, not R3LIVE closed-loop accuracy or recovery benefit.
- `hold_output=true` affects only the supervisor's `/safety/odom`; it does not write back into R3LIVE.
