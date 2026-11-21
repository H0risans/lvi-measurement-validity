// test_output_gate.cpp -- offline checks for the output abstention gate.
#include <cmath>
#include <cstdio>

#include <safety/output_gate.h>

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
  p.p[1] = 0.0;
  p.p[2] = 0.0;
  p.q[0] = 0.0;
  p.q[1] = 0.0;
  p.q[2] = 0.0;
  p.q[3] = 1.0;
  return p;
}
}  // namespace

int main() {
  using safety::GateOutput;
  using safety::OutputGate;
  using safety::Pose;
  using safety::RelState;

  // 1. disabled gate is pass-through and still tracks the last OK pose.
  {
    OutputGate g(false);
    GateOutput a = g.update(RelState::OK, poseAt(1.0));
    check(!a.hold && a.pose.p[0] == 1.0, "disabled gate passes OK");
    GateOutput b = g.update(RelState::UNKNOWN, poseAt(2.0));
    check(!b.hold && b.pose.p[0] == 2.0, "disabled gate passes UNKNOWN");
    check(g.hasLastOk() && g.lastOk().p[0] == 1.0, "last OK tracked");
    check(g.holdFrames() == 0 && g.releaseCount() == 0, "disabled counters");
  }

  // 2. hold on UNKNOWN, freeze exactly at the last OK pose.
  {
    OutputGate g(true);
    g.update(RelState::OK, poseAt(1.0));
    GateOutput h1 = g.update(RelState::UNKNOWN, poseAt(2.0));
    check(h1.hold && h1.pose.p[0] == 1.0, "first UNKNOWN holds last OK");
    check(h1.pose.q[3] == 1.0, "held quaternion copied");
    GateOutput h2 = g.update(RelState::UNKNOWN, poseAt(3.0));
    check(h2.hold && h2.pose.p[0] == 1.0, "repeated UNKNOWN stays frozen");
    check(g.holdFrames() == 2, "hold frame counter");
  }

  // 3. release on OK, publish raw pose, update last OK.
  {
    OutputGate g(true);
    g.update(RelState::OK, poseAt(1.0));
    g.update(RelState::UNKNOWN, poseAt(2.0));
    GateOutput r = g.update(RelState::OK, poseAt(5.0));
    check(!r.hold && r.pose.p[0] == 5.0, "OK releases and passes raw pose");
    check(g.releaseCount() == 1, "release counter");
    check(g.lastOk().p[0] == 5.0, "last OK updated on release");
    GateOutput h = g.update(RelState::UNKNOWN, poseAt(6.0));
    check(h.hold && h.pose.p[0] == 5.0, "next hold uses new anchor");
  }

  // 4. DEGRADED does not hold; if it interrupts a hold, it releases.
  {
    OutputGate g(true);
    g.update(RelState::OK, poseAt(1.0));
    g.update(RelState::UNKNOWN, poseAt(2.0));
    GateOutput d = g.update(RelState::DEGRADED, poseAt(3.0));
    check(!d.hold && d.pose.p[0] == 3.0, "DEGRADED passes raw pose");
    check(d.reason == "degraded", "DEGRADED reason");
    check(g.releaseCount() == 1, "DEGRADED releases a hold");
  }

  // 5. UNKNOWN before any OK: no anchor, do not fabricate a pose.
  {
    OutputGate g(true);
    GateOutput h = g.update(RelState::UNKNOWN, poseAt(4.0));
    check(!h.hold && h.pose.p[0] == 4.0, "no anchor passes raw pose");
    check(h.reason == "no_last_ok", "no anchor reason");
  }

  // 6. reset forgets anchor and counters.
  {
    OutputGate g(true);
    g.update(RelState::OK, poseAt(1.0));
    g.update(RelState::UNKNOWN, poseAt(2.0));
    g.reset();
    check(!g.hasLastOk() && g.holdFrames() == 0 && g.releaseCount() == 0, "reset clears state");
    GateOutput h = g.update(RelState::UNKNOWN, poseAt(7.0));
    check(!h.hold && h.pose.p[0] == 7.0, "after reset no anchor");
  }

  if (failures == 0) {
    std::printf("ALL CHECKS PASSED (0 failure(s))\n");
    return 0;
  }
  std::printf("%d CHECK(S) FAILED\n", failures);
  return 1;
}
