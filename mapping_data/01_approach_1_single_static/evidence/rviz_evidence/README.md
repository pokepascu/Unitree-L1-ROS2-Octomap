# Canonical RViz visual evidence — Approach 1

This directory defines the **primary visual verification evidence** for the static Unitree L1 study.

Python/Open3D/Matplotlib figures under the neighbouring result directories are analytical aids. The authoritative visual proof of ROS data interpretation is produced in **RViz2** from the ROS 2 topics and derived ROS-compatible map products.

## Evidence hierarchy

For each environment (`HcMR_lab`, `ISR_5th_floor`) the expected structure is:

```text
rviz_evidence/
├── README.md
├── HcMR_lab/
│   ├── pointcloud/
│   │   ├── 01_accumulation_rviz.mp4
│   │   ├── 02_final_accumulated_isometric.png
│   │   ├── 03_final_accumulated_top.png
│   │   ├── 04_final_accumulated_side.png
│   │   └── pointcloud_accumulation.rviz
│   └── octomap/
│       ├── 01_octomap_build_rviz.mp4
│       ├── 02_octomap_final_isometric.png
│       ├── 03_octomap_final_top.png
│       ├── 04_octomap_final_side.png
│       ├── 05_octomap_3d_orbit.mp4
│       ├── map.bt
│       ├── map.ot              # when a full-tree export is produced
│       ├── octomap.rviz
│       └── README.md
└── ISR_5th_floor/
    └── ... same structure ...
```

## PointCloud2 evidence

### `01_accumulation_rviz.mp4`
RViz2 screen recording while the verified static rosbag is replayed. `/unilidar/cloud` is displayed in fixed frame `unilidar_lidar` with a display decay time longer than the complete scan, so successive frames remain visible and the room cloud progressively accumulates.

This verifies:
- rosbag replay;
- correct `sensor_msgs/msg/PointCloud2` interpretation by RViz;
- correct frame ID;
- temporal continuity of the acquisition;
- final spatial accumulation.

### Final PNG captures
The final accumulated cloud is captured from repeatable RViz viewpoints:
- isometric;
- top;
- side.

These are the reference figures for the report.

## OctoMap evidence

OctoMap is built from the selected static PointCloud2 input with an explicitly documented resolution and sensor maximum range. The initial project baseline is 0.10 m resolution and 15 m maximum range, but any parameter change used for a comparison must be recorded in the environment README/configuration.

### `01_octomap_build_rviz.mp4`
RViz recording while the occupancy map is incrementally constructed.

### Final OctoMap captures
Reference RViz captures from isometric, top and side perspectives.

### `05_octomap_3d_orbit.mp4`
A screen recording of RViz while the camera is moved around the completed 3D occupancy map. It is meant to reveal holes, occlusions, wall thickness, spurious voxels and map shape from several perspectives.

### Reopenable map data
- `map.bt`: OctoMap binary occupancy tree, suitable for compact storage and later loading.
- `map.ot`: full OctoMap tree when generated/required.
- `octomap.rviz`: RViz display configuration used to inspect the map.

The upstream ROS 2 `octomap_server` project provides `octomap_saver_node`; the saved map path must use `.bt` or `.ot`. No screenshot or video is accepted as a substitute for the underlying map file.

## Human presence / occlusion rule

Two people were present during the HcMR acquisition. The RViz PointCloud2 evidence intentionally shows what the sensor actually measured. Human returns are not silently removed from the source visual record.

A separately processed/cleaned cloud may be visualized later, but it must be clearly labelled as **derived** and never replace the raw accumulated RViz evidence. Surfaces hidden behind people remain unknown; they are not synthetically filled.

## Reproducibility rule

Every accepted image or video must be traceable to:
1. source rosbag;
2. exact RViz configuration;
3. processing/map configuration if derived;
4. command or workflow used to replay/generate the result.

This makes the repository a visual audit trail rather than a gallery of untraceable renders.
