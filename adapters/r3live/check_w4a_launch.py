#!/usr/bin/env python3
"""Static checks for the W4a R3LIVE launch.  Does not start ROS or any estimator."""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

EXPECTED = {
    "image_topic": "/r3live_hilti_adapter/image_out",
    "lidar_topic": "/r3live_hilti_adapter/cloud_out",
    "odom_topic": "/aft_mapped_to_init",
    "state_topic": "/safety/state",
    "odom_out_topic": "/safety/odom",
}


def resolve(value, args):
    if value.startswith("$(arg ") and value.endswith(")"):
        return args.get(value[6:-1], value)
    return value


def main(path):
    root = ET.parse(path).getroot()
    assert root.tag == "launch", "root must be <launch>"
    args = {a.attrib["name"]: a.attrib.get("value", a.attrib.get("default", ""))
            for a in root if a.tag == "arg"}

    includes = [n for n in root if n.tag == "include"]
    assert len(includes) == 1, "expected exactly one included R3LIVE launch"
    inc = includes[0]
    assert inc.attrib["file"].endswith("hilti_r3live.launch"), inc.attrib["file"]

    nodes = [n for n in root if n.tag == "node"]
    assert len(nodes) == 1, "expected exactly one supervisor node"
    node = nodes[0]
    assert node.attrib["pkg"] == "safety_supervisor"
    assert node.attrib["type"] == "supervisor_node"

    params = {p.attrib["name"]: resolve(p.attrib["value"], args)
              for p in node if p.tag == "param"}
    for key, want in EXPECTED.items():
        got = params.get(key)
        assert got == want, "%s: expected %r, got %r" % (key, want, got)
    assert params.get("hold_output") in ("true", "false")
    assert params.get("lidar_p05") and params.get("lidar_p50")

    # No TF broadcaster in this launch; the supervisor must not compete with R3LIVE.
    assert not any(n.tag == "node" and "tf" in n.attrib.get("type", "") for n in root)
    print("W4a launch OK: %s" % Path(path).name)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "r3live_with_supervisor.launch"))
