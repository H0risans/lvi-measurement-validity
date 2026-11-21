#include <safety/output_gate.h>

namespace safety {

GateOutput OutputGate::update(RelState state, const Pose &raw) {
  GateOutput out;
  out.pose = raw;
  out.reason = "ok";

  if (state == RelState::OK) {
    if (was_holding_) {
      ++release_count_;
      was_holding_ = false;
    }
    last_ok_ = raw;
    have_last_ok_ = true;
    return out;
  }

  if (state == RelState::DEGRADED) {
    // The monitor can move UNKNOWN -> DEGRADED in principle; be safe and
    // release the hold rather than freezing on a non-UNKNOWN state.
    if (was_holding_) {
      ++release_count_;
      was_holding_ = false;
    }
    out.reason = "degraded";
    return out;
  }

  // UNKNOWN
  if (!hold_output_) {
    out.reason = "hold_disabled";
    return out;
  }
  if (!have_last_ok_) {
    out.reason = "no_last_ok";
    return out;
  }

  out.hold = true;
  out.pose = last_ok_;
  out.reason = "hold_unknown";
  was_holding_ = true;
  ++hold_frames_;
  return out;
}

}  // namespace safety
