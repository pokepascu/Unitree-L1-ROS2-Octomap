"""Small dependency-free statistics model used by the ROS monitor."""

from collections import deque


class StreamStats:
    """Track arrivals and message metadata over a bounded time window."""

    def __init__(self, window_size=100):
        if window_size < 2:
            raise ValueError("window_size must be at least 2")
        self.arrivals_ns = deque(maxlen=window_size)
        self.received = 0
        self.last_stamp_ns = None
        self.last_frame = ""
        self.last_item_count = None
        self.last_fields = ()
        self.non_monotonic_stamps = 0
        self.zero_stamps = 0

    def record(
        self,
        arrival_ns,
        stamp_ns,
        frame,
        item_count=None,
        fields=(),
    ):
        """Record one message using monotonic arrival and ROS header times."""
        if self.last_stamp_ns is not None and stamp_ns <= self.last_stamp_ns:
            self.non_monotonic_stamps += 1
        if stamp_ns == 0:
            self.zero_stamps += 1
        self.arrivals_ns.append(arrival_ns)
        self.received += 1
        self.last_stamp_ns = stamp_ns
        self.last_frame = frame
        self.last_item_count = item_count
        self.last_fields = tuple(fields)

    def frequency_hz(self):
        """Return the arrival frequency over the current window."""
        if len(self.arrivals_ns) < 2:
            return 0.0
        elapsed = (self.arrivals_ns[-1] - self.arrivals_ns[0]) / 1e9
        if elapsed <= 0.0:
            return 0.0
        return (len(self.arrivals_ns) - 1) / elapsed

    def arrival_age_sec(self, now_ns):
        """Return seconds since last arrival, or None before first message."""
        if not self.arrivals_ns:
            return None
        return max(0.0, (now_ns - self.arrivals_ns[-1]) / 1e9)

    def stamp_age_sec(self, now_ros_ns):
        """Return ROS-clock age of the latest header, or None if unavailable."""
        if self.last_stamp_ns is None or self.last_stamp_ns == 0:
            return None
        return (now_ros_ns - self.last_stamp_ns) / 1e9
