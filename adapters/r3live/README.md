# W4a：R3LIVE 外部 supervisor 接入

本目录只做 launch/remap 与 10 Hz 选帧链，不改 R3LIVE 源码。目标是让 R3LIVE 这一路也产生
`/safety/state` 与 `/safety/odom`，从而与 FAST-LIVO2 共用同一套判决/弃权层。

## 拓扑

```text
camera_fault_injector (40 Hz raw camera 必需；select_stride=4 → 10 Hz)
        │  /fault_injector/image_raw
        ▼
hilti_r3live_adapter ── /r3live_hilti_adapter/image_out ──► r3live_mapping (Image_topic)
        ▲                                      │
        │ /hesai/pandar                        └──► safety_supervisor (image_topic)
        │ /alphasense/imu                              ▲
        └──────────────────────────────────────────────┘
                                    /r3live_hilti_adapter/cloud_out (lidar_topic)
                                    /aft_mapped_to_init          (odom_topic)
```

`safety_supervisor` 只读：
- image：`R3LIVE Image_topic`（即 adapter 输出，默认 `/r3live_hilti_adapter/image_out`）；
- lidar：`/r3live_hilti_adapter/cloud_out`；
- odom：`/aft_mapped_to_init`。

输出：
- `/safety/state`：JSON 字符串，含 state/reason/hold/outage_frames；
- `/safety/odom`：`nav_msgs/Odometry`；`hold_output=true` 时在不可用状态保持最后可信位姿；
- 不广播 TF，避免与 R3LIVE 的 `/aft_mapped_to_init` TF 冲突。

## 静态检查（0 P0）

```bash
python3 check_w4a_launch.py r3live_with_supervisor.launch
```

在 VM 上还可以只解析 launch 树，不启动节点：

```bash
source /opt/ros/noetic/setup.bash
source ~/catkin_ws_safety/devel/setup.bash
source ~/catkin_r3live_ws/devel/setup.bash
export ROS_PACKAGE_PATH=$ROS_PACKAGE_PATH:$HOME/catkin_ws_safety/src
roslaunch --files r3live_with_supervisor.launch audit_path:=/tmp/w4a_audit.jsonl
```

`--files` 只打印解析后的 launch 文件与参数，不启动估计器。

## 10 Hz 链路核验（0 P0）

`run_w4a_image_chain_test.sh` 只启 injector + adapter，不启 R3LIVE：

```bash
BAG=/home/nano/datasets/HILTI22/exp18_corridor_lower_gallery_2.bag \
  bash run_w4a_image_chain_test.sh
```

期望 `images=1094 clouds=1094`，最近邻 |dt| p50 约 6 ms；证据见
`工程化/evidence/w4a/` 与 `工程化/REPRODUCE.md` §5。

## 真实运行（会启动估计器，计 P0）

`run_w4a_bag.sh` 默认拒绝运行；只有显式设置 `W4A_ALLOW_ESTIMATOR=1` 才会启动
R3LIVE。启动前必须按 [工程化路线](../工程化路线_20261118.md) 的 W4a 预登记写清：

- bag、R3LIVE commit、adapter commit、supervisor 版本；
- `lidar_p05/lidar_p50` 的标定来源；
- 是否开注入（`injected_image_topic`）；
- 记录话题与验收判据。

示例（预登记批准后）：

```bash
W4A_ALLOW_ESTIMATOR=1 \
BAG=/home/nano/datasets/HILTI22/exp18_corridor_lower_gallery_2.bag \
LIDAR_P05=55008 LIDAR_P50=58931 \
HOLD=1 \
  bash run_w4a_bag.sh
```

脚本默认启动 `camera_fault_injector`（`hilti22_select10.yaml`，passthrough + 4:1 选帧），
adapter 只接收其 10 Hz 输出；不要直接把 40 Hz 原始图送 adapter。

2026-11-19 clean exp18 结果：`/aft_mapped_to_init`、`/safety/odom`、`/safety/state` 各
1033 条；`state_counts={"OK":1033}`、`hold_frames=0`；R3LIVE VIO 1094 回调、1028 次状态更新。
clean 行未触发 UNKNOWN，只证明接入与发布链路，不证明弃权行为或精度。

## exp18 点数标定（0 P0）

2026-11-19 只启动 adapter（`test_adapter_only.launch`）回放 exp18，统计
`/r3live_hilti_adapter/cloud_out` 的 1094 帧：

| 分位 | p01 | p05 | p25 | p50 | p75 | p95 | p99 | max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 点数 | 53,781 | 55,008 | 56,461 | 58,931 | 61,003 | 61,790 | 62,457 | 63,013 |

因此本序列 W4a 用 `lidar_p05=55008`、`lidar_p50=58931`。14/1406.5 是
FAST-LIVO2 的有效约束数口径，不能用于 R3LIVE。标定原始文件：
`工程化/evidence/w4a/calibration_exp18.csv`。

## 限制

- `lidar_p05/p50` 默认是 Hilti/FAST-LIVO2 的有效约束数口径；R3LIVE 的
  `cloud_out` 计数必须先标定，不能直接套 14/1406.5。
- W4a 只证明“接入与记录”，不等于 R3LIVE 闭环精度或恢复收益。
- `hold_output=true` 只影响 supervisor 发布的 `/safety/odom`，不回写 R3LIVE。
