from l1_monitor.stats import StreamStats


def test_frequency_metadata_and_age():
    stats = StreamStats(window_size=3)
    stats.record(0, 1_000_000_000, "lidar", 10, ("x", "y", "z"))
    stats.record(100_000_000, 1_100_000_000, "lidar", 12, ("x", "y", "z"))
    stats.record(200_000_000, 1_200_000_000, "lidar", 14, ("x", "y", "z"))

    assert stats.frequency_hz() == 10.0
    assert stats.arrival_age_sec(250_000_000) == 0.05
    assert stats.stamp_age_sec(1_250_000_000) == 0.05
    assert stats.last_item_count == 14
    assert stats.last_fields == ("x", "y", "z")
    assert stats.last_frame == "lidar"


def test_detects_zero_and_non_increasing_timestamps():
    stats = StreamStats()
    stats.record(1, 0, "imu")
    stats.record(2, 0, "imu")

    assert stats.zero_stamps == 2
    assert stats.non_monotonic_stamps == 1
    assert stats.stamp_age_sec(10) is None


def test_requires_meaningful_window():
    try:
        StreamStats(window_size=1)
    except ValueError as error:
        assert "at least 2" in str(error)
    else:
        raise AssertionError("expected ValueError")
