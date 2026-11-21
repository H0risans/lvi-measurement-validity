# W0 baseline freeze

W0 makes the W1–W3 results traceable to fixed code, configuration and data rather than to whatever is currently installed on a machine. Full hashes are in `MANIFEST.yaml`.

## Frozen points

| Object | Freeze point | Note |
|---|---|---|
| FAST-LIVO2 | `~/catkin_ws/src/fast_livo` @ `916b3db29f6e0c8a9c70b8d189333fa359de7e58` | Adds optional `SAFETY_HOLD_OUTPUT` and `SAFETY_LIDAR_P50`; hold off by default, p50=1406.5 |
| Injector | `~/catkin_ws/src/camera_fault_injector` @ `5ade2ad327f820e7d12ea0b622d09de7ad5351c0` | Standalone ROS 1 package |
| R3LIVE | `~/catkin_r3live_ws/src/r3live` @ `6143a38537f28cb36eb24e9bbe2e39c8f7967157` | Event/acceptance layer only; no W16/hold integration |
| Base configuration | `config/HILTI22.yaml` sha256 `daeb30e2…` | Hilti22 platform |
| W16 thresholds | `safety_thresholds_v2.txt` sha256 `dc7b1d0a…` | 14 tau values; p50 is compiled into `RelConfig` |
| W16 source | `safety_reliability.h` sha256 `8fb1efc0…` | Copied to `safety_core/include/safety/reliability.h`; only the header guard changed |
| exp15 data | `/home/nano/datasets/HILTI22/exp15_attic_to_upper_gallery.bag` | 20,302,484,455 B; sha256 `3489d798…` |
| Three safety CSVs | `data/w3/` | Hashes in `MANIFEST.yaml`; m12e1 was recorded under the old p25 rule |

## Acceptance

1. Build `safety_core` from a clean tree: `cmake -S . -B build && cmake --build build`; all three tests pass.
2. `tools/run_w3.sh`: mismatch 0 for m12e1/m12c1; non-OK 0 for m12r1.
3. `safety_ros` builds in a clean catkin workspace; the synthetic-bag replay passes (W2 evidence).
4. Compare the copied core files against `core.files` in `MANIFEST.yaml`; confirm no drift.

## Not distributed

- HILTI22 raw bags (20.3 GB) and the full FAST-LIVO2 source/binaries are not in the release; verify the commits and hashes in `MANIFEST.yaml` on the VM.
- `safety_ros` build outputs (`devel/`, `build/`) are not committed; rebuild them with `REPRODUCE.md`.

## Budget

W0 starts no estimator: **0 P0**. At freeze time the total was 274/280 and the F pool was 14/14. Later, W4a used 3 P0 and W4b used 2 P0. On 2026-11-19 a G pool of 20 was added; W4c used 6 P0 initially and 6 P0 for repeats. Current total: **291/300**, remaining 9 (D 1 + G 8).
