// output_gate.h -- output abstention gate (pure C++, no ROS).
//
// The gate is deliberately independent of the estimator.  It holds the last
// pose that was published while the reliability monitor reported OK, and only
// holds while the monitor reports UNKNOWN.  It never feeds anything back into
// the estimator, so enabling it cannot change the internal trajectory.
#ifndef SAFETY_CORE_OUTPUT_GATE_H
#define SAFETY_CORE_OUTPUT_GATE_H

#include <string>

#include <safety/reliability.h>

namespace safety {

struct Pose {
  double stamp = 0.0;
  double p[3] = {0.0, 0.0, 0.0};
  double q[4] = {0.0, 0.0, 0.0, 1.0};  // x, y, z, w
};

struct GateOutput {
  bool hold = false;
  Pose pose;
  std::string reason;
};

class OutputGate {
 public:
  explicit OutputGate(bool hold_output = false) : hold_output_(hold_output) {}

  void setHoldOutput(bool enabled) { hold_output_ = enabled; }
  bool holdOutput() const { return hold_output_; }

  // state: reliability decision for this frame.
  // raw:   pose the estimator would have published without the gate.
  GateOutput update(RelState state, const Pose &raw);

  bool hasLastOk() const { return have_last_ok_; }
  const Pose &lastOk() const { return last_ok_; }
  int holdFrames() const { return hold_frames_; }
  int releaseCount() const { return release_count_; }

  void reset() {
    have_last_ok_ = false;
    last_ok_ = Pose();
    was_holding_ = false;
    hold_frames_ = 0;
    release_count_ = 0;
  }

 private:
  bool hold_output_ = false;
  bool have_last_ok_ = false;
  Pose last_ok_;
  bool was_holding_ = false;
  int hold_frames_ = 0;
  int release_count_ = 0;
};

}  // namespace safety

#endif  // SAFETY_CORE_OUTPUT_GATE_H
