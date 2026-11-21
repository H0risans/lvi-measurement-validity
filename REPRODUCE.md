# Reproduce this snapshot

This file is the release-level quick path.  Experiment commands, pre-registration rules and expected counts are in `docs/EXPERIMENTS.md` and the adapter READMEs.

## A. Core build and offline check (no ROS, no estimator)

```bash
./build_clean.sh
./run_offline_smoke.sh
```

Expected:

- `ctest` → `100% tests passed, 0 tests failed out of 3`
- replay → `W3 PASS: all three replays within tolerance`

The replay reads only `data/w3/` and needs Python 3.  It compares the offline
W16 state machine with `rel_state` recorded online:

| Data | Rule | Rows | Mismatch | Non-OK |
|---|---|---:|---:|---:|
| `m12e1_safety.csv` | p50=67 (old p25 recovery) | 2480 | 0 | 2008 |
| `m12c1/m12c1_safety.csv` | p50=1406.5 | 2599 | 0 | 2318 |
| `m12r1_safety.csv` | p50=1406.5, no rel_state column | 1336 | 0 | 0 |

## B. ROS node build (optional)

```bash
./build_clean.sh --with-ros
source build/ws/devel/setup.bash
```

Expected binary:
`build/ws/devel/lib/safety_supervisor/supervisor_node`.

Synthetic test (starts its own roscore on port 11312, no estimator):

```bash
source build/ws/devel/setup.bash
./safety_ros/test/run_synth_test.sh
```

Expected: `states=62 odoms=62 last_x=1.500 first_DEGRADED=16
first_UNKNOWN=26` and `W2 PASS`.

## C. Recorded experiment rows (not runnable without bags/estimators)

W4a/W4b/W4c require the HILTI22 bags, R3LIVE/LVI-SAM source trees and a GPU
host.  They are **not** part of this release build.  The exact commands,
pre-registration rules and expected counts are in `docs/EXPERIMENTS.md`; the concise results are in:

- `docs/EXPERIMENTS.md`
- `evidence/w4a/`, `evidence/w4b/`, `evidence/w4c/`

The W4a/W4b/W4c rows consumed 17 P0 in total (W4c 12 after repeats); this release itself consumes
**0 P0** and starts no estimator.

## D. Checksums

```bash
sha256sum -c SHA256SUMS
```

`MANIFEST.yaml` records upstream commits, data hashes and per-file hashes.
