# W0 基线冻结

W0 的目标是让 W1–W3 的结论可以追溯到固定的代码/配置/数据，而不是依赖某台机器上的当前状态。完整哈希见 `MANIFEST.yaml`。

## 冻结点

| 对象 | 冻结点 | 备注 |
|---|---|---|
| FAST-LIVO2 | `~/catkin_ws/src/fast_livo` @ `916b3db29f6e0c8a9c70b8d189333fa359de7e58` | 含可选 `SAFETY_HOLD_OUTPUT`、`SAFETY_LIDAR_P50`；默认关闭/1406.5 |
| 注入器 | `~/catkin_ws/src/camera_fault_injector` @ `5ade2ad327f820e7d12ea0b622d09de7ad5351c0` | 独立 ROS1 包 |
| R3LIVE | `~/catkin_r3live_ws/src/r3live` @ `6143a38537f28cb36eb24e9bbe2e39c8f7967157` | 仅事件层复用，无 W16/输出弃权 |
| 基础配置 | `config/HILTI22.yaml` sha256 `daeb30e2…` | Hilti22 平台 |
| W16 阈值 | `第4-5章_判别与恢复/safety_thresholds_v2.txt` sha256 `dc7b1d0a…` | 14 个 tau；p50 在编译期 `RelConfig` 中 |
| W16 源 | `第4-5章_判别与恢复/m12_stage/safety_reliability.h` sha256 `8fb1efc0…` | 复制为 `safety_core/include/safety/reliability.h`，仅改 header guard |
| exp15 数据 | `/home/nano/datasets/HILTI22/exp15_attic_to_upper_gallery.bag` | 20,302,484,455 B；sha256 `3489d798…` |
| 三份安全 CSV | `第4-5章_判别与恢复/m12_stage/` | 哈希见 `MANIFEST.yaml`；m12e1 是旧 p25 规则 |

## 验收

1. 从干净目录构建 `safety_core`：`cmake -S . -B build && cmake --build build`，3 个测试全部通过。
2. `tools/run_w3.sh` 对 m12e1/m12c1 的 mismatch 为 0，m12r1 非 OK 为 0。
3. `safety_ros` 在干净 catkin 工作空间构建成功；合成 bag 回放通过（W2 证据）。
4. 对照 `MANIFEST.yaml` 的 `core.files` 哈希，确认复制后的核心文件没有漂移。

## 不在仓库内的内容

- Hilti 原始 bag（20.3 GB）与 FAST-LIVO2 完整源码/二进制不随发布包分发；按 `MANIFEST.yaml` 的提交与哈希在 VM 核对。
- `safety_ros` 的构建产物（`devel/`、`build/`）不入库；由 `REPRODUCE.md` 的命令重建。

## 预算

W0 不启动估计器，**0 P0**；冻结时总账 274/280，F 池 14/14。后续 W4a 用 3 P0、W4b 用 2 P0；2026-11-19 追加 G 池 20，W4c 初轮 6 + 重复 6；当前总账 **291/300、剩 9（D 1 + G 8）**。
