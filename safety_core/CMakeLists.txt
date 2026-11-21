cmake_minimum_required(VERSION 3.10)
project(safety_core CXX)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(safety_core STATIC
  src/output_gate.cpp
)
target_include_directories(safety_core PUBLIC
  ${CMAKE_CURRENT_SOURCE_DIR}/include
)
target_compile_options(safety_core PRIVATE -Wall -Wextra -pedantic)

enable_testing()
foreach(test_name test_reliability test_output_gate test_supervisor)
  add_executable(${test_name} tests/${test_name}.cpp)
  target_link_libraries(${test_name} PRIVATE safety_core)
  target_compile_options(${test_name} PRIVATE -Wall -Wextra -pedantic)
  add_test(NAME ${test_name} COMMAND ${test_name})
endforeach()
