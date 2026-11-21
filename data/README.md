# Data

This directory contains the derived data used by the manuscript and the small inputs needed for the offline W16 equivalence check. HILTI22 raw bags and upstream estimator source trees are not redistributed.

## Layout

```
data/
  w3/                 three safety CSVs for the offline W16 replay check
  content_replay/     eight full-frame content-replay runs (exp14/exp18 x 3 s/6 s x 2)
  hold/               six online output-hold runs and the summary table
  degradation/        W4c degradation summaries and the dropout-chain test
  paper/              paper-facing derived tables
```

### `data/w3/`

`m12e1_safety.csv`, `m12c1_safety.csv`, `m12r1_safety.csv` are the inputs to `tools/run_w3.sh`. The expected replay results are:

| input | rows | mismatch | non-OK |
|---|---:|---:|---:|
| m12e1 (p50=67) | 2480 | 0 | 2008 |
| m12c1 (p50=1406.5) | 2599 | 0 | 2318 |
| m12r1 (no rel_state) | 1336 | 0 | 0 |

### `data/content_replay/`

One directory per run: `run.json`, `fault_events.csv`, `safety_risk.csv` and the estimator trajectory `exp14.txt` or `exp18.txt`. The runs are the eight rows of Table 3A and the content-replay rows of Table 2.

### `data/hold/`

`a_results.csv` is the six-row online output-hold table used for Table 4: publish envelope, frozen fraction, internal final position and paired raw/safety comparison. `a_summary.md` is the human-readable summary.

### `data/degradation/`

`<tag>/degradation.json` reports counts, state counts, first DEGRADED/UNKNOWN/OK-after, hold frames, hold displacement and raw/safety envelopes for the W4c runs. `dropout_chain_test/` contains the injector+adapter-only test proving the intended 3 s image gap. Topic `.bag` files are intentionally omitted from the repository; the JSON summaries carry the values used in the paper.

## `data/paper/`

These CSVs are generated from the run records above:

- `content_replay_runs.csv`: `tag, seq, dose, rep, valid, ape_m, rpe1s_m, rpe_delta, rpe_halfspan, harm`.
- `hold_runs.csv`: the six-row hold table (`tag, first_unknown_s, first_resume_s, n_unknown_entries, pub_env_m, pub_first50_s, frozen_frac, pub_final_m, internal_final_m, max_div_10s_m, pub_rows, internal_rows`).
- `degradation_runs.csv`: `label, status, valid, odom, safety_odom, state, OK, DEGRADED, UNKNOWN, hold_frames, first_DEGRADED_s, first_UNKNOWN_s, first_OK_after_UNKNOWN_s, hold_displacement_m, raw_envelope_m, safety_envelope_m`.

## Units and conventions

- APE/RPE in metres; 1 s RPE is the translation RPE over 1 s windows on the [30,45) s segment.
- `rpe_delta` is the run's 1 s RPE minus the same-sequence 24-run reference median; `rpe_halfspan` is half the reference range (exp14 0.0002 m/s, exp18 0.0111 m/s).
- `hold_displacement_m` is the maximum displacement of the **published** pose during `[first_UNKNOWN, first_OK_after)`; it is 0 for a working hold and nonzero for the no-hold control.
- `raw_envelope_m` and `safety_envelope_m` are maximum displacement from the start of the evaluated segment for the raw estimator pose and the supervisor output.
- `frozen_frac` is the fraction of published messages after first UNKNOWN that repeat the held pose.

## Provenance

- `data/content_replay/` contains the eight content-replay runs (trajectory, run summary, fault events, safety CSV).
- `data/hold/` contains the six online hold runs (`a_results.csv`, `a_summary.md`).
- `data/degradation/` contains the W4c degradation summaries and logs, with multi-GB bags removed.

See `../MANIFEST.yaml` for baseline commits and `../REPRODUCE.md` for commands.
