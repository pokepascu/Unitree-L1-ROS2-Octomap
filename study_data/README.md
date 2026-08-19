# Static subsets for mapping Approaches 1 and 2

These MCAPs are derived **only from intervals verified as stationary by `/odom`**, using thresholds of 0.02 m/s linear speed and 0.02 rad/s angular speed. No interval is artificially extended with robot motion merely to reach 30 seconds.

## Approach 1 — single static scan

- HcMR laboratory: the longest strict stationary period found in the continuous HcMR bag is about **15.1 s**.
- ISR 5th floor: a strict stationary period of about **35.3 s** is available.

The HcMR subset therefore does **not** meet the original ~30 s duration target. This limitation must be stated in the experimental report, or a dedicated static recording should be used/re-recorded if identical acquisition duration is required.

## Approach 2 — three static scans + ICP

Three spatially distinct stationary views are provided for each environment. Selection prioritizes genuine stationarity and local geometric overlap for Iterative Closest Point (ICP), rather than selecting long but widely separated stops.

HcMR durations are approximately **13.7 s, 15.1 s and 7.4 s**. ISR 5th-floor durations are approximately **35.3 s, 3.3 s and 3.5 s**. The two short ISR stops are scientifically usable as stationary point-cloud acquisitions, but they do not reproduce the planned 30 s-per-station protocol. A new acquisition is recommended if protocol fidelity is required for the final quantitative comparison.

Each scan directory contains:

- `static_segment.mcap` — derived standalone MCAP;
- `metadata.yaml` — rosbag2 metadata rebuilt for the subset;
- `selection.yaml` — exact source, timestamps, duration, approximate odometric pose, topic counts and selection note.

`static_selection_report.csv` summarizes all selected intervals. The full immutable source recordings remain under `bags/raw/`.
