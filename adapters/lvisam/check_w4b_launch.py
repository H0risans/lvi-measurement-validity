#!/usr/bin/env python3
"""Static W4b check: adapter package, launch graph, configs, and fail-closed rules.

No ROS and no estimator. Run from the repository root:
    python3 工程化/adapters/lvisam/check_w4b_launch.py
"""
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))  # 工程化/adapters/lvisam -> 工程化
PKG = os.path.join(HERE, "ros", "hilti_lvisam_adapter")
FAIL = []


def check(cond, msg):
    if cond:
        print("OK   " + msg)
    else:
        FAIL.append(msg)
        print("FAIL " + msg)


def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def strip_comments(text):
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def main():
    files = [
        os.path.join(PKG, "package.xml"),
        os.path.join(PKG, "CMakeLists.txt"),
        os.path.join(PKG, "scripts", "point_cloud_converter.py"),
        os.path.join(PKG, "scripts", "imu_converter.py"),
        os.path.join(PKG, "launch", "hilti_lvisam_cloud.launch"),
        os.path.join(PKG, "launch", "lvisam_hilti.launch"),
        os.path.join(PKG, "launch", "lvisam_hilti_stack.launch"),
        os.path.join(PKG, "config", "params_lidar_hilti.yaml"),
        os.path.join(PKG, "config", "params_camera_hilti.yaml"),
        os.path.join(HERE, "patches", "opencv4_cxx14.patch"),
    ]
    for f in files:
        check(os.path.isfile(f), "exists: " + os.path.relpath(f, ROOT))

    for f in [p for p in files if p.endswith(".launch")]:
        try:
            ET.parse(f)
            check(True, "XML parses: " + os.path.basename(f))
        except Exception as exc:
            check(False, "XML parses: %s (%s)" % (os.path.basename(f), exc))

    stack = strip_comments(read(os.path.join(PKG, "launch", "lvisam_hilti_stack.launch")))
    for token in [
        'pkg="camera_fault_injector"',
        'pkg="hilti_r3live_adapter"',
        'pkg="safety_supervisor"',
        '$(find hilti_lvisam_adapter)/launch/hilti_lvisam_cloud.launch',
        '$(find hilti_lvisam_adapter)/launch/lvisam_hilti.launch',
        'type="imu_converter.py"',
        'output_topic" value="/lvisam/imu"',
        'image_topic" value="/r3live_hilti_adapter/image_out"',
        'lidar_topic" value="/lvisam/points"',
        'odom_topic" value="/lvi_sam/lidar/mapping/odometry"',
        '~image_in" to="/fault_injector/image_raw"',
    ]:
        check(token in stack, "stack contains " + token)
    check("r3live_mapping" not in stack, "no R3LIVE estimator in W4b stack")
    check("rviz" not in stack.lower(), "no RViz node in stack")

    lvisam = strip_comments(read(os.path.join(PKG, "launch", "lvisam_hilti.launch")))
    for node_type in [
        "lvi_sam_imuPreintegration",
        "lvi_sam_imageProjection",
        "lvi_sam_featureExtraction",
        "lvi_sam_mapOptmization",
        "lvi_sam_visual_feature",
        "lvi_sam_visual_odometry",
    ]:
        check('type="%s"' % node_type in lvisam, "LVI-SAM node " + node_type)
    check("lvi_sam_visual_loop" not in lvisam, "visual loop is not launched")

    cloud = strip_comments(read(os.path.join(PKG, "launch", "hilti_lvisam_cloud.launch")))
    check('pkg="hilti_lvisam_adapter"' in cloud, "converter package in cloud launch")
    check('type="point_cloud_converter.py"' in cloud, "converter node type")

    lidar = read(os.path.join(PKG, "config", "params_lidar_hilti.yaml"))
    for pat, name in [
        (r'pointCloudTopic:\s*"/lvisam/points"', "pointCloudTopic"),
        (r'imuTopic:\s*"/lvisam/imu"', "imuTopic"),
        (r'N_SCAN:\s*32', "N_SCAN=32"),
        (r'Horizon_SCAN:\s*1800', "Horizon_SCAN=1800"),
        (r'loopClosureEnableFlag:\s*false', "loop closure disabled"),
        (r'extrinsicTrans:\s*\[-0\.001,\s*-0\.00855,\s*0\.055\]', "T_IL"),
    ]:
        check(re.search(pat, lidar) is not None, "lidar config: " + name)

    cam = read(os.path.join(PKG, "config", "params_camera_hilti.yaml"))
    for pat, name in [
        (r'model_type:\s*PINHOLE', "PINHOLE"),
        (r'image_topic:\s*"/r3live_hilti_adapter/image_out"', "image topic"),
        (r'fisheye:\s*0', "fisheye off"),
        (r'loop_closure:\s*0', "loop closure off"),
        (r'extrinsicRotation:\s*!!opencv-matrix', "R_IC matrix"),
        (r'k1:\s*0\.0', "zero distortion"),
    ]:
        check(re.search(pat, cam) is not None, "camera config: " + name)

    conv = read(os.path.join(PKG, "scripts", "point_cloud_converter.py"))
    check("R_IL" in conv and "itemsize" in conv and "rejected" in conv,
          "converter has transform, explicit layout and fail-closed path")
    check('"/lvisam/points"' in conv, "converter default output /lvisam/points")

    imu = read(os.path.join(PKG, "scripts", "imu_converter.py"))
    check("orientation.w = 1.0" in imu and "norm2 < 0.01" in imu,
          "IMU converter fills only invalid orientation")

    print("\nW4b static check: %s" % ("PASS" if not FAIL else "FAIL (%d)" % len(FAIL)))
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
