#!/usr/bin/env python3
"""Convert Hilti22 Hesai XT32 scans to the field contract expected by LVI-SAM.

Input  : /hesai/pandar (sensor_msgs/PointCloud2), fields x,y,z,intensity,timestamp,ring
Output : /lvisam/points (sensor_msgs/PointCloud2), fields x,y,z,intensity,ring,time

The output points are expressed in a "virtual LiDAR" frame: same origin as the
Hesai LiDAR, axes aligned with the Hilti IMU (R_IL from the existing Hilti
adapter). LVI-SAM then uses extrinsicTrans=[-0.001,-0.00855,0.055] and an
identity rotation; no point is translated twice.

This node performs no selection/fault injection. Feed it the raw 10 Hz Hesai
stream; camera selection is done by camera_fault_injector.
"""
import copy
import numpy as np
import rospy
from sensor_msgs.msg import PointCloud2, PointField

# Hilti22 Hesai XT32 -> IMU rotation, same constant as hilti_r3live_adapter.
R_IL = np.array([[0.0, -1.0, 0.0],
                 [-1.0, 0.0, 0.0],
                 [0.0, 0.0, -1.0]], dtype=np.float64)
RING_MAX = 32

# PCL PointXYZIRT layout: 4 floats, uint16 ring, float time, padded to 24 bytes.
OUT_DTYPE = np.dtype({
    "names": ["x", "y", "z", "intensity", "ring", "time"],
    "formats": ["<f4", "<f4", "<f4", "<f4", "<u2", "<f4"],
    "offsets": [0, 4, 8, 12, 16, 20],
    "itemsize": 24,
})
OUT_FIELDS = [
    PointField("x", 0, PointField.FLOAT32, 1),
    PointField("y", 4, PointField.FLOAT32, 1),
    PointField("z", 8, PointField.FLOAT32, 1),
    PointField("intensity", 12, PointField.FLOAT32, 1),
    PointField("ring", 16, PointField.UINT16, 1),
    PointField("time", 20, PointField.FLOAT32, 1),
]


class Converter(object):
    def __init__(self):
        self.input_topic = rospy.get_param("~input_topic", "/hesai/pandar")
        self.output_topic = rospy.get_param("~output_topic", "/lvisam/points")
        self.frame_id = rospy.get_param("~frame_id", "hilti_lidar_imu_axes")
        self.max_rel_s = float(rospy.get_param("~max_rel_s", 0.2))
        self.n_scan = int(rospy.get_param("~n_scan", 32))
        if self.n_scan != RING_MAX:
            raise ValueError("this adapter is frozen for Hesai XT32 (32 rings)")
        self.pub = rospy.Publisher(self.output_topic, PointCloud2, queue_size=5)
        self.sub = rospy.Subscriber(self.input_topic, PointCloud2, self.callback,
                                    queue_size=5, buff_size=16000000)
        self.count = 0
        rospy.loginfo("converter: %s -> %s", self.input_topic, self.output_topic)

    def _structured(self, msg):
        fields = {f.name: f for f in msg.fields}
        required = ["x", "y", "z", "intensity", "timestamp", "ring"]
        missing = [n for n in required if n not in fields]
        if missing:
            raise ValueError("missing Hesai fields: %s" % ",".join(missing))
        allowed = {"x": 7, "y": 7, "z": 7, "intensity": 7, "timestamp": 8, "ring": 4}
        for name in required:
            if fields[name].datatype != allowed[name] or fields[name].count != 1:
                raise ValueError("unexpected field type for %s" % name)
        endian = ">" if msg.is_bigendian else "<"
        dtype = np.dtype({
            "names": required,
            "formats": [endian + "f4"] * 4 + [endian + "f8", endian + "u2"],
            "offsets": [fields[n].offset for n in required],
            "itemsize": msg.point_step,
        })
        return np.ndarray((msg.height, msg.width), dtype=dtype, buffer=msg.data,
                          strides=(msg.row_step, msg.point_step)).reshape(-1)

    def callback(self, msg):
        try:
            data = self._structured(msg)
            if data.size == 0:
                rospy.logwarn_throttle(5.0, "empty Hesai scan; skip")
                return
            if np.any(data["ring"] >= RING_MAX):
                raise ValueError("ring outside Hesai XT32 range")
            xyz = np.column_stack([data["x"], data["y"], data["z"]]).astype(np.float64)
            if not np.isfinite(xyz).all():
                raise ValueError("non-finite point coordinates")
            rel = data["timestamp"].astype(np.float64) - msg.header.stamp.to_sec()
            if rel.min() < -0.002 or rel.max() > self.max_rel_s:
                raise ValueError("scan time support [%.4f, %.4f] outside [0, %.2f] s"
                                 % (rel.min(), rel.max(), self.max_rel_s))
            xyz = xyz @ R_IL.T
            out = np.zeros(data.size, dtype=OUT_DTYPE)
            out["x"], out["y"], out["z"] = xyz[:, 0], xyz[:, 1], xyz[:, 2]
            out["intensity"] = data["intensity"].astype("<f4")
            out["ring"] = data["ring"].astype("<u2")
            out["time"] = rel.astype("<f4")

            result = PointCloud2()
            result.header = copy.deepcopy(msg.header)
            result.header.frame_id = self.frame_id
            result.height = 1
            result.width = data.size
            result.is_bigendian = False
            result.is_dense = True
            result.fields = OUT_FIELDS
            result.point_step = OUT_DTYPE.itemsize
            result.row_step = result.point_step * result.width
            result.data = out.tobytes()
            self.pub.publish(result)
            self.count += 1
            if self.count % 100 == 0:
                rospy.loginfo("converted scans=%d points=%d rel=[%.4f,%.4f]",
                              self.count, data.size, rel.min(), rel.max())
        except Exception as exc:  # fail closed: never forward an invented scan
            rospy.logerr_throttle(5.0, "Hesai->LVI-SAM conversion rejected: %s", exc)


if __name__ == "__main__":
    rospy.init_node("hilti_lvisam_cloud")
    Converter()
    rospy.spin()
