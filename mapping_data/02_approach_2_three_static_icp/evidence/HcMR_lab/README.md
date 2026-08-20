# Approach 2 — three stationary scans, globally constrained registration

The three original raw-scan RViz evidence folders are retained unchanged. Downstream registration is recomputed globally.

Because `base_link` and `unilidar_lidar` have exactly zero translation, the norm of each inter-scan transform translation must equal the robot-origin displacement measured by `/odom`. This norm is independent of the unknown constant LiDAR/base rotation. The pipeline therefore combines FPFH global hypotheses (Fast Global Registration and RANSAC), geometry multistart hypotheses, translation-norm-constrained ICP, and a three-edge cycle check (`2→1`, `3→2`, `3→1`). No LiDAR/base rotation is assumed.

`icp/registration_metrics.json` contains every selected transform, overlap/RMSE metrics, physical constraints and cycle residuals. The merged cloud and OctoMap are generated only after the acceptance gates pass. OctoMap still raycasts from the three distinct registered LiDAR origins and retains `.bt/.ot`, RViz construction video, three final perspectives and a 3D orbit.
