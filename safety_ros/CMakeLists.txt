cmake_minimum_required(VERSION 3.0.2)
project(safety_supervisor)

find_package(catkin REQUIRED COMPONENTS
  roscpp
  sensor_msgs
  nav_msgs
  std_msgs
)

catkin_package()

include_directories(
  ${catkin_INCLUDE_DIRS}
  ${CMAKE_CURRENT_SOURCE_DIR}/../safety_core/include
)

add_executable(supervisor_node
  src/supervisor_node.cpp
  ../safety_core/src/output_gate.cpp
)

target_link_libraries(supervisor_node ${catkin_LIBRARIES})
add_dependencies(supervisor_node ${catkin_EXPORTED_TARGETS})
