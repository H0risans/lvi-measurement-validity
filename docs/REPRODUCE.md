# 复现说明（W0–W3 + W4a + W4b clean + W4c）

本文件对应 `MANIFEST.yaml` 的 `release: safety_supervisor-0.3.2-w4c`。W0–W3 不启动任何 LVI 估计器（0 P0）；W4a 启动 R3LIVE 3 次（2 次技术无效 + 1 次有效 clean exp18）；W4b 启动 LVI-SAM 2 次（1 次 6 轴 IMU 技术无效 + 1 次有效 clean exp18）；W4c 清单 0 P0 + 退化段初轮 6 P0 + 重复 6 P0。总账 **291/300**（G 池 20 为 2026-11-19 追加，已用 12，剩 8）。

## 1. 环境

- Linux（验证环境 Ubuntu 20.04，g++ 9.4.0，CMake 3.16.3）。
- Python 3.8+（W3/W4a 辅助脚本只用标准库）。
- ROS Noetic（W2/W4a/W4b；W4a 还需要 Xvfb、`catkin_r3live_ws` 和带 injector 的 `catkin_ws`；W4b 还需要 `catkin_lvisam_ws`、GTSAM 4.0.3）。

本机 Windows 没有 g++/CMake，因此本文的构建与 W2 回放是在 VM `nano@192.168.58.129` 上完成的；W3 在本地与 VM 均可运行。

## 2. W1：纯 C++ 核心与单测

```bash
cd safety_core
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j4
cd build
ctest --output-on-failure
```

期望：

```
1/3 Test #1: test_reliability .... Passed
2/3 Test #2: test_output_gate .... Passed
3/3 Test #3: test_supervisor ..... Passed
100% tests passed, 0 tests failed out of 3
```

测试内容：

- `test_reliability`：W16 的默认阈值、干净流、DEGRADED/UNKNOWN 进入条件、恢复需 10 个健康帧、LiDAR 单独升级、NaN 中性。
- `test_output_gate`：关闭时直通、UNKNOWN 冻结在最后 OK 位姿、恢复释放、DEGRADED 释放、无锚点时不伪造位姿。
- `test_supervisor`：图像/点云/odom 编排；第 7 个盲帧 DEGRADED、第 17 个盲帧 UNKNOWN；恢复第 10 帧释放；与直接 W16 逐帧状态一致。

## 3. W3：离线等价

```bash
PYTHON=python3 ./tools/run_w3.sh /path/to/第4-5章_判别与恢复/m12_stage
```

数据要求：`m12e1_safety.csv`、`m12c1/m12c1_safety.csv`、`m12r1_safety.csv`；后两个路径见 `MANIFEST.yaml`。

期望：

| CSV | 配置 | 行数 | 结果 |
|---|---|---:|---|
| `m12e1_safety.csv` | p50=67（旧 p25 规则） | 2480 | mismatch=0 |
| `m12c1/m12c1_safety.csv` | p50=1406.5（v2） | 2599 | mismatch=0 |
| `m12r1_safety.csv` | p50=1406.5；无 `rel_state` 列 | 1336 | 非 OK=0 |

结果写入 `evidence/w3/*.json`。注意 `m12r1` 没有在线 `rel_state` 列，工具只统计重放状态，不比较标签。

## 4. W2：ROS Level-A 节点与合成回放

### 4.1 构建

```bash
source /opt/ros/noetic/setup.bash
mkdir -p ~/catkin_ws_safety/src
cp -r safety_ros ~/catkin_ws_safety/src/safety_supervisor
cp -r safety_core ~/catkin_ws_safety/src/safety_core
cd ~/catkin_ws_safety
catkin_make -j4
source devel/setup.bash
```

节点依赖 `roscpp/sensor_msgs/nav_msgs/std_msgs`；`safety_core` 只作为同工作空间的相对 include，不会被当成独立 catkin 包。

### 4.2 合成回放

```bash
source /opt/ros/noetic/setup.bash
source ~/catkin_ws_safety/devel/setup.bash
bash safety_ros/test/run_synth_test.sh
```

脚本自带 roscore（端口 11312），生成 40 帧合成 bag：

- 前 10 帧有图像，之后无图像；
- 前 20 帧 LiDAR 2000 点，之后空；
- 以默认 W16 计数器，第 7 个盲帧进入 DEGRADED（帧索引 16），10 帧后进入 UNKNOWN（帧索引 26），之后保持最后 OK 位姿 `x=1.5 m`。

期望输出：

```
states=40 odoms=40 last_x=1.500
W2 PASS: synthetic ROS replay matches the offline W16 sequence
```

### 4.3 接新 LIVO 系统

只改 launch 参数：

```bash
roslaunch safety_supervisor supervisor.launch \
  image_topic:=/your/image \
  lidar_topic:=/your/lidar \
  odom_topic:=/your/odom \
  hold_output:=true \
  lidar_p05:=<calibrated> \
  lidar_p50:=<calibrated>
```

注意：

- `lidar_p05/p50` 是**有效约束数**阈值。若系统只暴露原始点云，需要先做适配/标定；直接套 14/1406.5 会产生错误的恢复/升级。
- 节点只发布 `/safety/odom`，不广播 TF；需要 TF 的消费者应显式使用该话题或自行广播。
- `hold_output` 默认关闭；W4a launch 默认打开以便记录弃权。开启后只在 UNKNOWN 冻结发布位姿，不写回估计器。

## 5. W4a：R3LIVE Level-A 接入（clean exp18）

W4a 不修改 R3LIVE 源码，只在 bag 与 R3LIVE 之间串入现有 `camera_fault_injector`，把 40 Hz 原始相机图选成 10 Hz 再交给适配层。链路：

```
exp18 bag → /alphasense/cam0/image_raw → camera_fault_injector (hilti22_select10.yaml)
          → /fault_injector/image_raw → hilti_r3live_adapter → /r3live_hilti_adapter/image_out
          → r3live_mapping + safety_supervisor
```

先做 0 P0 的链路核验（不启 R3LIVE）：

```bash
BAG=/home/nano/datasets/HILTI22/exp18_corridor_lower_gallery_2.bag \
  bash adapters/r3live/run_w4a_image_chain_test.sh
```

期望：`images=1094 clouds=1094`，image/cloud 时间跨度均约 109.3 s，最近邻 |dt| p50 约 6 ms。

再跑一次完整接入（会启动估计器并计 P0）：

```bash
W4A_ALLOW_ESTIMATOR=1 \
BAG=/home/nano/datasets/HILTI22/exp18_corridor_lower_gallery_2.bag \
OUT=$HOME/experiments/w4a_20261119/runs/w4a_exp18_clean_hold_fix1 \
  bash adapters/r3live/run_w4a_bag.sh
```

本次结果：`/aft_mapped_to_init`、`/safety/odom`、`/safety/state` 各 1033 条；`state_counts={"OK": 1033}`，`hold_frames=0`；run.json `status=done`、`valid=true`、`exit_code=0`、`settle_timeout=0`。clean exp18 没有触发 UNKNOWN，因此本次只验证接入、选帧、状态/位姿发布链路，不验证弃权行为或精度。

`lidar_p05/p50` 用 exp18 适配层 `cloud_out` 的点数标定：p05=55,008、p50=58,931；不能套 FAST-LIVO2 的 14/1406.5。标定脚本见 `adapters/r3live/calibrate_w4a_lidar.sh`。

## 6. W4b：LVI-SAM 接入与 clean exp18（2 P0）

W4b 不修改 LVI-SAM 算法，只用外部点云转换器与 launch/remap 接入。源码固定 `0d822f6dcac3378312f6703b4f45829e049f221a`，构建需要 OpenCV4/C++14 补丁 `adapters/lvisam/patches/opencv4_cxx14.patch` 与 GTSAM 4.0.3。

静态检查（本机，不需要 ROS）：

```bash
python3 工程化/adapters/lvisam/check_w4b_launch.py
```

期望最后一行 `W4b static check: PASS`。

VM 构建与 launch 解析（不启动估计器）：

```bash
cd ~/catkin_lvisam_ws && catkin_make -j4
source /opt/ros/noetic/setup.bash
source devel/setup.bash
roslaunch --files hilti_lvisam_adapter lvisam_hilti_stack.launch
```

期望解析出 `lvisam_hilti_stack.launch`、`hilti_lvisam_cloud.launch`、`lvisam_hilti.launch` 三个文件；`rospack find` 能解析 `hilti_lvisam_adapter`、`lvi_sam`、`camera_fault_injector`、`hilti_r3live_adapter`、`safety_supervisor`。构建产物为 `devel/lib/lvi_sam/` 下七个 `lvi_sam_*` 二进制。

转换器空跑（0 P0，只启 converter，不启 LVI-SAM）：回放 exp18 前 8 s，录制 `/lvisam/points`，期望 3 条消息、`point_step=24`、字段 `x,y,z,intensity,ring,time`、`ring` 0–31、`time` 0–0.1 s、坐标有限。证据：`evidence/w4b/converter_smoke.txt`。

clean exp18 运行（1 P0；必须已按台账 §0.8 预登记）：

```bash
W4B_ALLOW_ESTIMATOR=1 \
BAG=$HOME/datasets/HILTI22/exp18_corridor_lower_gallery_2.bag \
OUT=$HOME/experiments/w4b_20261119/runs/w4b_exp18_clean_hold_imu1 \
HOLD=1 LIDAR_P05=55008 LIDAR_P50=58931 PLAY_RATE=1.0 \
bash 工程化/adapters/lvisam/run_w4b_bag.sh
```

运行链包含 `imu_converter.py`：Hilti IMU 是 6 轴、`orientation` 恒为零，LVI-SAM 的 `imuPreintegration` 会因四元数范数不足 shutdown；转换器只在范数平方 <0.01 时填单位四元数，其余字段原样转发。该四元数是接口占位，不是姿态测量。

期望：duration 约 109 s；`/lvi_sam/lidar/mapping/odometry`、`/safety/state`、`/safety/odom` 各 ≥500（实测 538）、`state_counts={"OK":538}`、`hold_frames=0`、`run.json` status=done/valid=true/exit_code=0。VINS 侧会出现 48 次 failure detection/reboot，LIO 输出仍到袋尾；本行只证明 LIO→supervisor 发布链，不证明 VINS 稳定、精度、弃权或恢复收益。证据：`evidence/w4b/fix_imu1/`。

## 6.1 W4c：三算法清单 + 退化段（清单 0 P0，退化段 12 P0：初轮 6 + 重复 6）

W4c 的清单部分不启动估计器，只核对三份适配清单与总表：

```bash
ls ADAPTERS.md manifests/fast_livo2.yaml manifests/r3live.yaml manifests/lvisam.yaml
```

总表 `ADAPTERS.md` 明确每列的接入级别、输入、判决/弃权位置、已验证项和缺口；三份 manifest 分别记录 FAST-LIVO2、R3LIVE、LVI-SAM。

退化段用 exp18、injector `drop_burst`，R3LIVE 3 s、LVI-SAM 5 s（LVI-SAM 3 s 只到 DEGRADED）：

```bash
W4C_ALLOW_ESTIMATOR=1 SYSTEM=R3 HOLD=1 REP=1 TAG=w4c_r3_drop_hold1_r1f \
  BAG=$HOME/datasets/HILTI22/exp18_corridor_lower_gallery_2.bag \
  bash adapters/common/run_w4c_degradation.sh
W4C_ALLOW_ESTIMATOR=1 SYSTEM=R3 HOLD=0 REP=1 TAG=w4c_r3_drop_hold0_r1 \
  BAG=$HOME/datasets/HILTI22/exp18_corridor_lower_gallery_2.bag \
  bash adapters/common/run_w4c_degradation.sh
W4C_ALLOW_ESTIMATOR=1 SYSTEM=LVI HOLD=1 REP=1 TAG=w4c_lvi_drop5_hold1_r1 \
  BAG=$HOME/datasets/HILTI22/exp18_corridor_lower_gallery_2.bag \
  INJECTOR_CONFIG=$HOME/experiments/w4c_20261119/cfg/inject_drop_30_35.yaml \
  bash adapters/common/run_w4c_degradation.sh
W4C_ALLOW_ESTIMATOR=1 SYSTEM=LVI HOLD=0 REP=1 TAG=w4c_lvi_drop5_hold0_r1 \
  BAG=$HOME/datasets/HILTI22/exp18_corridor_lower_gallery_2.bag \
  INJECTOR_CONFIG=$HOME/experiments/w4c_20261119/cfg/inject_drop_30_35.yaml \
  bash adapters/common/run_w4c_degradation.sh
```

期望：R3LIVE hold1 `1121 state/safety`、`OK 987 / DEG 10 / UNK 124`、`hold_frames=124`、`hold_disp=0`；LVI-SAM 5 s hold1 `548`、`OK 521 / DEG 10 / UNK 17`、`hold_frames=17`、`hold_disp=0`；hold0 臂 `hold_frames=0`，safety 与 raw 按 header 配对差 0。详细表与限制见 [W4c_退化段记录_20261119.md](W4c_退化段记录_20261119.md)。

## 7. 基线核对

```bash
sha256sum safety_core/include/safety/reliability.h \
         safety_core/include/safety/output_gate.h \
         safety_core/include/safety/supervisor.h \
         safety_core/src/output_gate.cpp \
         tools/replay_w16.py \
         safety_ros/src/supervisor_node.cpp
```

与 `MANIFEST.yaml` 的 `core.files` 与 `offline_equivalence.tool_sha256` 对照。数据与上游提交的哈希见 `MANIFEST.yaml` 的 `baseline` / `datasets` 段。

W4a 的 launch/runner/test 哈希：

```bash
sha256sum adapters/r3live/r3live_with_supervisor.launch \
         adapters/r3live/run_w4a_bag.sh \
         adapters/r3live/test_w4a_image_chain.launch \
         adapters/r3live/run_w4a_image_chain_test.sh
```

与 `MANIFEST.yaml` 的 `adapters.r3live` 段对照；clean 运行摘要见 `evidence/w4a/fix1/run.json`。

## 8. 不包含的内容

- 不包含 Hilti 原始 bag（20.3 GB），也不包含 FAST-LIVO2/LVI-SAM 的完整源码或二进制；这些按 `MANIFEST.yaml` 的提交与哈希在 VM 上核对。
- W4a 只包含 R3LIVE 的 launch/remap 适配与 clean exp18 一行；W4b 包含 LVI-SAM 构建/适配与 clean exp18 一行；W4c 包含三算法清单、R3LIVE/LVI-SAM 各 hold1/hold0 初轮 6 行与重复 6 行（共 12 P0；每臂 n=2），不含三算法完整剂量/精度矩阵。
- 不承诺实时性、端侧性能或精度提升；W2 的合成回放只验证编排与状态序列，W4a/W4b 的 clean 行只验证接入与记录，W4c 只验证状态/弃权链，不等价于真实退化闭环或恢复收益实验。
