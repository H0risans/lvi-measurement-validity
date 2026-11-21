# lvi-measurement-validity

Research code and derived data for **measurement-validity assessment** in tightly coupled LiDAR–visual–inertial odometry (LIVO). The repository accompanies the manuscript:

> *When Is a Visual Measurement Still Valid? Event-Level Injection and Output Hold in Tightly Coupled LiDAR–Visual–Inertial Odometry*

It contains the external supervisor (`safety_core` + `safety_ros`), the injection/exposure/evaluation tooling, Level-A adapters for FAST-LIVO2, R3LIVE and LVI-SAM, the W16 reliability state machine, and the derived tables/figures used by the paper.

The supervisor only observes ROS topics. It never writes back into the estimator, never changes W16 thresholds, and never broadcasts TF. `hold_output` is disabled by default.

## What is here

| Path | Content |
|---|---|
| `safety_core/` | Pure C++14 W16 state machine, `OutputGate`, `Supervisor`; no ROS dependency |
| `safety_ros/` | ROS 1 Noetic `supervisor_node`, launch file, synthetic-bag test |
| `adapters/r3live/` | R3LIVE launch/remap, runner, static checks |
| `adapters/lvisam/` | LVI-SAM launch/config, point-cloud and IMU converters, OpenCV4 build patch |
| `adapters/common/` | Degradation runner, dropout configs, summarizer |
| `manifests/` | Per-system adapter manifests |
| `data/w3/` | Three safety CSVs for the offline W16 equivalence check |
| `data/content_replay/` | Eight content-replay runs: run metadata, event tables, safety CSVs, trajectories |
| `data/hold/` | Six online output-hold runs and summary |
| `data/degradation/` | W4c degradation summaries and dropout-chain evidence |
| `data/paper/` | Paper-facing derived tables (content replay, hold, degradation) |
| `figs/` | Final English SVG/PDF figures and their generator |
| `docs/` | W0 baseline, W4a/W4b/W4c records, full engineering route |
| `evidence/` | W1–W4 evidence summaries and small test artifacts |
| `MANIFEST.yaml` | Release/baseline/file hashes and P0 accounting |
| `REPRODUCE.md` | Reproduction commands and expected numbers |

HILTI22 bags (multi-GB), upstream source trees, and built binaries are **not** redistributed.

## Quick start

Requirements: Ubuntu 20.04, CMake ≥ 3.16, a C++14 compiler, Python 3.8. ROS Noetic is optional for the core/offline check.

```bash
./build_clean.sh                 # safety_core + ctest
./run_offline_smoke.sh           # core build + W3 replay, expects "W3 PASS"
```

With ROS Noetic:

```bash
./build_clean.sh --with-ros      # catkin build of the supervisor node
```

The full experiment matrix requires the HILTI22 bags and the three estimator builds; see `REPRODUCE.md` and `DEPENDENCIES.md`.

## Data and paper mapping

`data/paper/` contains the derived values behind the paper's tables:

- `content_replay_runs.csv` — eight full-frame replay runs (exp14/exp18 × 3 s/6 s × 2 repeats): APE, 1 s RPE, zero-distribution half-span, harm flag.
- `hold_runs.csv` — six online output-hold runs: first UNKNOWN, published envelope, frozen fraction, internal/published final positions.
- `degradation_runs.csv` — eleven W4c/adapter runs: state counts, first DEGRADED/UNKNOWN/OK-after, hold frames, hold displacement, raw/safety envelopes.

`data/content_replay/<tag>/` holds the per-run `run.json`, `fault_events.csv`, `safety_risk.csv` and estimator trajectory. `data/degradation/<tag>/` holds the degradation JSON and the recorded topic bag only where retained; multi-GB raw bags are not included.

The paper's data statement should point to this repository at the tag below. If a DOI is required, archive the tagged release with Zenodo and replace the repository URL in the manuscript with the DOI.

## Scope and limitations

- The reported evidence covers one FAST-LIVO2 build for the main mechanism experiments, plus Level-A clean/degradation integrations for R3LIVE and LVI-SAM.
- The three systems share the decision/abstention contract, **not** a verified cross-system mechanism. No cross-system accuracy comparison is made.
- W4c has two repeats per arm. Hold displacement is reproducible; UNKNOWN duration and published envelope vary substantially between repeats. Do not report stable durations, effect sizes, or recovery benefits.
- `lidar_p05`/`lidar_p50` in the examples are calibrated per system; the FAST-LIVO2 values are not transferable to R3LIVE/LVI-SAM.
- The clean runs do not exercise UNKNOWN/hold; they only verify the Level-A chain.
- The LVI-SAM patch is build-compatibility only and does not change the estimation method.

## Reproduction

See `REPRODUCE.md` for:

1. core build and unit tests;
2. ROS build and synthetic-bag test;
3. W3 offline replay equivalence;
4. W4a/W4b/W4c run commands and acceptance criteria;
5. release checksums.

Expected W3 result: `m12e1` 2480 rows / mismatch 0 / non-OK 2008; `m12c1` 2599 / 0 / 2318; `m12r1` 1336 / 0 / 0.

## Citation

Citation metadata is in `CITATION.cff`. Update author names/affiliations before publication; the current entry uses the repository handle.

## License

Original code and documentation are released under the MIT License (see `LICENSE`). The LVI-SAM OpenCV4/C++14 patch is a derivative of the upstream GPL-3.0 source and remains under GPL-3.0; see `NOTICE.md`. Upstream projects retain their own licenses.
