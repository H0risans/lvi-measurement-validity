// test_supervisor.cpp -- synthetic sequence checks for the ROS-free supervisor.
#include <cmath>
#include <cstdio>
#include <vector>

#include <safety/supervisor.h>

namespace {
int failures = 0;
void check(bool ok, const char *what) {
  if (!ok) {
    std::printf("  [FAIL] %s\n", what);
    ++failures;
  }
}
safety::Pose poseAt(double x) {
  safety::Pose p;
  p.p[0] = x;
  p.q[3] = 1.0;
  return p;
}
}  // namespace

int main() {
  using safety::RelState;
  using safety::Supervisor;
  using safety::SupervisorConfig;
  using safety::SupervisorOutput;

  // 1. clean stream: image every frame, healthy LiDAR, never leaves OK.
  {
    Supervisor s;
    bool ever = false;
    for (int i = 0; i < 100; ++i) {
      s.notifyImage(i * 0.1);
      s.notifyLidar(2000);
      SupervisorOutput o = s.step(poseAt(i * 0.01));
      if (o.state != RelState::OK) ever = true;
    }
    check(!ever, "clean stream stays OK");
    check(s.monitor().degradeCount() == 0 && s.monitor().unknownCount() == 0, "clean counters zero");
    check(s.gate().holdFrames() == 0, "clean stream never holds");
  }

  // 2. visual outage: DEGRADED at the 7th blind frame, UNKNOWN at the 17th,
  //    and the gate freezes at the last OK pose.
  {
    SupervisorConfig cfg;
    cfg.hold_output = true;
    Supervisor s(cfg);
    for (int i = 0; i < 5; ++i) {
      s.notifyImage(i * 0.1);
      s.notifyLidar(2000);
      s.step(poseAt(1.0));
    }
    bool saw_degraded = false;
    int degraded_at = -1;
    int unknown_at = -1;
    for (int i = 0; i < 30; ++i) {
      SupervisorOutput o = s.step(poseAt(1.0));
      if (o.state == RelState::DEGRADED && !saw_degraded) {
        saw_degraded = true;
        degraded_at = i;
      }
      if (o.state == RelState::UNKNOWN && unknown_at < 0) unknown_at = i;
    }
    check(saw_degraded && degraded_at == 6, "DEGRADED on the 7th blind frame");
    check(unknown_at == 16, "UNKNOWN 10 frames after DEGRADED");
    check(s.gate().holdFrames() == 14, "hold starts at UNKNOWN");
    SupervisorOutput held = s.step(poseAt(9.0));
    check(held.gate.hold && held.gate.pose.p[0] == 1.0, "frozen at last OK pose");
  }

  // 3. recovery needs ten healthy frames; then the gate releases.
  {
    SupervisorConfig cfg;
    cfg.hold_output = true;
    Supervisor s(cfg);
    for (int i = 0; i < 5; ++i) {
      s.notifyImage(i * 0.1);
      s.notifyLidar(2000);
      s.step(poseAt(1.0));
    }
    for (int i = 0; i < 30; ++i) s.step(poseAt(2.0));
    check(s.state() == RelState::UNKNOWN, "precondition UNKNOWN");
    int resumed_at = -1;
    for (int i = 0; i < 12; ++i) {
      s.notifyImage(10.0 + i * 0.1);
      s.notifyLidar(2000);
      SupervisorOutput o = s.step(poseAt(5.0));
      if (o.state == RelState::OK) {
        resumed_at = i;
        check(!o.gate.hold && o.gate.pose.p[0] == 5.0, "released pose is raw");
        break;
      }
    }
    check(resumed_at == 9, "resumed on 10th healthy frame");
    check(s.gate().releaseCount() == 1, "one release");
    SupervisorOutput gap = s.step(poseAt(6.0));
    check(gap.outage_frames == 1 && gap.state == RelState::OK, "outage counter resets after recovery");
  }

  // 4. vision healthy but LiDAR vanishing escalates to UNKNOWN.
  {
    SupervisorConfig cfg;
    cfg.hold_output = true;
    Supervisor s(cfg);
    for (int i = 0; i < 5; ++i) {
      s.notifyImage(i * 0.1);
      s.notifyLidar(2000);
      s.step(poseAt(1.0));
    }
    int unknown_at = -1;
    for (int i = 0; i < 20; ++i) {
      s.notifyImage(10.0 + i * 0.1);
      s.notifyLidar(0);
      SupervisorOutput o = s.step(poseAt(2.0));
      if (o.state == RelState::UNKNOWN && unknown_at < 0) unknown_at = i;
    }
    check(unknown_at == 9, "LiDAR-only escalation on 10th poor frame");
    check(s.gate().holdFrames() > 0, "LiDAR escalation holds output");
  }

  // 5. same outage/lidar sequence as a direct monitor: states must match.
  {
    Supervisor s;
    safety::ReliabilityMonitor m;
    int of = 0;
    std::vector<double> lidar;
    for (int i = 0; i < 60; ++i) {
      bool image = (i < 10) || (i >= 30);
      bool lidar_ok = (i < 40);
      if (image) {
        s.notifyImage(i * 0.1);
        of = 0;
      } else {
        ++of;
      }
      int pts = lidar_ok ? 2000 : 0;
      s.notifyLidar(pts);
      SupervisorOutput o = s.step(poseAt(0.01 * i));
      RelState direct = m.update(of, static_cast<double>(pts));
      check(o.state == direct, "supervisor state matches direct monitor");
      if (o.state != direct) break;
    }
  }

  if (failures == 0) {
    std::printf("ALL CHECKS PASSED (0 failure(s))\n");
    return 0;
  }
  std::printf("%d CHECK(S) FAILED\n", failures);
  return 1;
}
