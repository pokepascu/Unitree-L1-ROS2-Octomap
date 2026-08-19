#!/usr/bin/env python3
"""Select low-motion 30 s windows from raw ROS 2 MCAPs and write standalone MCAP subsets."""
import csv
import math
from pathlib import Path

import numpy as np
import yaml
from mcap.reader import make_reader
from mcap.writer import Writer
from mcap_ros2.decoder import DecoderFactory

WINDOW_NS = 30_000_000_000
STEP_NS = 1_000_000_000
SOURCES = {
    "HcMR_lab": Path("bags/raw/HcMR_lab_2026-08-07_21-13-45"),
    "ISR_5th_floor_run_1": Path("bags/raw/ISR_5th_floor_run_1_2026-08-07_21-31-58"),
    "ISR_5th_floor_run_2": Path("bags/raw/ISR_5th_floor_run_2_2026-08-07_21-48-31"),
}


def yaw(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


def read_odom(bag):
    rows = []
    with bag.open("rb") as f:
        reader = make_reader(f, decoder_factories=[DecoderFactory()])
        for _, _, msg, ros in reader.iter_decoded_messages(topics=["/odom"]):
            p = ros.pose.pose.position
            q = ros.pose.pose.orientation
            tw = ros.twist.twist
            lin = math.sqrt(tw.linear.x**2 + tw.linear.y**2 + tw.linear.z**2)
            ang = math.sqrt(tw.angular.x**2 + tw.angular.y**2 + tw.angular.z**2)
            rows.append((msg.log_time, p.x, p.y, p.z, yaw(q), lin, ang))
    if not rows:
        raise RuntimeError(f"No /odom messages in {bag}")
    return np.asarray(rows, dtype=float)


def candidates(bag, label):
    a = read_odom(bag)
    t = a[:, 0].astype(np.int64)
    out = []
    for start in range(int(t[0]), int(t[-1]) - WINDOW_NS + 1, STEP_NS):
        end = start + WINDOW_NS
        window = a[np.searchsorted(t, start, "left") : np.searchsorted(t, end, "right")]
        if len(window) < 20:
            continue
        xyz = window[:, 1:4]
        center = np.median(xyz, axis=0)
        radius = float(np.max(np.linalg.norm(xyz - center, axis=1)))
        path = float(np.sum(np.linalg.norm(np.diff(xyz, axis=0), axis=1))) if len(xyz) > 1 else 0.0
        yaw_span = float(np.ptp(np.unwrap(window[:, 4]))) if len(window) > 1 else 0.0
        lin95 = float(np.percentile(window[:, 5], 95))
        ang95 = float(np.percentile(window[:, 6], 95))
        score = radius + 0.15 * path + 0.5 * yaw_span + 4 * lin95 + 2 * ang95
        out.append(
            {
                "source": label,
                "start_ns": int(start),
                "end_ns": int(end),
                "score": score,
                "position_radius_m": radius,
                "path_length_m": path,
                "yaw_span_rad": yaw_span,
                "linear_speed_p95_mps": lin95,
                "angular_speed_p95_radps": ang95,
                "median_x_m": float(center[0]),
                "median_y_m": float(center[1]),
                "median_z_m": float(center[2]),
            }
        )
    return out


def select(cands, n):
    picked = []
    # First pass: non-overlapping and spatially separated candidates.
    for c in sorted(cands, key=lambda x: x["score"]):
        if any(c["source"] == p["source"] and abs(c["start_ns"] - p["start_ns"]) < WINDOW_NS for p in picked):
            continue
        same_source = [p for p in picked if p["source"] == c["source"]]
        if same_source and all(
            math.hypot(c["median_x_m"] - p["median_x_m"], c["median_y_m"] - p["median_y_m"]) < 0.35
            for p in same_source
        ):
            continue
        picked.append(c)
        if len(picked) == n:
            return picked
    # Fallback: preserve non-overlap if the experiment lacks three clearly separated low-motion windows.
    for c in sorted(cands, key=lambda x: x["score"]):
        if c in picked:
            continue
        if any(c["source"] == p["source"] and abs(c["start_ns"] - p["start_ns"]) < WINDOW_NS for p in picked):
            continue
        picked.append(c)
        if len(picked) == n:
            break
    return picked


def slice_mcap(src, out, start, end):
    schema_ids = {}
    channel_ids = {}
    count = 0
    with src.open("rb") as fi, out.open("wb") as fo:
        reader = make_reader(fi)
        header = reader.get_header()
        writer = Writer(fo)
        writer.start(profile=header.profile, library="HcMR-static-window-extractor")
        for schema, channel, msg in reader.iter_messages(start_time=start, end_time=end, log_time_order=False):
            schema_id = 0
            if schema is not None:
                if schema.id not in schema_ids:
                    schema_ids[schema.id] = writer.register_schema(schema.name, schema.encoding, schema.data)
                schema_id = schema_ids[schema.id]
            if channel.id not in channel_ids:
                channel_ids[channel.id] = writer.register_channel(
                    channel.topic, channel.message_encoding, schema_id, dict(channel.metadata)
                )
            writer.add_message(
                channel_ids[channel.id], msg.log_time, msg.data, msg.publish_time, msg.sequence
            )
            count += 1
        writer.finish()
    if count == 0:
        raise RuntimeError(f"Empty slice {src}: {start}:{end}")
    return count


def cloud_count(bag, start, end):
    with bag.open("rb") as f:
        return sum(
            1
            for _ in make_reader(f).iter_messages(
                topics=["/unilidar/cloud"], start_time=start, end_time=end
            )
        )


def make_metadata(out, template):
    with template.open() as f:
        meta = yaml.safe_load(f)
    counts = {}
    first = None
    last = None
    total = 0
    with out.open("rb") as f:
        for _, channel, msg in make_reader(f).iter_messages():
            counts[channel.topic] = counts.get(channel.topic, 0) + 1
            total += 1
            first = msg.log_time if first is None else min(first, msg.log_time)
            last = msg.log_time if last is None else max(last, msg.log_time)
    info = meta["rosbag2_bagfile_information"]
    for item in info.get("topics_with_message_count", []):
        item["message_count"] = int(counts.get(item["topic_metadata"]["name"], 0))
    info["message_count"] = int(total)
    info["starting_time"] = {"nanoseconds_since_epoch": int(first or 0)}
    info["duration"] = {
        "nanoseconds": int((last - first) if first is not None and last is not None else 0)
    }
    info["relative_file_paths"] = [out.name]
    info["files"] = [
        {
            "path": out.name,
            "starting_time": {"nanoseconds_since_epoch": int(first or 0)},
            "duration": info["duration"],
            "message_count": int(total),
        }
    ]
    with (out.parent / "metadata.yaml").open("w") as f:
        yaml.safe_dump(meta, f, sort_keys=False)


def write_subset(candidate, dest):
    srcdir = SOURCES[candidate["source"]]
    src = next(srcdir.glob("*.mcap"))
    dest.mkdir(parents=True, exist_ok=True)
    out = dest / "static_30s.mcap"
    candidate = dict(candidate)
    candidate["total_messages"] = slice_mcap(
        src, out, candidate["start_ns"], candidate["end_ns"]
    )
    candidate["cloud_messages"] = cloud_count(
        src, candidate["start_ns"], candidate["end_ns"]
    )
    make_metadata(out, srcdir / "metadata.yaml")
    with (dest / "selection.yaml").open("w") as f:
        yaml.safe_dump(candidate, f, sort_keys=False)
    return candidate


all_candidates = {
    key: candidates(next(directory.glob("*.mcap")), key)
    for key, directory in SOURCES.items()
}
lab = select(all_candidates["HcMR_lab"], 3)
floor = select(
    all_candidates["ISR_5th_floor_run_1"] + all_candidates["ISR_5th_floor_run_2"], 3
)
if len(lab) < 3 or len(floor) < 3:
    raise RuntimeError(f"Not enough 30 s windows: lab={len(lab)}, floor={len(floor)}")

root = Path("study_data")
# Approach 1: one best static window in each target environment.
write_subset(lab[0], root / "approach_1_single_static" / "HcMR_lab" / "scan_01")
write_subset(floor[0], root / "approach_1_single_static" / "ISR_5th_floor" / "scan_01")
# Approach 2: three separate static windows for registration/ICP.
written = []
for env, seq in [("HcMR_lab", lab), ("ISR_5th_floor", floor)]:
    for i, c in enumerate(seq, 1):
        rec = write_subset(c, root / "approach_2_three_static_icp" / env / f"scan_{i:02d}")
        written.append({"environment": env, "scan_index": i, **rec})

with (root / "static_selection_report.csv").open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(written[0]))
    writer.writeheader()
    writer.writerows(written)
