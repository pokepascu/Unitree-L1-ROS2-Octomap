#!/usr/bin/env python3
"""Validate source ROS 2 MCAP payloads by full message iteration and metadata agreement."""
from pathlib import Path
import json
import yaml
from mcap.reader import make_reader

ROOT = Path('/tmp/nas_download')
required_topics = {'/unilidar/cloud', '/unilidar/imu', '/odom', '/tf', '/cmd_vel'}
report = []

folders = sorted(p for p in ROOT.glob('rosbag2_2026_08_07-21_*') if p.is_dir())
if len(folders) != 3:
    raise RuntimeError(f'Expected 3 rosbag directories, found {len(folders)}')

for folder in folders:
    bag = next(folder.glob('*.mcap'))
    metadata_path = folder / 'metadata.yaml'
    with metadata_path.open() as f:
        meta = yaml.safe_load(f)['rosbag2_bagfile_information']

    expected = {
        item['topic_metadata']['name']: int(item['message_count'])
        for item in meta.get('topics_with_message_count', [])
    }
    actual = {}
    schemas = {}
    first = None
    last = None
    total = 0
    with bag.open('rb') as f:
        reader = make_reader(f)
        header = reader.get_header()
        for schema, channel, message in reader.iter_messages(log_time_order=False):
            actual[channel.topic] = actual.get(channel.topic, 0) + 1
            if schema is not None:
                schemas[channel.topic] = schema.name
            total += 1
            first = message.log_time if first is None else min(first, message.log_time)
            last = message.log_time if last is None else max(last, message.log_time)

    missing = sorted(required_topics - set(actual))
    if missing:
        raise RuntimeError(f'{bag}: required topics missing: {missing}')
    mismatches = {
        topic: {'metadata': count, 'read': actual.get(topic, 0)}
        for topic, count in expected.items()
        if actual.get(topic, 0) != count
    }
    if mismatches:
        raise RuntimeError(f'{bag}: metadata/message count mismatch: {mismatches}')
    if total != int(meta.get('message_count', total)):
        raise RuntimeError(f'{bag}: total count {total} != metadata {meta.get("message_count")}')

    record = {
        'bag': str(bag),
        'size_bytes': bag.stat().st_size,
        'message_count': total,
        'first_log_time_ns': first,
        'last_log_time_ns': last,
        'duration_s_from_messages': (last - first) / 1e9 if first is not None and last is not None else 0,
        'profile': header.profile,
        'topic_counts': actual,
        'schema_names': schemas,
    }
    report.append(record)
    print('SOURCE BAG VALID:', bag)
    print(json.dumps(record, indent=2))

(ROOT / 'source_validation_report.json').write_text(json.dumps(report, indent=2) + '\n')
