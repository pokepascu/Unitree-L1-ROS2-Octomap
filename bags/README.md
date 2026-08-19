# Unitree L1 source rosbags

Raw ROS 2 Humble recordings acquired on 7 August 2026 with the Unitree L1 3D LiDAR and the mobile platform.

| Dataset | Environment | Purpose |
|---|---|---|
| `raw/HcMR_lab_2026-08-07_21-13-45/` | HcMR laboratory | Laboratory continuous run |
| `raw/ISR_5th_floor_run_1_2026-08-07_21-31-58/` | ISR building, **5th floor** | Continuous mobile run 1 |
| `raw/ISR_5th_floor_run_2_2026-08-07_21-48-31/` | ISR building, **5th floor** | Continuous mobile run 2 |

The former “Floor 4” label was incorrect; the confirmed location is the **5th floor of the ISR building**.

Relevant recorded streams are `/unilidar/cloud`, `/unilidar/imu`, `/odom`, `/tf`, and `/cmd_vel`. The source MCAPs are retained unchanged and tracked through Git LFS.

Confirmed LiDAR translation relative to the mobile base:

```text
base_link -> unilidar_lidar
x = 0.0 m
y = 0.0 m
z = 1.0 m
```

The rotational extrinsic has not been independently specified and is therefore not invented here.
