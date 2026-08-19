# Static datasets derived for mapping Approaches 1 and 2

These are **derived 30-second ROS 2 MCAP subsets** extracted from the immutable recordings in `bags/raw/`. Every subset preserves the recorded messages inside its selected time interval, including LiDAR, IMU, odometry, TF and velocity commands when present.

## Approach 1 — single static scan

- `approach_1_single_static/HcMR_lab/scan_01/static_30s.mcap`
- `approach_1_single_static/ISR_5th_floor/scan_01/static_30s.mcap`

Purpose: accumulate a stationary Unitree L1 point cloud for approximately 30 s, inspect LiDAR quality and generate an occupancy representation with OctoMap without introducing a continuously estimated trajectory.

## Approach 2 — three static scans + ICP

- `approach_2_three_static_icp/HcMR_lab/scan_01..03/`
- `approach_2_three_static_icp/ISR_5th_floor/scan_01..03/`

Purpose: independently accumulate three stationary clouds, use known/estimated scanner poses as initial information, refine cloud-to-cloud registration with **Iterative Closest Point (ICP)**, merge the registered clouds and generate an OctoMap.

## Reproducible static-window selection

`tools/extract_static_rosbags.py` evaluates sliding 30 s windows using `/odom`. Lower scores correspond to lower observed motion and combine:

- positional spread around the median pose;
- accumulated odometric path length;
- yaw variation;
- 95th-percentile linear speed;
- 95th-percentile angular speed.

The selector avoids overlapping windows and preferentially chooses spatially distinct poses. `selection.yaml` beside each derived bag contains the exact source, absolute start/end timestamps and residual-motion metrics. `static_selection_report.csv` summarizes the three selected stations per environment.

**Scientific limitation:** “static” here means *supported by recorded robot odometry as a low-motion interval*. It is not external motion-capture ground truth. Before the three poses are used as absolute geometric ground truth, their physical locations should be independently measured/documented.

## LiDAR extrinsic available for later mobile mapping

Confirmed translation `base_link -> unilidar_lidar`: **(0.0, 0.0, 1.0) m**. The rotational extrinsic remains to be explicitly confirmed.
