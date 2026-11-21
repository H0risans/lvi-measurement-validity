#!/usr/bin/env python3
"""Offline equivalence check for the W16 reliability monitor.

This is the W3 tool: it re-runs the two-level state machine on a recorded
safety CSV and compares the result with the ``rel_state`` column that the
vehicle wrote online.  It has no ROS, estimator or third-party dependency.

Exit status is 0 only when the mismatch count is within --expect-mismatch
(default 0).  A CSV without a state column is allowed (e.g. the clean
reference run); use --expect-non-ok to assert that it never degrades.
"""
import argparse
import csv
import json
import math
import sys
from collections import Counter


DEFAULT_CFG = {
    "n_outage": 5,
    "n_deg": 3,
    "n_unk": 10,
    "n_lidar_unk": 10,
    "n_res": 10,
    "lidar_p05": 14.0,
    "lidar_p50": 1406.5,
}


class ReliabilityMonitor:
    def __init__(self, cfg):
        self.cfg = cfg
        self.state = "OK"
        self.deg = 0
        self.unk = 0
        self.lidar_bad = 0
        self.rec = 0

    def update(self, outage_frames, lidar_pts):
        c = self.cfg
        outage = outage_frames >= c["n_outage"]
        lidar_dead = not math.isnan(lidar_pts) and lidar_pts < c["lidar_p05"]
        healthy_vis = (outage_frames == 0) and (
            math.isnan(lidar_pts) or lidar_pts >= c["lidar_p50"]
        )

        if self.state == "OK":
            self.deg = self.deg + 1 if outage else 0
            if self.deg >= c["n_deg"]:
                self.state = "DEGRADED"
                self.deg = 0
                self.unk = 0
        elif self.state == "DEGRADED":
            if outage:
                self.unk += 1
                if self.unk >= c["n_unk"]:
                    self.state = "UNKNOWN"
                    self.rec = 0
            else:
                self.unk = 0
                self.rec = self.rec + 1 if healthy_vis else 0
                if self.rec >= c["n_res"]:
                    self.state = "OK"
                    self.rec = 0
        else:  # UNKNOWN
            self.rec = self.rec + 1 if healthy_vis else 0
            if self.rec >= c["n_res"]:
                self.state = "OK"
                self.rec = 0

        if self.state == "OK":
            self.lidar_bad = self.lidar_bad + 1 if lidar_dead else 0
            if self.lidar_bad >= c["n_lidar_unk"]:
                self.state = "UNKNOWN"
                self.lidar_bad = 0
                self.rec = 0
        else:
            self.lidar_bad = 0
        return self.state


def _float(value):
    if value is None or value == "":
        return float("nan")
    try:
        return float(value)
    except ValueError:
        return float("nan")


def _int(value, default=0):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def run(path, args):
    cfg = dict(DEFAULT_CFG)
    cfg.update(
        n_outage=args.n_outage,
        n_deg=args.n_deg,
        n_unk=args.n_unk,
        n_lidar_unk=args.n_lidar_unk,
        n_res=args.n_res,
        lidar_p05=args.p05,
        lidar_p50=args.p50,
    )
    monitor = ReliabilityMonitor(cfg)
    counts = Counter()
    mismatch = []
    transitions = []
    previous = None
    compared = 0
    rows = 0

    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise SystemExit("empty CSV: %s" % path)
        for row in reader:
            rows += 1
            outage = _int(row.get(args.outage_col), 0)
            lidar = _float(row.get(args.lidar_col))
            state = monitor.update(outage, lidar)
            counts[state] += 1
            if previous is not None and state != previous:
                transitions.append(
                    {
                        "t": row.get("t_vio", row.get("t_state", "")),
                        "from": previous,
                        "to": state,
                    }
                )
            previous = state

            if args.state_col and args.state_col in (reader.fieldnames or []):
                expected = (row.get(args.state_col) or "").strip().upper()
                if expected:
                    compared += 1
                    if expected != state:
                        mismatch.append(
                            {
                                "row": rows,
                                "t": row.get("t_vio", ""),
                                "expected": expected,
                                "got": state,
                                "outage_frames": outage,
                                "lidar_pts": lidar,
                            }
                        )

    result = {
        "file": str(path),
        "rows": rows,
        "compared": compared,
        "mismatches": len(mismatch),
        "first_mismatches": mismatch[:5],
        "states": dict(counts),
        "transitions": transitions,
        "p50": cfg["lidar_p50"],
        "p05": cfg["lidar_p05"],
        "has_state_column": bool(args.state_col and args.state_col in (reader.fieldnames or [])),
    }
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("csv", help="safety CSV with outage_frames/lidar_pts/rel_state")
    ap.add_argument("--state-col", default="rel_state")
    ap.add_argument("--outage-col", default="outage_frames")
    ap.add_argument("--lidar-col", default="lidar_pts")
    ap.add_argument("--p50", type=float, default=DEFAULT_CFG["lidar_p50"])
    ap.add_argument("--p05", type=float, default=DEFAULT_CFG["lidar_p05"])
    ap.add_argument("--n-outage", type=int, default=DEFAULT_CFG["n_outage"])
    ap.add_argument("--n-deg", type=int, default=DEFAULT_CFG["n_deg"])
    ap.add_argument("--n-unk", type=int, default=DEFAULT_CFG["n_unk"])
    ap.add_argument("--n-lidar-unk", type=int, default=DEFAULT_CFG["n_lidar_unk"])
    ap.add_argument("--n-res", type=int, default=DEFAULT_CFG["n_res"])
    ap.add_argument("--expect-mismatch", type=int, default=0)
    ap.add_argument("--expect-non-ok", type=int, default=None,
                    help="allowed non-OK frames (use 0 for a clean run)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    result = run(args.csv, args)
    ok = result["mismatches"] <= args.expect_mismatch
    non_ok = result["rows"] - result["states"].get("OK", 0)
    if args.expect_non_ok is not None:
        ok = ok and non_ok <= args.expect_non_ok
    result["non_ok"] = non_ok
    result["ok"] = ok

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("file: %s" % result["file"])
        print("rows=%d compared=%d mismatches=%d non_ok=%d p50=%g" %
              (result["rows"], result["compared"], result["mismatches"], non_ok, result["p50"]))
        print("states: %s" % json.dumps(result["states"], ensure_ascii=False))
        if result["first_mismatches"]:
            for m in result["first_mismatches"]:
                print("  mismatch row=%s t=%s expected=%s got=%s" %
                      (m["row"], m["t"], m["expected"], m["got"]))
        if result["transitions"]:
            print("transitions:")
            for tr in result["transitions"]:
                print("  t=%s %s -> %s" % (tr["t"], tr["from"], tr["to"]))
        print("RESULT: %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
