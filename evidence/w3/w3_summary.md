# W3 offline-equivalence summary

Tool: `tools/replay_w16.py`; one-shot script: `tools/run_w3.sh`; per-file JSON is in `evidence/w3/`.

| CSV | p50 | rows | mismatch vs online `rel_state` | non-OK frames | state distribution |
|---|---:|---:|---:|---:|---|
| `m12e1_safety.csv` | 67.0 (old p25 rule) | 2480 | 0 | 2008 | OK 472 / DEGRADED 20 / UNKNOWN 1988 |
| `m12c1/m12c1_safety.csv` | 1406.5 (v2) | 2599 | 0 | 2318 | OK 281 / DEGRADED 10 / UNKNOWN 2308 |
| `m12r1_safety.csv` | 1406.5 (clean reference) | 1336 | no `rel_state` column | 0 | OK 1336 |

Key transitions (m12e1): 28.4352 s OK-to-DEGRADED, 29.4352 s DEGRADED-to-UNKNOWN, 35.5348 s UNKNOWN-to-OK, 54.6336 s OK-to-DEGRADED, 55.6335 s DEGRADED-to-UNKNOWN.

Key transitions (m12c1): 28.4352 s OK-to-DEGRADED, 29.4352 s DEGRADED-to-UNKNOWN; no recovery before the sequence ends.

Notes:

- The online CSV for `m12e1` was recorded with the old p25 resume rule; only `p50=67` reproduces its labels frame by frame. The default `p50=1406.5` does not match.
- `m12r1` has no `rel_state` column; it can only show that a clean run does not escalate, not provide a label comparison.
- The result only shows that the offline W16 replay matches the online labels recorded at the time. It does not validate output hold, R3LIVE or LVI-SAM online behavior.
