# 三 LIVO 适配清单（W4c，2026-11-19）

本文件只回答一个问题：同一套“故障注入 → 处理暴露核验 → 可靠性判决 → 输出弃权”能否在不改算法核心的前提下，接到三个 LIVO 上；每个系统分别验收，**不把三列数字当作跨系统可比证据**。

## 1. 总表

| 项目 | FAST-LIVO2 | R3LIVE | LVI-SAM |
|---|---|---|---|
| 算法形态 | 直接光度 + 滤波 | ESIKF + RGB 点云 | 因子图 VIO + LIO |
| 接入级别 | 进程内（原生安全层） | Level A：外部 supervisor，只读话题 | Level A：外部 supervisor，只读话题 |
| 算法源码改动 | 有：`SAFETY_HOLD_OUTPUT`、`SAFETY_LIDAR_P50` | 无 | 无（OpenCV4/C++14 兼容补丁只修编译） |
| 图像输入 | injector 选帧后的 `/fault_injector/image_raw` | `hilti_r3live_adapter` 的 `image_out`（10 Hz） | 同 R3LIVE 图像链（10 Hz） |
| 点云输入 | Hilti 原生点云 | `hilti_r3live_adapter` 的 `cloud_out` | `/lvisam/points`（Hesai→PointXYZIRT、旋到 IMU 轴） |
| 原始 odom | `/aft_mapped_to_init` | `/aft_mapped_to_init` | `/lvi_sam/lidar/mapping/odometry` |
| 判决位置 | `libvio` 内 W16 | 外部 `safety_supervisor` | 外部 `safety_supervisor` |
| 弃权位置 | `LIVMapper::publish_odometry()` 内 hold | `/safety/odom`（不改算法输出） | `/safety/odom`（不改算法输出） |
| LiDAR 口径 | 有效约束数（p05=14 / p50=1406.5） | 原始点云条数（p05=55,008 / p50=58,931） | 原始点云条数（沿用 exp18 标定，未按 LVI-SAM 前端重标） |
| 已验证 | exp15 真实停摆、恢复准入 6 行、阶段 1 内容回放 8 行 | clean exp18 1 行（1033 state/odom，全 OK）+ 退化段 hold1/hold0 各 2 行（n=2） | clean exp18 1 行（538 state/odom，全 OK）+ 5 s 退化段 hold1/hold0 各 2 行（n=2） |
| 退化段/弃权 | 已在线触发（UNKNOWN + hold） | 已触发：hold1 两次 UNK 124/56 帧、hold_disp 0；hold0 输出跟随 raw（两次 UNK 124/58 帧） | 已触发（5 s）：hold1 两次 UNK 17/18 帧、hold_disp 0；hold0 输出跟随 raw（UNK 230/18 帧）；3 s 停更只到 DEGRADED |
| 精度声明 | 仅 exp14/exp18 的 APE/RPE | 不成立 | 不成立（VINS 48 次 reboot） |
| 主要证据 | `第4-5章_判别与恢复/a_stage/`、`f_stage/` | `evidence/w4a/fix1/`、`evidence/w4c/w4c_r3_*` | `evidence/w4b/fix_imu1/`、`evidence/w4c/w4c_lvi_*` |
| 仍缺 | 外部 supervisor 迁移（可选） | 恢复时间比较；重复间差异量化 | 恢复时间比较；重复间差异量化；外参轨迹核验 |

## 2. 结论口径

- **可写**：三个算法分别能接入同一事件层/监督层；R3LIVE 与 LVI-SAM 在不改算法源码的前提下完成 clean exp18 的记录与发布链路；两系统在预登记退化段中都能产生 UNKNOWN 并在 hold 时冻结发布位姿；FAST-LIVO2 的判决/弃权为进程内实现。
- **不可写**：三算法精度可比；三算法机制等价；R3LIVE/LVI-SAM 的弃权行为可跨系统等价；LVI-SAM 视觉-惯性融合稳定；同一阈值可直接跨系统复用。
- **下一步**：W5 已完成；退化段每臂 n=2，但重复间时长/包络差异大，若继续应先做恢复时间分布与重复差异量化，再讨论跨系统描述性并置；仍不比较精度。

## 3. 复现入口

- 总清单与哈希：`MANIFEST.yaml`。
- 构建/运行/验收命令：`REPRODUCE.md`。
- W4a：`adapters/r3live/`、`evidence/w4a/`。
- W4b：`adapters/lvisam/`、`evidence/w4b/`。
- 外部 supervisor 核心：`safety_core/`；ROS 节点：`safety_ros/`。
