# Experiment log (W0–W5, English summary)

This is the public, English-language experiment log for release `0.3.2-w4c`. It replaces the longer internal Chinese working notes; those remain in the author's workspace and are not part of the public repository.

## Scope

The release asks a measurement question: **does an image-side anomaly actually reach the state estimate as a harmful measurement update?** The chain under test is:

1. event-level injection with preserved timestamps, frame count and order;
2. processing-exposure verification (did the replacement reach the estimator?);
3. a W16 validity decision (OK / DEGRADED / UNKNOWN);
4. optional output hold (publish the last valid pose while UNKNOWN).

The three systems are integrated separately. The shared element is the decision/hold **contract**, not a verified cross-system mechanism. No cross-system accuracy comparison is made.

## W0 — baseline freeze

- FAST-LIVO2 `916b3db`, injector `5ade2ad`, R3LIVE `6143a385`.
- W16 thresholds v2: `tau_d2=700`, `tau_photo_z=32`, `tau_dpos=0.05`, etc.; p50 is compiled into `RelConfig`.
- Three safety CSVs from exp15/exp14 are in `data/w3/`; `tools/run_w3.sh` replays them with zero mismatch.
- 0 P0.

## W1 — `safety_core`

- Pure C++14: `ReliabilityMonitor` (W16), `OutputGate`, `Supervisor`.
- Three unit tests pass on a clean build (reliability, gate, supervisor).
- No ROS dependency; 0 P0.

## W2 — ROS supervisor

- ROS 1 Noetic node `safety_supervisor`.
- Subscribes to image/LiDAR/odometry topics; publishes `/safety/state` and `/safety/odom`.
- A 10 Hz timer advances the supervisor when the estimator's odometry goes silent; this is required for R3LIVE, which stops publishing odometry when images stop.
- Synthetic-bag test passes: 62 state/odom messages, first DEGRADED at frame 16, first UNKNOWN at 26, final published x held at 1.5 m.
- 0 P0.

## W3 — offline equivalence

- `tools/replay_w16.py` reproduces the recorded W16 state sequence from the CSVs.
- m12e1 (p50=67): 2480 rows, mismatch 0, non-OK 2008.
- m12c1 (p50=1406.5): 2599 rows, mismatch 0, non-OK 2318.
- m12r1 (no `rel_state`): 1336 rows, non-OK 0.
- 0 P0.

## W4a — R3LIVE Level-A integration

- Input chain: 40 Hz camera → injector `hilti22_select10` (10 Hz) → Hilti adapter image; LiDAR `cloud_out`; odometry `/aft_mapped_to_init`.
- Clean exp18: 1033 odom/state/safety messages, all OK, hold=0; 10 Hz image chain has 1094 images/1094 clouds, |dt| p50 6.1 ms.
- Two earlier launches were technical-invalid (supervisor path; 40 Hz images bypassing the injector); the valid row is the third. W4a used 3 P0.
- Scope: Level-A wiring/recording only. Clean data cannot exercise UNKNOWN or hold.

## W4b — LVI-SAM Level-A integration

- LVI-SAM `0d822f6d`; OpenCV4/C++14 compatibility patch (7 files, 13 lines); GTSAM 4.0.3.
- Point cloud converter: Hesai PointCloud2 → PointXYZIRT (`ring` 0–31, relative `time`), rotated to IMU axes; translation is applied once through `extrinsicTrans`.
- IMU converter fills the zero quaternion with `(0,0,0,1)` because LVI-SAM rejects 6-axis IMUs; this is an interface placeholder, not an attitude measurement.
- Clean exp18: 538 odom/state/safety messages, all OK, hold=0. VINS reported 48 failure-detection/reboot events; only the LIO→supervisor publication chain is demonstrated.
- Two launches: first invalid (zero quaternion), second valid. W4b used 2 P0.

## W4c — degradation and hold across three systems

- Dropout: 3 s `[30,33)` for R3LIVE; 5 s `[30,35)` for LVI-SAM (3 s produced only 15 blind frames at ~5 Hz LIO, below the 17-frame UNKNOWN threshold).
- Pre-registered arms: hold=1 / hold=0, two repeats each; 12 P0 total (6 initial + 6 repeats; 2 repeat rows technical-invalid).
- R3LIVE: hold1 UNKNOWN 124/56 frames, `hold_disp=0`; hold0 UNKNOWN 124/58, output follows raw.
- LVI-SAM: hold1 UNKNOWN 17/18 frames, `hold_disp=0`; hold0 UNKNOWN 230/18, output follows raw.
- **Supported:** the mechanism triggers; a working hold freezes the published pose; no-hold follows raw.
- **Not supported:** stable UNKNOWN duration, effect size, recovery benefit, cross-system equivalence. Two repeats differ substantially (R3 hold1 124 vs 56; LVI hold0 230 vs 18).

## W5 — release package

- `safety_supervisor-0.3.2-w4c`; source tree in this repository; tar `822,191 B`, sha `aa44e594…`.
- Clean VM build: core 3/3, ROS node, `W3 PASS`, 121/121 checksums.
- 0 P0.

## Budget

Current accounting: **291/300** P0 used; 9 remaining (D 1 + G 8). W4c is 12 P0 (6 initial + 6 repeats). No new estimator run was added for W5.

## Evidence map

| Item | Path |
|---|---|
| W1 unit tests | `evidence/w1/` |
| W2 synthetic ROS bag | `evidence/w2/` |
| W3 replay | `evidence/w3/`, `data/w3/` |
| W4a clean/degradation | `evidence/w4a/`, `evidence/w4c/w4c_r3_*` |
| W4b clean/degradation | `evidence/w4b/`, `evidence/w4c/w4c_lvi_*` |
| Paper-facing tables | `data/paper/` |
| Reproduce | `REPRODUCE.md` |
