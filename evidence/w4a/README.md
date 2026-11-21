# W4a 证据（R3LIVE Level-A 接入）

## 文件

| 文件 | 内容 |
|---|---|
| `launch_check.txt` | 0 P0：launch 静态检查与 VM `roslaunch --files` 解析 |
| `calibration_exp18.csv` | 0 P0：exp18 的 1094 帧 `cloud_out` 点数分位（p05=55,008 / p50=58,931） |
| `image_chain_summary.txt` | 0 P0：injector→adapter 10 Hz 链路，images=1094、clouds=1094、\|dt\| p50=6.1 ms |
| `fix1/run.json` | 第三次有效 clean 运行的汇总（done/valid/exit 0） |
| `fix1/adapter_audit.jsonl` | adapter 逐帧 audit；修复后 image=1094、cloud=1094 |
| `fix1/w4a_topics.bag` | `/safety/state`、`/safety/odom`、`/aft_mapped_to_init` 记录 |
| `fix1/vio_summary.txt` | R3LIVE VIO 计数：1094 callback、1028 state update、6 skipped |

## clean exp18 结果

- `/aft_mapped_to_init`、`/safety/odom`、`/safety/state` 各 **1033** 条。
- `state_counts = {"OK": 1033}`，无 UNKNOWN/DEGRADED，`hold_frames = 0`。
- 配对 993 帧中，`/safety/odom` 与原始 odom 最大位置差 **0.0 m**。
- 最终位置 `(-16.602989, 7.970427, -33.120181)`。

## 边界

- clean 行没有触发降级，因此不能据此声称“UNKNOWN 弃权已在线验证”。
- 3 P0 中含 2 次技术无效（缺 supervisor 节点、40 Hz 原图绕过 10 Hz 选帧）；第 3 次有效。
- R3LIVE 源码未改；只改 launch/remap 与 10 Hz 选帧链。
