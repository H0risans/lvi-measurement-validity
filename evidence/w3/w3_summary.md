# W3 离线等价摘要

工具：`tools/replay_w16.py`；一键脚本：`tools/run_w3.sh`；逐文件 JSON 见 `evidence/w3/`。

| CSV | p50 | 行数 | 与在线 `rel_state` 不一致 | 非 OK 帧 | 状态分布 |
|---|---:|---:|---:|---:|---|
| `m12e1_safety.csv` | 67.0（旧 p25 规则） | 2480 | 0 | 2008 | OK 472 / DEGRADED 20 / UNKNOWN 1988 |
| `m12c1/m12c1_safety.csv` | 1406.5（v2） | 2599 | 0 | 2318 | OK 281 / DEGRADED 10 / UNKNOWN 2308 |
| `m12r1_safety.csv` | 1406.5（干净参照） | 1336 | 无 `rel_state` 列 | 0 | OK 1336 |

关键转段（m12e1）：28.4352 s OK→DEGRADED，29.4352 s DEGRADED→UNKNOWN，35.5348 s UNKNOWN→OK，54.6336 s OK→DEGRADED，55.6335 s DEGRADED→UNKNOWN。

关键转段（m12c1）：28.4352 s OK→DEGRADED，29.4352 s DEGRADED→UNKNOWN；到序列结束未恢复。

注意：

- `m12e1` 的在线 CSV 是旧 p25 规则录制的，必须用 `p50=67` 才能逐帧对齐；用默认 `p50=1406.5` 会不匹配。
- `m12r1` 没有 `rel_state` 列，只能验证“干净运行不升级”，不能做标签对照。
- 结果只证明离线 W16 重放与当时的在线记录一致，不证明输出 hold、R3LIVE 或 LVI-SAM 的在线行为。
