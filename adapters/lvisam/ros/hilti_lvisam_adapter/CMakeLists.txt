cmake_minimum_required(VERSION 3.0.2)
project(hilti_lvisam_adapter)

find_package(catkin REQUIRED COMPONENTS rospy sensor_msgs std_msgs)

catkin_package()

catkin_install_python(PROGRAMS
  scripts/point_cloud_converter.py
  scripts/imu_converter.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch config
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
