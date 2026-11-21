#!/usr/bin/env python3
"""Summarize one W4a R3LIVE+supervisor bag into JSON (no estimator)."""
import argparse
import json
import rosbag


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bag", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--bag-sha", default="")
    ap.add_argument("--bag-bytes", type=int, default=0)
    ap.add_argument("--play-exit", type=int, default=0)
    ap.add_argument("--p05", type=float, required=True)
    ap.add_argument("--p50", type=float, required=True)
    ap.add_argument("--hold", type=int, default=1)
    ap.add_argument("--start-utc", default="")
    args = ap.parse_args()

    n_state = n_odom_out = n_odom_raw = 0
    state_counts = {}
    hold_frames = 0
    transitions = []
    last_state = None
    final_raw = None
    final_out = None
    invalid = []

    bag = rosbag.Bag(args.bag, "r")
    try:
        for topic, msg, t in bag.read_messages(
                topics=["/safety/state", "/safety/odom", "/aft_mapped_to_init"]):
            if topic == "/safety/state":
                n_state += 1
                try:
                    rec = json.loads(msg.data)
                except Exception:
                    continue
                st = str(rec.get("state", ""))
                state_counts[st] = state_counts.get(st, 0) + 1
                if bool(rec.get("hold", False)):
                    hold_frames += 1
                if st != last_state:
                    transitions.append({"t": round(t.to_sec(), 6), "state": st})
                    last_state = st
            elif topic == "/safety/odom":
                n_odom_out += 1
                final_out = [msg.pose.pose.position.x, msg.pose.pose.position.y,
                             msg.pose.pose.position.z]
            else:
                n_odom_raw += 1
                final_raw = [msg.pose.pose.position.x, msg.pose.pose.position.y,
                             msg.pose.pose.position.z]
    finally:
        bag.close()

    if args.play_exit != 0:
        invalid.append("rosbag_play_exit_%d" % args.play_exit)
    if n_odom_raw < 1000:
        invalid.append("raw_odom_lt_1000")
    if n_state < 1000:
        invalid.append("state_lt_1000")
    if n_odom_out < 1000:
        invalid.append("safety_odom_lt_1000")

    out = {
        "tag": args.tag,
        "status": "done" if not invalid else "invalid",
        "valid": not invalid,
        "invalid_reasons": invalid,
        "bag": args.bag,
        "bag_sha256": args.bag_sha,
        "bag_bytes": args.bag_bytes,
        "start_utc": args.start_utc,
        "play_exit": args.play_exit,
        "exit_code": 0,
        "settle_timeout": 0,
        "lidar_p05": args.p05,
        "lidar_p50": args.p50,
        "hold_output": bool(args.hold),
        "counts": {
            "state": n_state,
            "safety_odom": n_odom_out,
            "raw_odom": n_odom_raw,
        },
        "state_counts": state_counts,
        "hold_frames": hold_frames,
        "transitions": transitions,
        "final_raw_odom": final_raw,
        "final_safety_odom": final_out,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
