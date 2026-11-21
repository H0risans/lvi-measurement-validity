#!/usr/bin/env python3
"""Print /safety/state + /safety/odom + raw odom timeline around W4c transitions."""
import json
import sys

import rosbag


def main(path):
    states, safety, raw = [], [], []
    with rosbag.Bag(path) as bag:
        for topic, msg, t in bag.read_messages():
            ts = t.to_sec()
            if topic == "/safety/state":
                states.append((ts, json.loads(msg.data)))
            elif topic == "/safety/odom":
                p = msg.pose.pose.position
                safety.append((ts, p.x, p.y, p.z, msg.header.stamp.to_sec()))
            elif topic == "/aft_mapped_to_init":
                p = msg.pose.pose.position
                raw.append((ts, p.x, p.y, p.z, msg.header.stamp.to_sec()))

    print("states=%d safety=%d raw=%d" % (len(states), len(safety), len(raw)))
    print("first state t=%.6f last=%.6f" % (states[0][0], states[-1][0]))
    print("first safety t=%.6f last=%.6f" % (safety[0][0], safety[-1][0]))
    trans = []
    prev = None
    for ts, s in states:
        st = s.get("state")
        if st != prev:
            trans.append((ts, st, s.get("hold"), s.get("outage_frames"), s.get("reason")))
            prev = st
    for x in trans[:20]:
        print("TRANS t=%.6f state=%s hold=%s outage=%s reason=%s" % x)

    # positions at each transition and within UNKNOWN window
    for ts, st, hold, outage, reason in trans:
        if st == "UNKNOWN":
            print("UNKNOWN start t=%.6f" % ts)
            for item in safety:
                if item[0] >= ts:
                    print(" first safety t=%.6f xyz=(%.4f,%.4f,%.4f) hdr=%.6f" % item)
                    break
            for item in raw:
                if item[0] >= ts:
                    print(" first raw    t=%.6f xyz=(%.4f,%.4f,%.4f) hdr=%.6f" % item)
                    break
            # print every 10th safety in hold window
            cnt = 0
            for item in safety:
                if item[0] >= ts:
                    if cnt % 10 == 0:
                        print("  s[%3d] t=%.6f xyz=(%.4f,%.4f,%.4f)" % (cnt, item[0], item[1], item[2], item[3]))
                    cnt += 1
            print("  safety in unknown from first: %d" % cnt)
            break

    # show safety around first unknown: 5 before/after
    unk_t = next((ts for ts, st, *_ in trans if st == "UNKNOWN"), None)
    if unk_t:
        idx = next(i for i, x in enumerate(safety) if x[0] >= unk_t)
        for j in range(max(0, idx - 5), min(len(safety), idx + 10)):
            item = safety[j]
            print("POS j=%d t=%.6f xyz=(%.4f,%.4f,%.4f)" % ((j,) + item[:4]))
    # last OK anchor: safety message just before unk
    if unk_t:
        before = [x for x in safety if x[0] < unk_t]
        if before:
            print("last pre-UNK safety: t=%.6f xyz=(%.4f,%.4f,%.4f)" % before[-1])


if __name__ == "__main__":
    main(sys.argv[1])
