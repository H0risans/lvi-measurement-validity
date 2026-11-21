// safety_reliability_test.cpp -- offline checks for the W16 monitor (no ROS, no estimator).
#include <cmath>
#include <cstdio>
#include <limits>
#include <vector>

#include <safety/reliability.h>

namespace {
int failures = 0;
void check(bool ok, const char *what) {
  if (!ok) {
    std::printf("  [FAIL] %s\n", what);
    ++failures;
  }
}

const double kNan = std::numeric_limits<double>::quiet_NaN();

// Feed a run of (outage, lidar) frames and return the first time the state changes to want.
int firstFrame(const std::vector<std::pair<int, double> > &seq, safety::RelState want,
               safety::ReliabilityMonitor *out = nullptr) {
  safety::ReliabilityMonitor m;
  for (size_t i = 0; i < seq.size(); ++i) {
    safety::RelState s = m.update(seq[i].first, seq[i].second);
    if (s == want) {
      if (out) *out = m;
      return static_cast<int>(i);
    }
  }
  if (out) *out = m;
  return -1;
}
}  // namespace

int main() {
  using safety::RelState;

  // 1. defaults
  {
    safety::RelConfig c;
    check(c.n_outage == 5 && c.n_deg == 3 && c.n_unk == 10 && c.n_lidar_unk == 10 && c.n_res == 10,
          "default counters");
    check(c.lidar_p05 == 14.0 && c.lidar_p25 == 67.0 && c.lidar_p50 == 1406.5, "default healthy thresholds");
  }

  // 2. a clean run never leaves OK
  {
    std::vector<std::pair<int, double> > seq;
    for (int i = 0; i < 500; ++i) seq.push_back(std::make_pair(0, 1400.0));
    safety::ReliabilityMonitor m;
    bool ever = false;
    for (size_t i = 0; i < seq.size(); ++i)
      if (m.update(seq[i].first, seq[i].second) != RelState::OK) ever = true;
    check(!ever, "clean run stays OK");
    check(m.degradeCount() == 0 && m.unknownCount() == 0 && m.frozenFrames() == 0, "clean counters zero");
  }

  // 3. outage -> DEGRADED after 3 blind frames (of >= 5 outage frames)
  {
    std::vector<std::pair<int, double> > seq;
    for (int i = 0; i < 5; ++i) seq.push_back(std::make_pair(0, 1400.0));
    for (int i = 0; i < 20; ++i) seq.push_back(std::make_pair(9, 1700.0));  // lidar fine, vision blind
    check(firstFrame(seq, RelState::DEGRADED) == 7, "DEGRADED on the 3rd blind frame (index 5+2)");
  }

  // 4. DEGRADED -> UNKNOWN after 10 more blind frames
  {
    std::vector<std::pair<int, double> > seq;
    for (int i = 0; i < 5; ++i) seq.push_back(std::make_pair(0, 1400.0));
    for (int i = 0; i < 40; ++i) seq.push_back(std::make_pair(9, 1700.0));
    check(firstFrame(seq, RelState::UNKNOWN) == 17, "UNKNOWN 10 frames after DEGRADED");
  }

  // 5. a single-frame visual gap is not an outage
  {
    std::vector<std::pair<int, double> > seq;
    for (int i = 0; i < 3; ++i) seq.push_back(std::make_pair(4, 1400.0));
    for (int i = 0; i < 20; ++i) seq.push_back(std::make_pair(0, 1400.0));
    check(firstFrame(seq, RelState::DEGRADED) == -1, "outage below n_outage never degrades");
  }

  // 6. vision ticking but LiDAR vanishing escalates to UNKNOWN
  {
    std::vector<std::pair<int, double> > seq;
    for (int i = 0; i < 30; ++i) seq.push_back(std::make_pair(0, 1600.0));
    for (int i = 0; i < 20; ++i) seq.push_back(std::make_pair(0, 3.0));
    check(firstFrame(seq, RelState::UNKNOWN) == 39, "LiDAR-only escalation after 10 frames");
  }

  // 7. recovery needs 10 healthy frames
  {
    safety::ReliabilityMonitor m;
    for (int i = 0; i < 5; ++i) m.update(0, 1400.0);
    for (int i = 0; i < 20; ++i) m.update(9, 1700.0);
    check(m.state() == RelState::UNKNOWN, "precondition: UNKNOWN");
    int resumed_at = -1;
    for (int i = 0; i < 12; ++i)
      if (m.update(0, 1700.0) == RelState::OK) { resumed_at = i; break; }
    check(resumed_at == 9, "RESUMED on the 10th healthy frame");
    check(m.resumeCount() == 1, "resume counter");
  }

  // 8. frozen frames are counted only while UNKNOWN
  {
    safety::ReliabilityMonitor m;
    for (int i = 0; i < 5; ++i) m.update(0, 1400.0);
    for (int i = 0; i < 18; ++i) m.update(9, 1700.0);  // 2 degrade + 10 unknown + 6 more
    check(m.frozenFrames() > 0, "frozen frames counted");
    check(m.frozen(), "state is UNKNOWN");
    check(std::string(safety::relStateName(m.state())) == "UNKNOWN", "state name");
  }

  // 9. NaN lidar does not freeze or escalate by itself
  {
    std::vector<std::pair<int, double> > seq;
    for (int i = 0; i < 40; ++i) seq.push_back(std::make_pair(0, kNan));
    check(firstFrame(seq, RelState::UNKNOWN) == -1, "NaN lidar is neutral");
  }


  // 10. a resume needs the median healthy density, not just "not dead" (M13)
  {
    safety::ReliabilityMonitor m;
    for (int i = 0; i < 5; ++i) m.update(0, 1400.0);
    for (int i = 0; i < 20; ++i) m.update(9, 1700.0);
    check(m.state() == RelState::UNKNOWN, "precondition: UNKNOWN");
    bool resumed = false;
    for (int i = 0; i < 40; ++i)
      if (m.update(0, 900.0) == RelState::OK) resumed = true;  // above p25, below p50
    check(!resumed, "vision back with sub-median lidar does not resume");
  }

  if (failures == 0) {
    std::printf("ALL CHECKS PASSED (0 failure(s))\n");
    return 0;
  }
  std::printf("%d CHECK(S) FAILED\n", failures);
  return 1;
}
