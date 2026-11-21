# Dependencies

The release was built and tested on the following baseline.  Newer versions
may work but are not claimed.

## Host

| Component | Version |
|---|---|
| OS | Ubuntu 20.04 (Focal) |
| Compiler | g++ 9.4.0 |
| CMake | 3.16.3 |
| Python | 3.8 (system) |
| ROS | Noetic Ninjemys (optional for core/offline check) |

## C++ libraries

| Library | Version | Used by |
|---|---|---|
| PCL | 1.10 | LVI-SAM / R3LIVE adapters (external) |
| OpenCV | 4.2.0 | LVI-SAM / R3LIVE adapters (external) |
| Ceres | 1.14.0 | LVI-SAM (external) |
| GTSAM | 4.0.3 | LVI-SAM (external) |
| Eigen | 3.3 | transitively |

Install the common packages:

```bash
sudo apt-get update
sudo apt-get install -y build-essential cmake python3 \
  libpcl-dev libopencv-dev libceres-dev
```

GTSAM 4.0.3 was installed from `ppa:borglab/gtsam-release-4.0`:

```bash
sudo add-apt-repository ppa:borglab/gtsam-release-4.0
sudo apt-get update
sudo apt-get install -y libgtsam-dev libgtsam-unstable-dev
```

## ROS packages

For `safety_ros`:

```bash
sudo apt-get install -y ros-noetic-roscpp ros-noetic-sensor-msgs \
  ros-noetic-nav-msgs ros-noetic-std-msgs
```

For the external LVI-SAM adaptation (not built by `build_clean.sh`):

```bash
sudo apt-get install -y ros-noetic-cv-bridge ros-noetic-image-transport \
  ros-noetic-pcl-ros ros-noetic-tf ros-noetic-tf2-ros
```

The LVI-SAM upstream tree must be obtained separately at commit
`0d822f6dcac3378312f6703b4f45829e049f221a`; apply
`adapters/lvisam/patches/opencv4_cxx14.patch` before building.  R3LIVE must be
obtained at commit `6143a38537f28cb36eb24e9bbe2e39c8f7967157` and built with
the Hilti22 adapter option described in `docs/W4a_接入记录_20261119.md`.

## Python

The offline replay and summarizers use only the Python standard library plus
the ROS `rosbag` module when reading bags:

- `python3` ≥ 3.8
- `rosbag` from ROS Noetic for `summarize_w4a.py`, `summarize_w4b.py`,
  `summarize_degradation.py` and `tools/inspect_w4c_bag.py`
- `numpy` is pulled in by ROS message helpers; no pinned version is required
  for the offline CSV replay

`tools/replay_w16.py` and `run_offline_smoke.sh` need **no** ROS and no
third-party Python packages.

## Data not included

The HILTI22 bags are not redistributed.  Their sizes and SHA-256 values are in
`MANIFEST.yaml`:

- exp18: 8,657,654,860 B, `98373b52f207b9ace3914792b5604a6642f89441190cabca6acbaf1d17249280`
- exp14: 6.26 GB (see `MANIFEST.yaml`)

The three small W3 CSVs are included under `data/w3/` so the offline check is
self-contained.
