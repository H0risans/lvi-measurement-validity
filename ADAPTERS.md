# Three-LIVO adapter matrix (W4c, 2026-11-19)

This file answers one question: can the same chain — fault injection → processing-exposure verification → validity decision → output hold — be attached to three LIVO systems without changing their estimator cores? Each system is validated separately. The three columns are **not** cross-system comparable evidence.

## 1. Matrix

| Item | FAST-LIVO2 | R3LIVE | LVI-SAM |
|---|---|---|---|
| Algorithm form | Direct photometric + filter | ESIKF + RGB point cloud | Factor-graph VIO + LIO |
| Integration level | In-process (native safety layer) | Level A: external supervisor, read-only topics | Level A: external supervisor, read-only topics |
| Algorithm source changes | Yes: `SAFETY_HOLD_OUTPUT`, `SAFETY_LIDAR_P50` | None | None (OpenCV4/C++14 compatibility patch only) |
| Image input | `/fault_injector/image_raw` after injector selection | `hilti_r3live_adapter` `image_out` (10 Hz) | Same image chain as R3LIVE (10 Hz) |
| LiDAR input | Hilti native point cloud | `hilti_r3live_adapter` `cloud_out` | `/lvisam/points` (Hesai → PointXYZIRT, rotated to IMU axes) |
| Raw odometry | `/aft_mapped_to_init` | `/aft_mapped_to_init` | `/lvi_sam/lidar/mapping/odometry` |
| Decision location | W16 inside `libvio` | External `safety_supervisor` | External `safety_supervisor` |
| Hold location | `LIVMapper::publish_odometry()` | `/safety/odom` (does not modify estimator output) | `/safety/odom` (does not modify estimator output) |
| LiDAR scale | Valid-constraint count (p05=14 / p50=1406.5) | Raw point count (p05=55,008 / p50=58,931) | Raw point count (exp18 calibration; not re-calibrated for the LVI-SAM front end) |
| Validated | exp15 real outage; 6 recovery-admission rows; 8 stage-1 replay rows | clean exp18: 1033 state/odom, all OK; degradation hold1/hold0, n=2 | clean exp18: 538 state/odom, all OK; 5 s degradation hold1/hold0, n=2 |
| Degradation/hold | Triggered online (UNKNOWN + hold) | Triggered: hold1 UNKNOWN 124/56 frames, hold_disp 0; hold0 follows raw (UNKNOWN 124/58 frames) | Triggered (5 s): hold1 UNKNOWN 17/18 frames, hold_disp 0; hold0 follows raw (UNKNOWN 230/18 frames); 3 s dropout reaches DEGRADED only |
| Accuracy claim | exp14/exp18 APE/RPE only | Not established | Not established (VINS rebooted 48 times) |
| Main evidence | `data/hold/`, `data/content_replay/` | `evidence/w4a/fix1/`, `evidence/w4c/w4c_r3_*` | `evidence/w4b/fix_imu1/`, `evidence/w4c/w4c_lvi_*` |
| Still missing | Optional migration to the external supervisor | Recovery-time comparison; repeat variability | Recovery-time comparison; repeat variability; trajectory-validated extrinsics |

## 2. Claim boundary

- **Supported.** Each of the three systems can be attached to the same event/supervision layer. R3LIVE and LVI-SAM record and publish the clean exp18 chain without changing their estimator cores. Both produce UNKNOWN in a pre-registered dropout and freeze the published pose when hold is enabled. FAST-LIVO2 implements decision and hold in-process.
- **Not supported.** Cross-system accuracy comparison; mechanism equivalence across the three systems; equivalence of hold behavior; LVI-SAM visual-inertial stability; direct reuse of one LiDAR threshold across systems.
- **Next step.** W5 is complete. Each degradation arm has n=2, but UNKNOWN duration and published envelope vary widely between repeats. The next study should quantify recovery-time distributions and repeat variability before any descriptive cross-system juxtaposition. Accuracy is still not compared.

## 3. Entry points

- Full manifest and hashes: `MANIFEST.yaml`.
- Build/run/acceptance commands: `REPRODUCE.md`.
- W4a: `adapters/r3live/`, `evidence/w4a/`.
- W4b: `adapters/lvisam/`, `evidence/w4b/`.
- Core supervisor: `safety_core/`; ROS node: `safety_ros/`.
