// supervisor.h -- ROS-free orchestration of reliability + output gate.
//
// The ROS node is a thin adapter around this class.  A caller notifies it
// about image and LiDAR observations, then calls step() once per odometry
// frame with the pose the estimator would publish.  This is the piece that
// makes the same supervision logic reusable across LIVO systems.
#ifndef SAFETY_CORE_SUPERVISOR_H
#define SAFETY_CORE_SUPERVISOR_H

#include <limits>

#include <safety/output_gate.h>
#include <safety/reliability.h>

namespace safety {

struct SupervisorConfig {
  RelConfig reliability;
  bool hold_output = false;
};

struct SupervisorOutput {
  RelState state = RelState::OK;
  GateOutput gate;
  int outage_frames = 0;
};

class Supervisor {
 public:
  Supervisor() {}
  explicit Supervisor(const SupervisorConfig &cfg) : cfg_(cfg), monitor_(cfg.reliability), gate_(cfg.hold_output) {}

  // Call from the image callback.  Consecutive images before the next
  // odometry frame collapse to a single "visual update present" event.
  void notifyImage(double /*stamp*/) { image_seen_ = true; }

  // Call from the LiDAR callback.  Pass 0 for an empty cloud; the value is
  // an adapter-level health count (raw points for Level A, effective
  // constraints for systems that expose them).
  void notifyLidar(int points) { lidar_points_ = points; }

  SupervisorOutput step(const Pose &raw) {
    int of = 0;
    if (image_seen_) {
      outage_frames_ = 0;
      of = 0;
      image_seen_ = false;
    } else {
      if (outage_frames_ < 1000000000) ++outage_frames_;
      of = outage_frames_;
    }

    double lidar = (lidar_points_ >= 0) ? static_cast<double>(lidar_points_)
                                        : std::numeric_limits<double>::quiet_NaN();
    RelState state = monitor_.update(of, lidar);
    GateOutput gate = gate_.update(state, raw);

    SupervisorOutput out;
    out.state = state;
    out.gate = gate;
    out.outage_frames = of;
    return out;
  }

  void reset() {
    monitor_.reset();
    gate_.reset();
    outage_frames_ = 0;
    image_seen_ = false;
    lidar_points_ = -1;
  }

  const SupervisorConfig &config() const { return cfg_; }
  RelState state() const { return monitor_.state(); }
  const ReliabilityMonitor &monitor() const { return monitor_; }
  const OutputGate &gate() const { return gate_; }

 private:
  SupervisorConfig cfg_;
  ReliabilityMonitor monitor_;
  OutputGate gate_;
  int outage_frames_ = 0;
  bool image_seen_ = false;
  int lidar_points_ = -1;
};

}  // namespace safety

#endif  // SAFETY_CORE_SUPERVISOR_H
