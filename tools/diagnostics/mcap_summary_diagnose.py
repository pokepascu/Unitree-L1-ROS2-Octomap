#!/usr/bin/env python3
import argparse
import json
from collections import Counter
from pathlib import Path

import yaml
from mcap.records import Channel, Chunk, DataEnd, Footer, Header, Message, Schema, Statistics
from mcap.stream_reader import StreamReader, breakup_chunk


def schema_dict(s: Schema):
    preview = ""
    try:
        preview = s.data.decode("utf-8", errors="replace")[:500]
    except Exception:
        preview = repr(s.data[:120])
    return {
        "id": s.id,
        "name": s.name,
        "encoding": s.encoding,
        "data_length": len(s.data),
        "data_preview": preview,
    }


def channel_dict(c: Channel):
    return {
        "id": c.id,
        "schema_id": c.schema_id,
        "topic": c.topic,
        "message_encoding": c.message_encoding,
        "metadata": dict(c.metadata),
    }


def diagnose(mcap_path: Path, metadata_path: Path | None):
    report = {
        "file": str(mcap_path),
        "size_bytes": mcap_path.stat().st_size,
        "header": None,
        "footer": None,
        "data": {
            "schemas_top_level": {},
            "schemas_in_chunks": {},
            "channels_top_level": {},
            "channels_in_chunks": {},
            "messages_by_channel": {},
            "chunk_count": 0,
        },
        "summary": {
            "schemas": {},
            "channels": {},
            "statistics_channel_message_counts": {},
        },
        "rosbag2_metadata": None,
    }

    counts = Counter()
    phase = "data"

    with mcap_path.open("rb") as f:
        reader = StreamReader(f, emit_chunks=True, validate_crcs=False)
        for record in reader.records:
            if isinstance(record, Header):
                report["header"] = {"profile": record.profile, "library": record.library}
                continue
            if isinstance(record, DataEnd):
                phase = "summary"
                continue
            if isinstance(record, Footer):
                report["footer"] = {
                    "summary_start": record.summary_start,
                    "summary_offset_start": record.summary_offset_start,
                    "summary_crc": record.summary_crc,
                }
                continue

            if phase == "data":
                if isinstance(record, Schema):
                    report["data"]["schemas_top_level"][str(record.id)] = schema_dict(record)
                elif isinstance(record, Channel):
                    report["data"]["channels_top_level"][str(record.id)] = channel_dict(record)
                elif isinstance(record, Message):
                    counts[record.channel_id] += 1
                elif isinstance(record, Chunk):
                    report["data"]["chunk_count"] += 1
                    for inner in breakup_chunk(record, validate_crc=False):
                        if isinstance(inner, Schema):
                            report["data"]["schemas_in_chunks"][str(inner.id)] = schema_dict(inner)
                        elif isinstance(inner, Channel):
                            report["data"]["channels_in_chunks"][str(inner.id)] = channel_dict(inner)
                        elif isinstance(inner, Message):
                            counts[inner.channel_id] += 1
            else:
                if isinstance(record, Schema):
                    report["summary"]["schemas"][str(record.id)] = schema_dict(record)
                elif isinstance(record, Channel):
                    report["summary"]["channels"][str(record.id)] = channel_dict(record)
                elif isinstance(record, Statistics):
                    report["summary"]["statistics_channel_message_counts"] = {
                        str(k): int(v) for k, v in record.channel_message_counts.items()
                    }

    report["data"]["messages_by_channel"] = {str(k): int(v) for k, v in sorted(counts.items())}

    data_schemas = set(report["data"]["schemas_top_level"]) | set(report["data"]["schemas_in_chunks"])
    data_channels = set(report["data"]["channels_top_level"]) | set(report["data"]["channels_in_chunks"])
    summary_schemas = set(report["summary"]["schemas"])
    summary_channels = set(report["summary"]["channels"])

    report["comparison"] = {
        "data_schema_ids": sorted(map(int, data_schemas)),
        "summary_schema_ids": sorted(map(int, summary_schemas)),
        "summary_only_schema_ids": sorted(map(int, summary_schemas - data_schemas)),
        "data_only_schema_ids": sorted(map(int, data_schemas - summary_schemas)),
        "data_channel_ids": sorted(map(int, data_channels)),
        "summary_channel_ids": sorted(map(int, summary_channels)),
        "summary_only_channel_ids": sorted(map(int, summary_channels - data_channels)),
        "data_only_channel_ids": sorted(map(int, data_channels - summary_channels)),
        "message_channels_not_defined_in_data": sorted(
            int(k) for k in report["data"]["messages_by_channel"] if k not in data_channels
        ),
    }

    # Enrich every summary channel with actual message count and schema name.
    enriched = []
    all_data_channels = dict(report["data"]["channels_top_level"])
    all_data_channels.update(report["data"]["channels_in_chunks"])
    all_data_schemas = dict(report["data"]["schemas_top_level"])
    all_data_schemas.update(report["data"]["schemas_in_chunks"])
    for cid, c in sorted(report["summary"]["channels"].items(), key=lambda kv: int(kv[0])):
        sid = str(c["schema_id"])
        s = report["summary"]["schemas"].get(sid) or all_data_schemas.get(sid)
        enriched.append({
            **c,
            "schema_name": s["name"] if s else None,
            "message_count_scanned": int(report["data"]["messages_by_channel"].get(cid, 0)),
            "present_in_data_section": cid in data_channels,
            "schema_present_in_data_section": sid in data_schemas,
        })
    report["channels_enriched"] = enriched

    if metadata_path and metadata_path.exists():
        obj = yaml.safe_load(metadata_path.read_text())
        info = obj.get("rosbag2_bagfile_information", {})
        topics = []
        for item in info.get("topics_with_message_count", []):
            md = item.get("topic_metadata", {})
            topics.append({
                "name": md.get("name"),
                "type": md.get("type"),
                "serialization_format": md.get("serialization_format"),
                "message_count": int(item.get("message_count", 0)),
            })
        report["rosbag2_metadata"] = {
            "message_count": int(info.get("message_count", 0)),
            "topics": topics,
        }

    return report


def markdown(reports):
    lines = ["# Low-level MCAP Data vs Summary diagnostic", ""]
    for r in reports:
        lines += [f"## `{Path(r['file']).name}`", ""]
        h = r.get("header") or {}
        lines += [f"- Size: `{r['size_bytes']}` bytes", f"- Header profile: `{h.get('profile')}`", f"- Header library: `{h.get('library')}`", f"- Chunks: `{r['data']['chunk_count']}`", ""]
        c = r["comparison"]
        lines += [
            f"- Data schema IDs: `{c['data_schema_ids']}`",
            f"- Summary schema IDs: `{c['summary_schema_ids']}`",
            f"- **Summary-only schema IDs:** `{c['summary_only_schema_ids']}`",
            f"- Data channel IDs: `{c['data_channel_ids']}`",
            f"- Summary channel IDs: `{c['summary_channel_ids']}`",
            f"- **Summary-only channel IDs:** `{c['summary_only_channel_ids']}`",
            f"- Message channels lacking a Data-section Channel definition: `{c['message_channels_not_defined_in_data']}`",
            "",
            "| ID | Topic | Schema | msgs scanned | channel in Data? | schema in Data? |",
            "|---:|---|---|---:|:---:|:---:|",
        ]
        for ch in r["channels_enriched"]:
            lines.append(
                f"| {ch['id']} | `{ch['topic']}` | `{ch['schema_name']}` | {ch['message_count_scanned']} | {'yes' if ch['present_in_data_section'] else '**NO**'} | {'yes' if ch['schema_present_in_data_section'] else '**NO**'} |"
            )
        lines.append("")
        if r.get("rosbag2_metadata"):
            lines += ["### rosbag2 `metadata.yaml`", "", "| Topic | Type | count |", "|---|---|---:|"]
            for t in r["rosbag2_metadata"]["topics"]:
                lines.append(f"| `{t['name']}` | `{t['type']}` | {t['message_count']} |")
            lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="diagnostic_output")
    ap.add_argument("bags", nargs="+")
    args = ap.parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    reports = []
    for bag_s in args.bags:
        bag = Path(bag_s)
        metadata = bag.parent / "metadata.yaml"
        reports.append(diagnose(bag, metadata if metadata.exists() else None))
    (out / "mcap_summary_diagnostic.json").write_text(json.dumps(reports, indent=2))
    md = markdown(reports)
    (out / "mcap_summary_diagnostic.md").write_text(md)
    print(md)

if __name__ == "__main__":
    main()
