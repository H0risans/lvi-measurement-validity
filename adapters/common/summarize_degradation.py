#!/usr/bin/env python3
"""Summarize one W4c degradation run from its recorded rosbag.

This script is deliberately small and read-only: it never starts a node and
never changes an estimator.  It is used after run_w4a_bag.sh / run_w4b_bag.sh
to turn /safety/state, /safety/odom and the raw estimator odometry into the
few numbers fixed by the W4c pre-registration (section 0.9).
"""
import argparse
import json
import math
import os
import sys

import rosbag


def _iter(bag, topic):
    for _, msg, t in bag.read_messages(topics=[topic]):
        yield t.to_sec(), msg


def _pos(msg):
    p = msg.pose.pose.position
    return [float(p.x), float(p.y), float(p.z)]


def _dist(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def _state(msg):
    try:
        obj = json.loads(msg.data)
    except Exception:
        return {}
    return obj if isinstance(obj, dict) else {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--bag", default="")
    ap.add_argument("--odom-topic", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--hold-arm", type=int, choices=[0, 1], required=True)
    ap.add_argument("--play-rc", type=int, default=0)
    ap.add_argument("--min-odom", type=int, default=500)
    args = ap.parse_args()

    bag_path = args.bag or os.path.join(args.out, "w4c_topics.bag")
    odom = []
    safety = []
    states = []
    raw_by_header = {}
    safety_by_header = []
    if os.path.exists(bag_path):
        with rosbag.Bag(bag_path, "r") as bag:
            odom = [(t, _pos(m)) for t, m in _iter(bag, args.odom_topic)]
            safety = [(t, _pos(m)) for t, m in _iter(bag, "/safety/odom")]
            states = [(t, _state(m)) for t, m in _iter(bag, "/safety/state")]
            for _, m in _iter(bag, args.odom_topic):
                raw_by_header[round(m.header.stamp.to_sec(), 9)] = _pos(m)
            for _, m in _iter(bag, "/safety/odom"):
                safety_by_header.append((round(m.header.stamp.to_sec(), 9), _pos(m)))

    reasons = []
    if args.play_rc != 0:
        reasons.append("play_rc=%d" % args.play_rc)
    if len(odom) < args.min_odom:
        reasons.append("odom=%d<%d" % (len(odom), args.min_odom))
    if len(states) < args.min_odom:
        reasons.append("state=%d<%d" % (len(states), args.min_odom))
    if len(safety) < args.min_odom:
        reasons.append("safety_odom=%d<%d" % (len(safety), args.min_odom))

    seq = [(t, s.get("state", ""), bool(s.get("hold", False)),
            int(s.get("outage_frames", 0) or 0), str(s.get("reason", "")))
           for t, s in states]
    counts = {}
    for _, st, _, _, _ in seq:
        counts[st] = counts.get(st, 0) + 1
    hold_frames = sum(1 for _, _, h, _, _ in seq if h)

    transitions = []
    for i in range(1, len(seq)):
        if seq[i][1] != seq[i - 1][1]:
            transitions.append({"t": round(seq[i][0], 3),
                                "from": seq[i - 1][1], "to": seq[i][1]})
    first_deg = next((t for t, st, _, _, _ in seq if st == "DEGRADED"), None)
    first_unk = next((t for t, st, _, _, _ in seq if st == "UNKNOWN"), None)
    first_ok_after_unk = None
    for t, st, _, _, _ in seq:
        if first_unk is not None and t > first_unk and st == "OK":
            first_ok_after_unk = t
            break

    if "DEGRADED" not in counts:
        reasons.append("no_DEGRADED")
    if "UNKNOWN" not in counts:
        reasons.append("no_UNKNOWN")
    if args.hold_arm and hold_frames == 0:
        reasons.append("hold_arm_has_no_hold")
    if not args.hold_arm and hold_frames != 0:
        reasons.append("nohold_arm_has_hold")

    # Envelope and hold displacement.  During UNKNOWN, a correct hold arm keeps
    # the published position exactly constant; the no-hold arm follows raw.
    def envelope(track):
        return max((_dist(p, track[0][1]) for _, p in track), default=0.0)

    raw_env = envelope(odom)
    safety_env = envelope(safety)
    start = odom[0][1] if odom else [0, 0, 0]
    hold_window = []
    if first_unk is not None:
        end = first_ok_after_unk if first_ok_after_unk is not None else 1e18
        # Exclude the exact release sample: first_ok_after_unk is the first
        # post-UNKNOWN state, and its safety odom already carries the new raw
        # pose.  Including it makes a correct hold look like a 9 m jump.
        hold_window = [(t, p) for t, p in safety if first_unk <= t < end]
    hold_disp = 0.0
    if len(hold_window) >= 2:
        hold_disp = max(_dist(p, hold_window[0][1]) for _, p in hold_window)

    # Pair safety odom with the exact raw sample by header stamp.  The
    # supervisor copies the last odom message (including its header) and only
    # replaces the pose; bag-time nearest matching can cross a callback/timer
    # race and compare against a newer raw sample.
    pairs = []
    for h, p in safety_by_header:
        if h in raw_by_header:
            pairs.append(_dist(p, raw_by_header[h]))
    pair_max = max(pairs, default=0.0)
    if len(pairs) < len(safety_by_header):
        # Timestamp rewriting in a recorder should not happen; keep this visible.
        pair_max = max(pair_max, 1e9)
    if args.hold_arm and first_unk is not None and len(hold_window) >= 2 and hold_disp > 1e-9:
        reasons.append("hold_arm_output_moved=%.6g" % hold_disp)
    if not args.hold_arm and pairs and pair_max > 1e-6:
        reasons.append("nohold_arm_differs=%.6g" % pair_max)

    result = {
        "label": args.label,
        "status": "done" if not reasons else "invalid",
        "valid": not reasons,
        "invalid_reasons": reasons,
        "bag": bag_path,
        "counts": {"odom": len(odom), "safety_odom": len(safety), "state": len(states)},
        "state_counts": counts,
        "hold_frames": hold_frames,
        "first_DEGRADED_s": round(first_deg, 3) if first_deg is not None else None,
        "first_UNKNOWN_s": round(first_unk, 3) if first_unk is not None else None,
        "first_OK_after_UNKNOWN_s": round(first_ok_after_unk, 3) if first_ok_after_unk is not None else None,
        "hold_displacement_m": hold_disp,
        "raw_envelope_m": raw_env,
        "safety_envelope_m": safety_env,
        "safety_raw_pair_max_m": pair_max,
        "transitions": transitions,
        "first_raw": start,
        "last_raw": odom[-1][1] if odom else None,
        "last_safety": safety[-1][1] if safety else None,
    }

    with open(os.path.join(args.out, "degradation.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    lines = [
        "%s: %s" % (args.label, result["status"]),
        "counts: odom=%d safety=%d state=%d" % (len(odom), len(safety), len(states)),
        "state_counts: %s" % json.dumps(counts, ensure_ascii=False, sort_keys=True),
        "first DEGRADED=%s UNKNOWN=%s OK_after=%s" % (
            result["first_DEGRADED_s"], result["first_UNKNOWN_s"],
            result["first_OK_after_UNKNOWN_s"]),
        "hold_frames=%d hold_disp=%.9g m raw_env=%.6g safety_env=%.6g" % (
            hold_frames, hold_disp, raw_env, safety_env),
        "invalid_reasons=%s" % ",".join(reasons),
    ]
    with open(os.path.join(args.out, "degradation.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if not reasons else 1


if __name__ == "__main__":
    sys.exit(main())
