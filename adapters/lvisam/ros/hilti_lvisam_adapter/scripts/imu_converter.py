#!/usr/bin/env python3
"""Hilti 6-axis IMU -> LVI-SAM-compatible 9-axis message.

LVI-SAM's imuConverter rejects messages whose orientation quaternion has a
norm below 0.1 ("Invalid quaternion, please use a 9-axis IMU!").  The Hilti
IMU is 6-axis and leaves orientation at (0,0,0,0).  This adapter republishes
the same measurements with a unit quaternion when the input is invalid.

The filled orientation is a placeholder, not an attitude measurement.  It is
only there to satisfy LVI-SAM's interface; attitude/deskew initialized from it
is not trustworthy and must not be used as an accuracy claim.
"""
import rospy
from sensor_msgs.msg import Imu


class ImuConverter:
    def __init__(self):
        self.input_topic = rospy.get_param("~input_topic", "/alphasense/imu")
        self.output_topic = rospy.get_param("~output_topic", "/lvisam/imu")
        self.frame_id = rospy.get_param("~frame_id", "")
        self.filled = 0
        self.passed = 0
        self.pub = rospy.Publisher(self.output_topic, Imu, queue_size=100)
        self.sub = rospy.Subscriber(self.input_topic, Imu, self.callback,
                                    queue_size=200, buff_size=65536)

    def callback(self, msg):
        q = msg.orientation
        norm2 = q.x * q.x + q.y * q.y + q.z * q.z + q.w * q.w
        out = msg
        if norm2 < 0.01:
            out.orientation.x = 0.0
            out.orientation.y = 0.0
            out.orientation.z = 0.0
            out.orientation.w = 1.0
            self.filled += 1
        else:
            self.passed += 1
        if self.frame_id:
            out.header.frame_id = self.frame_id
        self.pub.publish(out)
        n = self.filled + self.passed
        if n % 1000 == 0:
            rospy.loginfo("imu_converter: %d msgs (%d filled, %d passed)",
                          n, self.filled, self.passed)


if __name__ == "__main__":
    rospy.init_node("hilti_lvisam_imu")
    ImuConverter()
    rospy.spin()
