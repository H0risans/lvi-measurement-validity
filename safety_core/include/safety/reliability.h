// safety_reliability.h -- W16 two-level reliability decision (pure C++, no ROS).
//
// Rules (v2, revised 2026-11-15 from the M12 reference run):
//   DEGRADED : outage_frames >= n_outage (0.5 s without any visual update) for n_deg frames
//   UNKNOWN  : still degraded for n_unk more frames, or lidar_pts < lidar_p05 for n_lidar_unk frames
//   RESUMED  : outage_frames == 0 and lidar_pts >= lidar_p50 for n_res frames
//
// Healthy reference (exp14 m12r1, 1336 frames, instrument only):
//   lidar_pts p05 = 14, p25 = 67, p50 = 1406.5.
// Resume uses p50 (median healthy density), not p25: with p25 the exp15 run resumed at
// 35.5 s while still degrading and the frozen output drifted to 50.4 m (M12b offline replay, 0 P0).
// The window thresholds are frame counts, not wall clock, so the decision does not depend on
// scheduler jitter. No state is ever modified here: the monitor only reports a level.
#ifndef SAFETY_CORE_RELIABILITY_H
#define SAFETY_CORE_RELIABILITY_H

#include <cmath>
#include <cstdint>
#include <limits>
#include <string>

namespace safety {

enum class RelState { OK = 0, DEGRADED = 1, UNKNOWN = 2 };

inline const char *relStateName(RelState s) {
  switch (s) {
    case RelState::OK: return "OK";
    case RelState::DEGRADED: return "DEGRADED";
    case RelState::UNKNOWN: return "UNKNOWN";
  }
  return "OK";
}

struct RelConfig {
  int n_outage = 5;       // outage_frames >= n_outage counts as a blind frame
  int n_deg = 3;          // consecutive blind frames to enter DEGRADED
  int n_unk = 10;         // further degraded frames to enter UNKNOWN
  int n_lidar_unk = 10;   // consecutive lidar-poor frames that escalate to UNKNOWN
  int n_res = 10;         // consecutive healthy frames to come back to OK
  double lidar_p05 = 14.0;
  double lidar_p25 = 67.0;    // kept for reporting only
  double lidar_p50 = 1406.5;  // resume reference: return to median healthy density
};

class ReliabilityMonitor {
 public:
  ReliabilityMonitor() {}
  explicit ReliabilityMonitor(const RelConfig &c) : cfg_(c) {}

  void reset() {
    state_ = RelState::OK;
    deg_ = 0;
    unk_ = 0;
    lidar_bad_ = 0;
    rec_ = 0;
    n_degrade_ = 0;
    n_unknown_ = 0;
    n_resume_ = 0;
    n_frozen_ = 0;
  }

  // of: consecutive frames without any visual measurement (from the safety FSM)
  // lidar_pts: effective LiDAR constraint count of this frame (NaN if unknown)
  RelState update(int of, double lidar_pts) {
    const bool outage = (of >= cfg_.n_outage);
    const bool lidar_dead = (lidar_pts == lidar_pts) && (lidar_pts < cfg_.lidar_p05);
    const bool healthy_vis = (of == 0) && ((lidar_pts != lidar_pts) || (lidar_pts >= cfg_.lidar_p50));

    if (state_ == RelState::OK) {
      deg_ = outage ? (deg_ + 1) : 0;
      if (deg_ >= cfg_.n_deg) {
        state_ = RelState::DEGRADED;
        deg_ = 0;
        unk_ = 0;
        ++n_degrade_;
      }
    } else if (state_ == RelState::DEGRADED) {
      if (outage) {
        ++unk_;
        if (unk_ >= cfg_.n_unk) {
          state_ = RelState::UNKNOWN;
          rec_ = 0;
          ++n_unknown_;
        }
      } else {
        unk_ = 0;
        rec_ = healthy_vis ? (rec_ + 1) : 0;
        if (rec_ >= cfg_.n_res) {
          state_ = RelState::OK;
          rec_ = 0;
          ++n_resume_;
        }
      }
    } else {  // UNKNOWN
      rec_ = healthy_vis ? (rec_ + 1) : 0;
      if (rec_ >= cfg_.n_res) {
        state_ = RelState::OK;
        rec_ = 0;
        ++n_resume_;
      }
    }

    // Independent escalation: vision may still tick, but LiDAR has almost vanished.
    if (state_ == RelState::OK) {
      lidar_bad_ = lidar_dead ? (lidar_bad_ + 1) : 0;
      if (lidar_bad_ >= cfg_.n_lidar_unk) {
        state_ = RelState::UNKNOWN;
        lidar_bad_ = 0;
        rec_ = 0;
        ++n_unknown_;
      }
    } else {
      lidar_bad_ = 0;
    }

    if (state_ == RelState::UNKNOWN) ++n_frozen_;
    return state_;
  }

  RelState state() const { return state_; }
  bool frozen() const { return state_ == RelState::UNKNOWN; }
  int degradeCount() const { return n_degrade_; }
  int unknownCount() const { return n_unknown_; }
  int resumeCount() const { return n_resume_; }
  int frozenFrames() const { return n_frozen_; }
  const RelConfig &config() const { return cfg_; }

 private:
  RelConfig cfg_;
  RelState state_ = RelState::OK;
  int deg_ = 0;
  int unk_ = 0;
  int lidar_bad_ = 0;
  int rec_ = 0;
  int n_degrade_ = 0;
  int n_unknown_ = 0;
  int n_resume_ = 0;
  int n_frozen_ = 0;
};

}  // namespace safety

#endif  // SAFETY_CORE_RELIABILITY_H
