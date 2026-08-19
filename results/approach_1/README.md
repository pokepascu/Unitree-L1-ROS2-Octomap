# Approach 1 - single stationary Unitree L1 scan

Derived analysis outputs for the verified static HcMR and ISR 5th-floor datasets.

The conservative cleaned cloud removes invalid/range-rejected and sparse statistical/radius outliers. Low-persistence near-field voxels are written separately as `dynamic_foreground_candidates.ply`; they are **not automatically deleted** from the conservative cloud. Compact vertical foreground clusters are reported as ambiguous review candidates rather than asserted to be people.

No hidden surface behind a person or other occluder is reconstructed from a single viewpoint.
