// supervisor_node.cpp -- ROS1 adapter around safety::Supervisor.
//
// Level A: it reads the estimator's image / LiDAR / odometry topics and
// publishes a supervised odometry stream plus a state string.  It never
// writes back into the estimator and never broadcasts TF, so it can be
// attached to a different LIVO system by changing only topic names and the
// LiDAR point-count convention.
//
// Odometry is usually the estimator's only clock.  If the estimator stops
// publishing odometry exactly when images stop (R3LIVE does this when its VIO
// loses images), an odom-only supervisor would never see the outage.  A 10 Hz
// timer therefore steps the same Supervisor with the last raw pose when odom
// has been silent for >0.25 s.  This is still read-only with respect to the
// estimator; it only lets the supervisor's own clock advance.
#include <algorithm>
#include <limits>
#include <sstream>
#include <string>

#include <geometry_msgs/Twist.h>
#include <nav_msgs/Odometry.h>
#include <ros/ros.h>
#include <sensor_msgs/Image.h>
#include <sensor_msgs/PointCloud2.h>
#include <std_msgs/String.h>

#include <safety/supervisor.h>

namespace {

class SupervisorNode {
 public:
  SupervisorNode() : nh_(), pnh_("~") {
    std::string image_topic, lidar_topic, odom_topic, state_topic, odom_out_topic;
    pnh_.param<std::string>("image_topic", image_topic, "/fault_injector/image_raw");
    pnh_.param<std::string>("lidar_topic", lidar_topic, "/livox/lidar");
    pnh_.param<std::string>("odom_topic", odom_topic, "/aft_mapped_to_init");
    pnh_.param<std::string>("state_topic", state_topic, "/safety/state");
    pnh_.param<std::string>("odom_out_topic", odom_out_topic, "/safety/odom");

    safety::SupervisorConfig cfg;
    pnh_.param("hold_output", cfg.hold_output, false);
    pnh_.param("n_outage", cfg.reliability.n_outage, 5);
    pnh_.param("n_deg", cfg.reliability.n_deg, 3);
    pnh_.param("n_unk", cfg.reliability.n_unk, 10);
    pnh_.param("n_lidar_unk", cfg.reliability.n_lidar_unk, 10);
    pnh_.param("n_res", cfg.reliability.n_res, 10);
    pnh_.param("lidar_p05", cfg.reliability.lidar_p05, 14.0);
    pnh_.param("lidar_p50", cfg.reliability.lidar_p50, 1406.5);
    supervisor_ = safety::Supervisor(cfg);

    state_pub_ = nh_.advertise<std_msgs::String>(state_topic, 10);
    odom_pub_ = nh_.advertise<nav_msgs::Odometry>(odom_out_topic, 10);

    image_sub_ = nh_.subscribe(image_topic, 10, &SupervisorNode::imageCallback, this);
    lidar_sub_ = nh_.subscribe(lidar_topic, 10, &SupervisorNode::lidarCallback, this);
    odom_sub_ = nh_.subscribe(odom_topic, 10, &SupervisorNode::odomCallback, this);
    timer_ = nh_.createTimer(ros::Duration(0.1), &SupervisorNode::timerCallback, this);

    ROS_INFO_STREAM("safety_supervisor: image=" << image_topic << " lidar=" << lidar_topic
                                                << " odom=" << odom_topic
                                                << " hold=" << (cfg.hold_output ? "on" : "off"));
  }

 private:
  void imageCallback(const sensor_msgs::ImageConstPtr &msg) {
    supervisor_.notifyImage(msg->header.stamp.toSec());
  }

  void lidarCallback(const sensor_msgs::PointCloud2ConstPtr &msg) {
    size_t n = static_cast<size_t>(msg->width) * static_cast<size_t>(msg->height);
    if (n == 0 && msg->point_step > 0) n = msg->data.size() / msg->point_step;
    n = std::min<size_t>(n, static_cast<size_t>(std::numeric_limits<int>::max()));
    supervisor_.notifyLidar(static_cast<int>(n));
  }

  void odomCallback(const nav_msgs::OdometryConstPtr &msg) {
    last_odom_ = ros::Time::now();
    last_odom_msg_ = *msg;
    last_raw_.stamp = msg->header.stamp.toSec();
    last_raw_.p[0] = msg->pose.pose.position.x;
    last_raw_.p[1] = msg->pose.pose.position.y;
    last_raw_.p[2] = msg->pose.pose.position.z;
    last_raw_.q[0] = msg->pose.pose.orientation.x;
    last_raw_.q[1] = msg->pose.pose.orientation.y;
    last_raw_.q[2] = msg->pose.pose.orientation.z;
    last_raw_.q[3] = msg->pose.pose.orientation.w;
    have_raw_ = true;
    stepAndPublish();
  }

  void timerCallback(const ros::TimerEvent &) {
    if (!have_raw_) return;
    if ((ros::Time::now() - last_odom_).toSec() < 0.25) return;
    // The estimator is silent.  Advance the supervisor's own clock using the
    // last raw pose; the output gate decides whether to hold or repeat it.
    stepAndPublish();
  }

  void stepAndPublish() {
    safety::SupervisorOutput out = supervisor_.step(last_raw_);

    nav_msgs::Odometry odom = last_odom_msg_;
    odom.pose.pose.position.x = out.gate.pose.p[0];
    odom.pose.pose.position.y = out.gate.pose.p[1];
    odom.pose.pose.position.z = out.gate.pose.p[2];
    odom.pose.pose.orientation.x = out.gate.pose.q[0];
    odom.pose.pose.orientation.y = out.gate.pose.q[1];
    odom.pose.pose.orientation.z = out.gate.pose.q[2];
    odom.pose.pose.orientation.w = out.gate.pose.q[3];
    if (out.gate.hold) {
      odom.twist.twist = geometry_msgs::Twist();
    }
    odom_pub_.publish(odom);

    std::ostringstream js;
    js << "{\"state\":\"" << safety::relStateName(out.state)
       << "\",\"reason\":\"" << out.gate.reason
       << "\",\"hold\":" << (out.gate.hold ? "true" : "false")
       << ",\"outage_frames\":" << out.outage_frames << "}";
    std_msgs::String state_msg;
    state_msg.data = js.str();
    state_pub_.publish(state_msg);
  }

  ros::NodeHandle nh_;
  ros::NodeHandle pnh_;
  ros::Subscriber image_sub_;
  ros::Subscriber lidar_sub_;
  ros::Subscriber odom_sub_;
  ros::Publisher state_pub_;
  ros::Publisher odom_pub_;
  ros::Timer timer_;
  safety::Supervisor supervisor_;
  safety::Pose last_raw_;
  nav_msgs::Odometry last_odom_msg_;
  ros::Time last_odom_;
  bool have_raw_ = false;
};

}  // namespace

int main(int argc, char **argv) {
  ros::init(argc, argv, "safety_supervisor");
  SupervisorNode node;
  ros::spin();
  return 0;
}
