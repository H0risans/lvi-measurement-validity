#!/usr/bin/env python3
"""Check the synthetic ROS replay recorded by safety_ros/test/README.md.

The bag contains 40 odometry frames: 10 with an image, then 30 without; LiDAR
is healthy for the first 20 frames and empty afterwards.  With the default
W16 counters the supervisor must go OK -> DEGRADED -> UNKNOWN and then hold the
last OK pose (x=1.5 m).

The supervisor now also has a 10 Hz timer that advances its own clock when the
estimator stops publishing odometry.  That is required for estimators such as
R3LIVE, whose odometry stops exactly when images stop.  The timer can add
messages, so this check finds the state transitions rather than assuming a
fixed 40-message bag.
"""
import json
import sys

import rosbag


def main(bag_path):
    states = []
    odoms = []
    with rosbag.Bag(bag_path) as bag:
        for topic, msg, _ in bag.read_messages():
            if topic == "/safety/state":
                states.append(json.loads(msg.data))
            elif topic == "/safety/odom":
                odoms.append(msg)

    errors = []
    if len(states) < 40:
        errors.append("expected at least 40 state messages, got %d" % len(states))
    if len(odoms) < 40:
        errors.append("expected at least 40 odom messages, got %d" % len(odoms))

    first_deg = next((i for i, s in enumerate(states) if s.get("state") == "DEGRADED"), None)
    first_unk = next((i for i, s in enumerate(states) if s.get("state") == "UNKNOWN"), None)
    if first_deg is None:
        errors.append("no DEGRADED state")
    if first_unk is None:
        errors.append("no UNKNOWN state")
    if first_deg is not None and first_unk is not None and not (first_deg < first_unk):
        errors.append("DEGRADED must precede UNKNOWN")
    if first_unk is not None and not all(s.get("hold") for s in states[first_unk:]):
        errors.append("every frame from UNKNOWN onward must hold")
    if first_unk is not None and first_unk < len(states) - 1:
        # The last-OK anchor is x=1.5; both /safety/state and /safety/odom must
        # stay there after the transition.
        if not all(abs(o.pose.pose.position.x - 1.5) <= 1e-9 for o in odoms[first_unk:]):
            errors.append("held odometry left x=1.5 after UNKNOWN")
    if odoms:
        last_x = odoms[-1].pose.pose.position.x
        if abs(last_x - 1.5) > 1e-9:
            errors.append("last held x expected 1.5, got %.6f" % last_x)

    print("states=%d odoms=%d last_x=%.3f first_DEGRADED=%s first_UNKNOWN=%s" % (
        len(states), len(odoms),
        odoms[-1].pose.pose.position.x if odoms else float("nan"),
        first_deg, first_unk))
    for e in errors:
        print("FAIL:", e)
    if errors:
        return 1
    print("W2 PASS: synthetic ROS replay reaches DEGRADED/UNKNOWN and holds")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/safety_state.bag"))
