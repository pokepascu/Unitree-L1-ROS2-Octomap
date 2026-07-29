# Sources techniques

Consultées le 15 juillet 2026.

- SRC-000 — Dossier de cadrage fourni par Pascual, 11 pages A4 :
  `docs/references/dossier_configuration_unitree_l1_ros2.pdf`, SHA-256
  `848185726cf4899efac63df62cfdef21985ec3b042eec9e52ae26113b5b84661`.

- SRC-001 — ROS 2 Humble, plateformes et durée de support :
  <https://docs.ros.org/en/humble/Releases/Release-Humble-Hawksbill.html>
- SRC-002 — Image Docker ROS officielle :
  <https://hub.docker.com/_/ros/>
- SRC-003 — Docker Engine sur Ubuntu :
  <https://docs.docker.com/engine/install/ubuntu/>
- SRC-004 — Unitree UniLiDAR SDK `v1.0.16` :
  <https://github.com/unitreerobotics/unilidar_sdk/tree/v1.0.16>
- SRC-005 — README ROS 2 Unitree et environnement officiellement vérifié :
  <https://github.com/unitreerobotics/unilidar_sdk/blob/v1.0.16/unitree_lidar_ros2/src/unitree_lidar_ros2/README.md>
- SRC-006 — Manuel officiel Unitree 4D LiDAR L1 :
  <https://oss-global-cdn.unitree.com/static/52b72f707b304d229d4321eea223738f.pdf>
  Copie locale : `docs/references/unitree_l1_user_manual.pdf`, 18 pages,
  SHA-256 `4d816cdf6197a51c5e87e6e7876da822b2d0e52e0bf63df306b40ac32fb13a74`.
  Pages utiles : p. 3 (11 Hz/250 Hz), p. 7 (12 V et TTL 3,3 V), p. 11
  (adaptateur/câblage fourni), p. 15 (12 V/1 A), p. 16 (TTL UART/2 Mbit/s).
- SRC-006A — Centre de téléchargement officiel L1 :
  <https://www.unitree.com/download/LiDAR/>
- SRC-007 — Référence Docker Compose, `devices`, `group_add` et sécurité :
  <https://docs.docker.com/reference/compose-file/services/>
- SRC-008 — Concepts QoS ROS 2 Humble :
  <https://docs.ros.org/en/humble/Concepts/Intermediate/About-Quality-of-Service-Settings.html>
- SRC-009 — Message ROS 2 `diagnostic_msgs/DiagnosticArray` :
  <https://docs.ros.org/en/humble/p/diagnostic_msgs/msg/DiagnosticArray.html>
- SRC-010 — Point-LIO Unitree officiel, actuellement ROS 1/Noetic :
  <https://github.com/unitreerobotics/point_lio_unilidar>
- SRC-011 — Port communautaire Point-LIO ROS 2 à évaluer après le bag réel :
  <https://github.com/dfloreaa/point_lio_ros2>
- SRC-012 — Dépôt officiel OctoMap mapping, branche ROS 2 et version 2.3.1 :
  <https://github.com/OctoMap/octomap_mapping/tree/2.3.1>
- SRC-015 — Dépôt officiel OctoMap mapping, branche ROS 2 demandée pour ce
  projet : <https://github.com/OctoMap/octomap_mapping/tree/ros2>
- SRC-016 — README officiel de la branche ROS 2, incluant le serveur et la
  commande de sauvegarde `octomap_saver_node` :
  <https://github.com/OctoMap/octomap_mapping/blob/ros2/README.md>
- SRC-013 — Configuration officielle de `colcon`, notamment le fichier
  workspace-local `colcon_defaults.yaml` :
  <https://colcon.readthedocs.io/en/released/user/configuration.html>
- SRC-014 — Arguments officiels de découverte `colcon`, dont `--base-paths` :
  <https://colcon.readthedocs.io/en/released/reference/discovery-arguments.html>

Le manuel officiel indique notamment l'adaptateur fourni et l'alimentation séparée,
le besoin 12 V / 1 A, l'interface TTL UART à 2 000 000 bit/s, environ 11 Hz pour
le balayage azimutal et 250 Hz pour le report IMU. Ces valeurs servent de référence
initiale ; les fréquences effectivement publiées par le driver seront mesurées.
