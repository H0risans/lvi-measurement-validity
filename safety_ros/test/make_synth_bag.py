#!/usr/bin/env python3
"""Build the synthetic bag used by the W2 acceptance test."""
import rosbag
import rospy
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Image, PointCloud2


def main(path="/tmp/safety_synth.bag"):
    bag = rosbag.Bag(path, "w")
    try:
        for i in range(40):
            t = rospy.Time.from_sec(0.1 * i)
            if i < 10:
                img = Image()
                img.header.stamp = t
                img.header.frame_id = "cam"
                img.height = 1
                img.width = 1
                img.encoding = "mono8"
                img.step = 1
                img.data = b"\x00"
                bag.write("/fault_injector/image_raw", img, t)

            pc = PointCloud2()
            pc.header.stamp = t + rospy.Duration(0.02)
            pc.header.frame_id = "lidar"
            if i < 20:
                pc.height = 1
                pc.width = 2000
                pc.point_step = 16
                pc.row_step = 32000
            else:
                pc.height = 0
                pc.width = 0
                pc.point_step = 16
                pc.row_step = 0
            bag.write("/livox/lidar", pc, t + rospy.Duration(0.02))

            od = Odometry()
            od.header.stamp = t + rospy.Duration(0.05)
            od.header.frame_id = "map"
            od.pose.pose.position.x = 0.1 * i
            od.pose.pose.orientation.w = 1.0
            bag.write("/aft_mapped_to_init", od, t + rospy.Duration(0.05))
    finally:
        bag.close()
    print("wrote", path)


if __name__ == "__main__":
    main()
