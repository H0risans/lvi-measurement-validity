#!/usr/bin/env python3
"""Summarize a W4b ROS bag: topic counts, supervisor states, odometry endpoints.

Usage: python3 summarize_w4b.py OUT_DIR [EXIT_CODE]
Reads OUT_DIR/w4b_topics.bag and writes OUT_DIR/run.json + OUT_DIR/summary.txt.
"""
import json
import os
import sys

import rosbag


def pos(msg):
    p = msg.pose.pose.position
    return [float(p.x), float(p.y), float(p.z)]


def main():
    if len(sys.argv) < 2:
        print("usage: summarize_w4b.py OUT_DIR [EXIT_CODE]", file=sys.stderr)
        return 2
    out = os.path.abspath(sys.argv[1])
    exit_code = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    bag_path = os.path.join(out, "w4b_topics.bag")
    counts = {}
    states = []
    holds = 0
    raw = []
    safety = []
    with rosbag.Bag(bag_path, "r") as bag:
        start = bag.get_start_time()
        end = bag.get_end_time()
        for topic, msg, _ in bag.read_messages(
            topics=["/lvi_sam/lidar/mapping/odometry", "/safety/state",
                    "/safety/odom", "/clock"]
        ):
            counts[topic] = counts.get(topic, 0) + 1
            if topic == "/safety/state":
                try:
                    d = json.loads(msg.data)
                except Exception:
                    d = {}
                states.append(d)
                if d.get("hold"):
                    holds += 1
            elif topic == "/lvi_sam/lidar/mapping/odometry":
                raw.append(pos(msg))
            elif topic == "/safety/odom":
                safety.append(pos(msg))

    state_counts = {}
    for d in states:
        s = str(d.get("state", "?"))
        state_counts[s] = state_counts.get(s, 0) + 1

    need = {
        "/lvi_sam/lidar/mapping/odometry": 500,
        "/safety/state": 500,
        "/safety/odom": 500,
    }
    missing = [t for t, n in need.items() if counts.get(t, 0) < n]
    valid = exit_code == 0 and not missing
    result = {
        "status": "done" if valid else "invalid",
        "valid": valid,
        "exit_code": exit_code,
        "bag": bag_path,
        "duration_s": round(float(end - start), 3),
        "counts": counts,
        "state_counts": state_counts,
        "hold_frames": holds,
        "raw_odom": len(raw),
        "safety_odom": len(safety),
        "first_raw": raw[0] if raw else None,
        "last_raw": raw[-1] if raw else None,
        "first_safety": safety[0] if safety else None,
        "last_safety": safety[-1] if safety else None,
        "missing": missing,
        "note": "clean W4b LVI-SAM adapter run; no accuracy or abstention claim",
    }
    with open(os.path.join(out, "run.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    lines = [
        "W4b summary",
        "valid=%s exit=%d duration=%.3f" % (valid, exit_code, end - start),
        "counts=" + json.dumps(counts, ensure_ascii=False),
        "states=" + json.dumps(state_counts, ensure_ascii=False),
        "hold_frames=%d" % holds,
        "first_raw=%s last_raw=%s" % (result["first_raw"], result["last_raw"]),
        "first_safety=%s last_safety=%s" % (result["first_safety"], result["last_safety"]),
        "missing=" + json.dumps(missing, ensure_ascii=False),
    ]
    with open(os.path.join(out, "summary.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
