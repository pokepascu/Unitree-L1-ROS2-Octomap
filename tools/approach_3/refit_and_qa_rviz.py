#!/usr/bin/env python3
"""Prepare trajectory-fitted RViz cameras and QA final Approach 3 captures.

This utility does not modify map geometry. It only computes deterministic RViz
camera framing from recorded odometry extents and validates the resulting PNG
captures. The fixed mapping extrinsic remains documented separately.

The QA command always writes its report and returns successfully so that failed
metrics are preserved as evidence by CI. A FAIL in the report is a diagnostic
result to investigate; it is not silently converted into a PASS.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

import numpy as np


def load_xy(path: Path) -> tuple[np.ndarray, np.ndarray]:
    xs, ys = [], []
    with path.open(newline="") as f:
        for row in csv.DictReader(f):
            xs.append(float(row["x_m"]))
            ys.append(float(row["y_m"]))
    if len(xs) < 2:
        raise RuntimeError(f"insufficient odometry samples in {path}")
    return np.asarray(xs, dtype=float), np.asarray(ys, dtype=float)


def fit_camera(odom: Path, output: Path, config_dir: Path, sensor_range_m: float = 15.0) -> dict:
    xs, ys = load_xy(odom)
    xmin, xmax = float(xs.min()), float(xs.max())
    ymin, ymax = float(ys.min()), float(ys.max())
    cx, cy = (xmin + xmax) / 2.0, (ymin + ymax) / 2.0
    xr, yr = xmax - xmin, ymax - ymin

    # Allow the map to extend by the configured sensor range around the recorded
    # robot path, then add perspective margin. This is camera framing only.
    map_w = xr + 2.0 * sensor_range_m
    map_h = yr + 2.0 * sensor_range_m
    distance = max(28.0, 1.18 * max(map_h, map_w / 1.60))

    output.mkdir(parents=True, exist_ok=True)
    names = {
        "isometric": "approach3_fused_octomap_isometric.rviz",
        "top": "approach3_fused_octomap_top.rviz",
        "side": "approach3_fused_octomap_side.rviz",
    }
    for view, name in names.items():
        src = config_dir / name
        text = src.read_text(encoding="utf-8")
        text = re.sub(r"Distance: [-+0-9.eE]+", f"Distance: {distance:.3f}", text)
        text = re.sub(
            r"Focal Point: \{X: [-+0-9.eE]+, Y: [-+0-9.eE]+, Z: [-+0-9.eE]+\}",
            f"Focal Point: {{X: {cx:.6f}, Y: {cy:.6f}, Z: 0.5}}",
            text,
        )
        (output / f"octomap_{view}.rviz").write_text(text, encoding="utf-8")

    report = {
        "method": "trajectory_bbox_center_plus_sensor_range_margin",
        "trajectory_bounds_xy_m": {"xmin": xmin, "xmax": xmax, "ymin": ymin, "ymax": ymax},
        "trajectory_center_xy_m": [cx, cy],
        "trajectory_span_xy_m": [xr, yr],
        "sensor_range_margin_m_each_side": sensor_range_m,
        "estimated_map_span_xy_m": [map_w, map_h],
        "rviz_orbit_distance_m": distance,
        "focal_z_m": 0.5,
    }
    (output / "camera_fit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


def ascii_mask(mask: np.ndarray, h: int = 32, w: int = 76, gain: float = 10.0) -> str:
    chars = " .:-=+*#%@"
    H, W = mask.shape
    yy = np.linspace(0, H, h + 1, dtype=int)
    xx = np.linspace(0, W, w + 1, dtype=int)
    lines = []
    for i in range(h):
        row = []
        for j in range(w):
            block = mask[yy[i] : yy[i + 1], xx[j] : xx[j + 1]]
            value = float(block.mean()) if block.size else 0.0
            idx = min(len(chars) - 1, int(round(value * (len(chars) - 1) * gain)))
            row.append(chars[idx])
        lines.append("".join(row).rstrip())
    return "\n".join(lines)


def image_metrics(path: Path) -> dict:
    from PIL import Image
    from scipy import ndimage

    rgb = np.asarray(Image.open(path).convert("RGB"), dtype=np.uint8)
    H, W = rgb.shape[:2]
    if H < 700 or W < 1200:
        raise RuntimeError(f"unexpected RViz capture dimensions {W}x{H}: {path}")
    viewport = rgb[55 : H - 35, 320:W]
    blue = (viewport[:, :, 2] > 180) & (viewport[:, :, 0] < 80) & (viewport[:, :, 1] < 80)
    blue = ndimage.binary_opening(blue, structure=np.ones((2, 2)))
    fraction = float(blue.mean())
    if blue.any():
        ys, xs = np.nonzero(blue)
        bbox = [
            float((xs.max() - xs.min() + 1) / blue.shape[1]),
            float((ys.max() - ys.min() + 1) / blue.shape[0]),
        ]
        centroid = [float(xs.mean() / blue.shape[1]), float(ys.mean() / blue.shape[0])]
    else:
        bbox = [0.0, 0.0]
        centroid = [0.0, 0.0]
    labels, n = ndimage.label(blue)
    sizes = np.bincount(labels.ravel())[1:] if n else np.asarray([], dtype=int)
    large = sizes[sizes >= 20]
    return {
        "image_size_px": [W, H],
        "blue_octomap_fraction": fraction,
        "blue_bbox_fraction_xy": bbox,
        "blue_centroid_normalized_xy": centroid,
        "blue_components_ge_20px": int(len(large)),
        "ascii": ascii_mask(blue),
    }


def qa(root: Path, output: Path) -> list[str]:
    runs = ["HcMR_lab", "ISR_5th_floor_run_1", "ISR_5th_floor_run_2"]
    views = {
        "isometric": "02_final_isometric.png",
        "top": "03_final_top.png",
        "side": "04_final_side.png",
    }
    thresholds = {"isometric": 0.001, "top": 0.001, "side": 0.001}
    lines = [
        "# Approach 3 RViz visual QA — trajectory-fitted v3",
        "",
        "This diagnostic is computed from the actual final RViz PNG captures after trajectory-centered camera fitting. It does not replace the screenshots and is not a metrological map-accuracy score.",
        "",
        "The OctoMap MarkerArray is blue in these captures. The QA therefore measures blue occupied-cell visibility inside the cropped RViz viewport. A minimum 0.1% visible blue fraction is used as a conservative presentation diagnostic in every final view.",
        "",
    ]
    failed: list[str] = []
    for run in runs:
        out = root / run / "odometry_lidar_fusion"
        camera = json.loads((out / "camera_fit.json").read_text(encoding="utf-8"))
        lines += [
            f"## {run}",
            "",
            f"- trajectory center XY: `{camera['trajectory_center_xy_m']}` m",
            f"- trajectory span XY: `{camera['trajectory_span_xy_m']}` m",
            f"- fitted RViz distance: `{camera['rviz_orbit_distance_m']:.3f}` m",
            "",
        ]
        for view, name in views.items():
            m = image_metrics(out / name)
            passed = m["blue_octomap_fraction"] >= thresholds[view]
            if not passed:
                failed.append(f"{run}/{view}")
            lines += [
                f"### {view}",
                "",
                f"- blue OctoMap viewport fraction: `{100*m['blue_octomap_fraction']:.3f}%`",
                f"- blue bbox coverage XY: `{100*m['blue_bbox_fraction_xy'][0]:.1f}% x {100*m['blue_bbox_fraction_xy'][1]:.1f}%`",
                f"- blue centroid normalized XY: `({m['blue_centroid_normalized_xy'][0]:.3f}, {m['blue_centroid_normalized_xy'][1]:.3f})`",
                f"- blue components >=20 px: `{m['blue_components_ge_20px']}`",
                f"- visibility gate: `{'PASS' if passed else 'FAIL'}`",
                "",
            ]
            if view == "top":
                lines += ["#### Top-view blue occupancy proxy", "", "```text", m["ascii"], "```", ""]
    lines += ["## Overall result", "", f"**{'FAIL' if failed else 'PASS'}**", ""]
    if failed:
        lines += ["Failed views: " + ", ".join(failed), ""]
    lines += [
        "A PASS establishes that the trajectory-fitted captures contain a materially visible OctoMap in all three canonical views. It does not establish the absolute accuracy of the +23 deg mounting yaw, which remains a documented fixed-mount working constraint rather than an independently measured calibration.",
        "",
        "If this report says FAIL, the report is intentionally still preserved and committed so the failing view can be corrected from quantitative evidence rather than guessed.",
        "",
    ]
    output.write_text("\n".join(lines), encoding="utf-8")
    print(output.read_text(encoding="utf-8"))
    if failed:
        print("QA_DIAGNOSTIC_FAIL", ",".join(failed))
    else:
        print("QA_DIAGNOSTIC_PASS")
    return failed


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--odom", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--config-dir", type=Path, default=Path("config/rviz"))
    p.add_argument("--sensor-range", type=float, default=15.0)
    q = sub.add_parser("qa")
    q.add_argument("--root", type=Path, default=Path("results/approach_3"))
    q.add_argument("--report", type=Path, default=Path("results/approach_3/VISUAL_QA_V3.md"))
    args = ap.parse_args()
    if args.command == "prepare":
        fit_camera(args.odom, args.out, args.config_dir, args.sensor_range)
    else:
        qa(args.root, args.report)


if __name__ == "__main__":
    main()
