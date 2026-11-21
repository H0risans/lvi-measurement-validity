# Changelog

## 0.3.2-w4c (2026-11-20)

- Refresh W4c after one repeat per arm (n=2).  No estimator code or W16
  thresholds changed; W4c goes from 6 to 12 P0 and the ledger from 285/300
  to 291/300.
- Update `docs/EXPERIMENTS.md`, `ADAPTERS.md`, per-system manifests and
  `MANIFEST.yaml` with the repeat rows.  Hold freeze reproduces in all four
  valid hold rows (`hold_disp=0`), but UNKNOWN duration/envelope vary widely;
  no stability or effect-size claim is made.
- Rebuild the package from the refreshed staging tree and re-run the clean
  core/ROS build and offline W3 smoke.
## 0.3.1-w4c (2026-11-19)

- Add W4c degradation records for R3LIVE and LVI-SAM: dropout injection,
  `UNKNOWN` transition, hold-on/hold-off pairs, `hold_disp=0` for hold arms.
- Add 10 Hz supervisor timer so a silent estimator odometry does not blind the
  monitor; W2 synthetic test now checks state transitions rather than a fixed
  message count.
- Add degradation summarizer with header-stamp pairing and a strict
  `[first_UNKNOWN, first_OK_after)` hold window.
- Add LVI-SAM ROS 1 external IMU converter (unit-quaternion placeholder for
  Hilti's 6-axis IMU), point-cloud converter, and 6-node launch stack.
- Add three-LIVO `ADAPTERS.md` + per-system manifests; W4c complete (6 P0).

## 0.3.0-w4c (2026-11-19)

- Add W4c adapter matrix: FAST-LIVO2, R3LIVE, LVI-SAM.
- Add R3LIVE Level-A launch/remap and 10 Hz image chain.
- Add LVI-SAM build/adaptation, OpenCV4/C++14 patch, Hilti22 converters.

## 0.2.1-w4b (2026-11-19)

- Add LVI-SAM clean exp18 support and external IMU converter.
- Record 538 odometry/state messages; VINS reboot limitation documented.

## 0.2.0-w4a (2026-11-19)

- Add R3LIVE Level-A adapter, 10 Hz injector→adapter chain, exp18 LiDAR
  calibration (`p05=55008`, `p50=58931`).
- Record 1033 state/odom messages, all `OK`.

## 0.1.0-w0-w3 (2026-11-18)

- First `safety_core` + `safety_ros` release.
- W1: three no-ROS unit tests.
- W2: synthetic bag supervisor test.
- W3: offline W16 equivalence against m12e1/m12c1/m12r1.
