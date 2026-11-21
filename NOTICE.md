# NOTICE

This is a research snapshot assembled for reproducibility. It does not
redistribute the source trees or binaries of FAST-LIVO2, R3LIVE, LVI-SAM,
GTSAM, Ceres, PCL, OpenCV, Eigen, or ROS.

## Licensing of this repository

Original code and documentation in this repository
(`safety_core/`, `safety_ros/`, `tools/`, `adapters/` except the LVI-SAM
patch) are released under the MIT License; see `LICENSE`.

`adapters/lvisam/patches/opencv4_cxx14.patch` is a build-compatibility patch
against the upstream LVI-SAM tree. It contains context from the upstream
GPL-3.0 source and is distributed under GPL-3.0, not MIT. It does not change
the estimation method.

The derived data in `data/` are provided for research reproducibility. The
HILTI22 raw data remain subject to their own terms and are not included.

## Upstream components

Upstream components retain their own licenses and copyright notices:

- FAST-LIVO2: https://github.com/hku-mars/FAST-LIVO2
- R3LIVE: https://github.com/hku-mars/r3live
- LVI-SAM: https://github.com/TixiaoShan/LVI-SAM
- GTSAM: https://github.com/borglab/gtsam
- Ceres Solver: https://github.com/ceres-solver/ceres-solver
- PCL: https://github.com/PointCloudLibrary/pcl
- OpenCV: https://github.com/opencv/opencv
- ROS: https://www.ros.org/

Do not assume that the presence of this snapshot grants rights to redistribute
the upstream projects.
