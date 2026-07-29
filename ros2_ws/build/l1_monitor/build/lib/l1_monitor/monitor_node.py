"""ROS 2 diagnostics node for the Unitree L1 cloud and IMU streams."""

import time

import rclpy
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Imu, PointCloud2

from .stats import StreamStats


def _header_stamp_ns(message):
    return message.header.stamp.sec * 1_000_000_000 + message.header.stamp.nanosec


def _key_value(key, value):
    return KeyValue(key=str(key), value=str(value))


class L1Monitor(Node):
    """Observe raw streams without modifying or republishing sensor data."""

    def __init__(self):
        super().__init__("l1_monitor")
        self.declare_parameter("cloud_topic", "/unilidar/cloud")
        self.declare_parameter("imu_topic", "/unilidar/imu")
        self.declare_parameter("diagnostics_topic", "/diagnostics")
        self.declare_parameter("report_period_sec", 2.0)
        self.declare_parameter("timeout_sec", 3.0)
        self.declare_parameter("max_stamp_age_sec", 1.0)
        self.declare_parameter("min_cloud_hz", 5.0)
        self.declare_parameter("min_imu_hz", 20.0)
        self.declare_parameter("window_size", 100)

        self._report_period = float(self.get_parameter("report_period_sec").value)
        self._timeout = float(self.get_parameter("timeout_sec").value)
        self._max_stamp_age = float(self.get_parameter("max_stamp_age_sec").value)
        self._min_cloud_hz = float(self.get_parameter("min_cloud_hz").value)
        self._min_imu_hz = float(self.get_parameter("min_imu_hz").value)
        window_size = int(self.get_parameter("window_size").value)
        if self._report_period <= 0.0 or self._timeout <= 0.0:
            raise ValueError("report_period_sec and timeout_sec must be positive")

        self._started_ns = time.monotonic_ns()
        self._cloud = StreamStats(window_size)
        self._imu = StreamStats(window_size)
        qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
        )
        cloud_topic = str(self.get_parameter("cloud_topic").value)
        imu_topic = str(self.get_parameter("imu_topic").value)
        diagnostics_topic = str(self.get_parameter("diagnostics_topic").value)
        self.create_subscription(PointCloud2, cloud_topic, self._on_cloud, qos)
        self.create_subscription(Imu, imu_topic, self._on_imu, qos)
        self._publisher = self.create_publisher(DiagnosticArray, diagnostics_topic, 10)
        self.create_timer(self._report_period, self._report)
        self.get_logger().info(
            f"monitoring cloud={cloud_topic} imu={imu_topic} "
            f"diagnostics={diagnostics_topic}"
        )

    def _on_cloud(self, message):
        self._cloud.record(
            arrival_ns=time.monotonic_ns(),
            stamp_ns=_header_stamp_ns(message),
            frame=message.header.frame_id,
            item_count=message.width * message.height,
            fields=(field.name for field in message.fields),
        )

    def _on_imu(self, message):
        self._imu.record(
            arrival_ns=time.monotonic_ns(),
            stamp_ns=_header_stamp_ns(message),
            frame=message.header.frame_id,
        )

    def _status(self, name, stats, min_hz, now_steady_ns, now_ros_ns):
        status = DiagnosticStatus()
        status.name = f"unitree_l1/{name}"
        status.hardware_id = "unitree_l1"
        age = stats.arrival_age_sec(now_steady_ns)
        frequency = stats.frequency_hz()
        stamp_age = stats.stamp_age_sec(now_ros_ns)
        startup_age = (now_steady_ns - self._started_ns) / 1e9

        problems = []
        level = DiagnosticStatus.OK
        if stats.received == 0:
            level = (
                DiagnosticStatus.ERROR
                if startup_age > self._timeout
                else DiagnosticStatus.WARN
            )
            problems.append("no messages received")
        elif age is not None and age > self._timeout:
            level = DiagnosticStatus.ERROR
            problems.append(f"last message is {age:.3f}s old")
        if stats.received >= 2 and frequency < min_hz:
            level = max(level, DiagnosticStatus.WARN)
            problems.append(f"frequency {frequency:.2f}Hz below {min_hz:.2f}Hz")
        if stats.non_monotonic_stamps:
            level = DiagnosticStatus.ERROR
            problems.append(f"{stats.non_monotonic_stamps} non-increasing timestamps")
        if stats.zero_stamps:
            level = max(level, DiagnosticStatus.WARN)
            problems.append(f"{stats.zero_stamps} zero timestamps")
        if stamp_age is not None and abs(stamp_age) > self._max_stamp_age:
            level = max(level, DiagnosticStatus.WARN)
            problems.append(f"header age is {stamp_age:.3f}s")

        status.level = level
        status.message = "; ".join(problems) if problems else "stream healthy"
        status.values = [
            _key_value("received", stats.received),
            _key_value("frequency_hz", f"{frequency:.3f}"),
            _key_value("arrival_age_sec", "n/a" if age is None else f"{age:.3f}"),
            _key_value(
                "header_age_sec",
                "n/a" if stamp_age is None else f"{stamp_age:.3f}",
            ),
            _key_value("frame_id", stats.last_frame or "n/a"),
            _key_value("non_monotonic_stamps", stats.non_monotonic_stamps),
            _key_value("zero_stamps", stats.zero_stamps),
        ]
        if stats.last_item_count is not None:
            status.values.append(_key_value("point_count", stats.last_item_count))
            status.values.append(_key_value("fields", ",".join(stats.last_fields)))
        return status

    def _report(self):
        now_steady_ns = time.monotonic_ns()
        now_ros = self.get_clock().now()
        cloud_status = self._status(
            "cloud", self._cloud, self._min_cloud_hz, now_steady_ns, now_ros.nanoseconds
        )
        imu_status = self._status(
            "imu", self._imu, self._min_imu_hz, now_steady_ns, now_ros.nanoseconds
        )
        message = DiagnosticArray()
        message.header.stamp = now_ros.to_msg()
        message.status = [cloud_status, imu_status]
        self._publisher.publish(message)
        self.get_logger().info(
            "cloud="
            f"{cloud_status.message} ({self._cloud.frequency_hz():.2f}Hz, "
            f"points={self._cloud.last_item_count}) | "
            f"imu={imu_status.message} ({self._imu.frequency_hz():.2f}Hz)"
        )


def main(args=None):
    """Run the monitor until ROS requests shutdown."""
    rclpy.init(args=args)
    node = L1Monitor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        # The default ROS 2 signal handler can already have shut the context
        # down before spin() returns after Ctrl-C.
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
