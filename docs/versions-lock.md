# Verrouillage des versions

| Élément | Version / identifiant | État |
|---|---|---|
| Hôte | Ubuntu 24.04.2 LTS Noble, x86_64 | vérifié |
| Noyau hôte | 6.17.0-35-generic | vérifié |
| Docker Engine | 29.6.1 | vérifié |
| Docker Compose | 5.3.1 | vérifié |
| Image de base | `ros:humble-ros-base-jammy` | vérifié |
| Digest amd64 | `sha256:5c793b92e0b12d6babb438cb20eed7766495fde6419a21e3d2e918464f09dc17` | figé |
| ROS 2 | Humble, `rclcpp 16.0.19`, `sensor_msgs 4.9.1` | vérifié |
| Ubuntu conteneur | 22.04 Jammy, amd64, glibc 2.35 | vérifié |
| Unitree SDK | `v1.0.16` | figé |
| Commit Unitree | `1bd7d95d8ab7ce7a22058d2bb07e39fd62612aa6` | vérifié |
| OctoMap mapping ROS 2 | `2.3.1`, commit `f79da9a9a1fcdf82e72dab4df288d6cc27c6e163` | figé et vérifié |
| OctoMap C++ | `liboctomap-dev 1.9.7+dfsg-3` | vérifié |
| OctoMap ROS 2 | `octomap_msgs 2.0.1`, `octomap_ros 0.4.4` | vérifié |
| Archive SDK x86_64 | SHA-256 `295efc9d55192483c66be291fe74ba0c3795c049c5e5286f650c6e7cf2d79cdf` | vérifié |
| PCL / Eigen / Boost | 1.12.1 / 3.4.0 / 1.74 | vérifié |
| `pcl_conversions` | 2.4.5 | vérifié |
| GCC / G++ | 11.4.0 ; archive fournisseur GCC 9.4 | vérifié |
| CMake / Python | 3.22.1 / 3.10.12 | vérifié |
| colcon / rosdep / vcstool | 0.21.0 / 0.26.0 / 0.3.0 | vérifié |
| RViz2 / Mesa | 11.2.27 / 23.2.1 | vérifié |
| Image projet | `unitree-l1:humble-v1.0.16` | construite |
| ID image projet | `sha256:2e9707a45f0ef0dfa3a8e37ecd28cd89c873493aacde3494fda2cc33115a8978` | vérifié après ajout OctoMap |
| Binaire pilote | 1 554 464 octets, SHA-256 `c7ed1cf9d632bb7cf04b95018a0395819578816fc81a821ac241e3278cbb61b0` | vérifié |
| GLIBCXX | requis ≤ 3.4.29 ; runtime disponible jusqu’à 3.4.30 | ABI vérifiée |

La base Docker est figée par digest et le SDK par commit. Les versions de tous les
paquets APT ne sont toutefois pas verrouillées individuellement : le résultat est
reconstructible depuis les fichiers et références consignés, mais il n'est pas
promis identique octet pour octet à une date future.
