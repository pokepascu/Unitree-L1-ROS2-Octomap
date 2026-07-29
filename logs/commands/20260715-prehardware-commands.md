# Registre condensé des commandes — jalon avant matériel

Les secrets, cookies X11 et identifiants temporaires ne sont jamais reproduits.
Les sorties longues sont conservées dans `logs/builds/` et `logs/tests/`; les
résultats et incidents sont interprétés dans `docs/configuration-log.md`.

## Lecture et inventaire

```bash
pdfinfo dossier_configuration_unitree_l1_ros2.pdf
pdftotext -layout dossier_configuration_unitree_l1_ros2.pdf -
lsb_release -a
uname -a
lscpu
free -h
df -hT
lspci -nnk
nvidia-smi
ip -brief link
ip -brief address
ip route
lsusb
lsusb -t
docker version
docker info
docker compose version
docker ps -a
docker images --digests
docker system df
git --version
command -v gcc g++ make cmake colcon ros2 python3 pip3 rviz2
```

## Initialisation et dépendance Unitree

```bash
mkdir -p docker ros2_ws/src config launch scripts bags maps logs docs/records docs/references
git init
git branch -m main
docker buildx imagetools inspect ros:humble-ros-base-jammy
git clone --branch v1.0.16 --depth 1 \
  https://github.com/unitreerobotics/unilidar_sdk.git ros2_ws/src/unilidar_sdk
git -C ros2_ws/src/unilidar_sdk rev-parse HEAD
git -C ros2_ws/src/unilidar_sdk describe --tags --exact-match
```

## Image et versions

```bash
./scripts/docker-build.sh
docker image inspect unitree-l1:humble-v1.0.16
dpkg-query -W libpcl-dev
ros2 --help
colcon version-check
rviz2 --help
```

Incidents corrigés : `pkg-config --modversion pcl_common` ne trouve pas de fichier
`.pc`; une requête `dpkg-query` a d'abord subi une expansion `${Package}` sous
`set -u`; un sourcing ROS après `set -u` a signalé
`AMENT_TRACE_SETUP_FILES: unbound variable`. Les contrôles corrigés utilisent
respectivement `dpkg-query`/CMake, le format par défaut de dpkg, et le sourcing ROS
avant `nounset`.

## rosdep et builds

```bash
rosdep check --from-paths src/l1_bringup \
  src/unilidar_sdk/unitree_lidar_ros2 --ignore-src --rosdistro humble
rosdep install --simulate --from-paths src/l1_bringup \
  src/unilidar_sdk/unitree_lidar_ros2 --ignore-src --rosdistro humble \
  --skip-keys "ament_python pcl" -r -y
./scripts/workspace-build.sh
```

Le premier check signale les deux clés sans définition rosdep. La simulation
ciblée et tous les builds corrigés terminent avec code 0.

## Tests ROS et graphiques

```bash
./scripts/smoke-test.sh
docker compose -f docker/compose.yaml run --rm dev bash -lc \
  'source /workspace/ros2_ws/install/setup.bash; \
   colcon test --packages-select l1_monitor l1_bringup unitree_lidar_ros2; \
   colcon test-result --all --verbose'
./scripts/gui-smoke-test.sh
timeout --signal=INT --kill-after=3s 8s \
  rviz2 -d /workspace/ros2_ws/install/l1_bringup/share/l1_bringup/config/unitree_l1.rviz
```

Résultats : smoke code 0, 8 tests projet sur 8, rendu direct Intel/OpenGL 4.6,
RViz actif 8 s puis code timeout 124 attendu.

## Pilote et moniteur sans capteur

```bash
ros2 launch l1_bringup unitree_l1.launch.py \
  port:=/dev/unitree_absent_audit rviz:=false monitor:=false
ros2 node list
ros2 topic list -t
ros2 topic info -v /unilidar/cloud
ros2 topic info -v /unilidar/imu
ros2 param get /unitree_lidar_ros2_node port
timeout 3s ros2 topic echo /unilidar/cloud --once
timeout 3s ros2 topic echo /unilidar/imu --once
```

Les deux echos expirent sans donnée, ce qui est attendu. Le test direct de l'ELF
avec SIGINT est retenu pour l'arrêt ; un premier harnais launch a nécessité TERM et
ne sert pas de preuve d'arrêt gracieux.

Le moniteur a ensuite été testé par son exécution directe sans publishers et par
des publishers synthétiques PointCloud2 (~10 Hz) et Imu (~30 Hz). La commande
reproductible est :

```bash
./scripts/monitor-synthetic-test.sh
```

## Préparation matérielle sans L1

```bash
./scripts/check-lidar.sh
./scripts/lidar-launch.sh
```

Le premier trouve 0 port série et ne modifie rien. Le second refuse code 2 avant
Docker. Aucun test `lidar-validate`, rosbag2 ou Point-LIO n'est présenté comme
exécuté tant que le L1 n'est pas connecté.

## Conservation

```bash
sha256sum docs/references/dossier_configuration_unitree_l1_ros2.pdf
sha256sum logs/builds/*.log logs/tests/*.log
sha256sum ros2_ws/build/unitree_lidar_ros2/unitree_lidar_ros2_node
sha256sum ros2_ws/src/unilidar_sdk/unitree_lidar_sdk/lib/x86_64/libunitree_lidar_sdk.a
git -C ros2_ws/src/unilidar_sdk status --short
docker ps --filter name=unitree
```

Le vendor est propre et aucun conteneur projet/audit ne reste actif au jalon.
