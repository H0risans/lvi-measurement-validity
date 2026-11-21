# W4a evidence (R3LIVE Level-A integration)

## Files

| File | Content |
|---|---|
| `launch_check.txt` | 0 P0: launch static check and VM `roslaunch --files` resolution |
| `calibration_exp18.csv` | 0 P0: 1094-frame `cloud_out` point-count quantiles for exp18 (p05=55,008 / p50=58,931) |
| `image_chain_summary.txt` | 0 P0: injector→adapter 10 Hz chain, images=1094, clouds=1094, \|dt\| p50=6.1 ms |
| `fix1/run.json` | Summary of the third (valid) clean run: done/valid/exit 0 |
| `fix1/adapter_audit.jsonl` | Per-frame adapter audit; after the fix image=1094, cloud=1094 |
| `fix1/vio_summary.txt` | R3LIVE VIO counts: 1094 callbacks, 1028 state updates, 6 skipped |

The recorded topic bag from the clean run is not committed; the multi-megabyte bag remains in the author's archive.

## clean exp18 result

- `/aft_mapped_to_init`, `/safety/odom` and `/safety/state` each **1033** messages.
- `state_counts = {"OK": 1033}`, no UNKNOWN/DEGRADED, `hold_frames = 0`.
- Across 993 paired frames, the maximum position difference between `/safety/odom` and raw odometry is **0.0 m**.
- Final position: `(-16.602989, 7.970427, -33.120181)`.

## Boundary

- A clean row does not trigger degradation; it cannot support a claim that "UNKNOWN hold was validated online."
- The 3 P0 include two technical-invalid runs (missing supervisor node; 40 Hz raw images bypassing the 10 Hz selection). The third run is valid.
- R3LIVE source is unchanged; only launch/remap and the 10 Hz image chain were added.
