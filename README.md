# Unitree 4D LiDAR L1 — ROS 2 Humble

Environnement reproductible pour compiler, lancer, contrôler et enregistrer les
données du Unitree 4D LiDAR L1 sous ROS 2 Humble, sans installer ROS sur l’hôte
Ubuntu 24.04.

## État actuel

- Hôte inventorié : Ubuntu 24.04.2 LTS, `x86_64`.
- Docker et Docker Compose opérationnels.
- Environnement cible : Ubuntu 22.04 Jammy + ROS 2 Humble dans Docker.
- SDK Unitree figé : `v1.0.16`, commit
  `1bd7d95d8ab7ce7a22058d2bb07e39fd62612aa6`.
- Image Humble construite et pilote compilé contre PCL 1.12 sans patch fournisseur.
- Paquet `l1_monitor` compilé et testé : diagnostics cloud/IMU sur `/diagnostics`.
- X11, accélération OpenGL et démarrage contrôlé de RViz2 validés sans capteur.
- LiDAR réel validé : cloud ~8–10 Hz, IMU ~210–250 Hz et rosbag2 de référence.
- OctoMap 2.3.1 compilé et relié au cloud réel par `l1_octomap_bringup`.
- Carte de banc non vide validée ; la cartographie mobile/Point-LIO reste à faire.

## Architecture

```text
Ubuntu 24.04 (hôte)
└── Docker Ubuntu 22.04 + ROS 2 Humble
    └── ros2_ws
        ├── unilidar_sdk (source fournisseur non modifiée)
        ├── octomap_mapping (source externe figée)
        ├── l1_bringup (lancement configurable du projet)
        └── l1_octomap_bringup (adaptation et RViz OctoMap)
```

Le Compose principal fonctionne sans LiDAR. Le fichier
`docker/compose.lidar.yaml` ajoute explicitement le périphérique série seulement
lorsqu’il a été identifié sur l’hôte.

## Frontière Docker obligatoire

Ubuntu 24.04 sert uniquement d'hôte Docker, de serveur d'affichage X11 et de
passerelle vers le GPU et le port série. Les exécutables `ros2`, le pilote L1,
OctoMap et `rviz2` tournent dans l'image Ubuntu 22.04 + ROS 2 Humble. Une fenêtre
RViz visible sur le bureau Ubuntu ne signifie donc pas que RViz tourne sur
l'hôte : seul son affichage traverse le socket X11.

Chaque wrapper ROS appelle maintenant `assert-ros-container.sh`, qui refuse
l'exécution hors Docker et vérifie `/.dockerenv`, Ubuntu 22.04, ROS Humble et
les binaires sous `/opt/ros/humble`. Les trois launch files du projet vérifient
aussi `/.dockerenv`, de sorte qu'un lancement direct qui contournerait les
wrappers est refusé. Après un lancement graphique, la preuve utilisateur est :

```bash
./scripts/verify-docker-only.sh
```

Les verdicts attendus sont `HOST_NATIVE_RVIZ_ABSENT` et
`DOCKER_ONLY_PIPELINE_PASS`, accompagnés de la ligne du processus RViz issue de
`docker top`. Ne jamais lancer `rviz2`, `ros2 launch` ou
`source /opt/ros/...` directement au prompt hôte `isr@...`.

## Préparation

```bash
cd ~/unitree_l1_project
./scripts/docker-build.sh
./scripts/fetch-dependencies.sh
./scripts/workspace-build.sh
./scripts/smoke-test.sh
```

`workspace-build.sh` vérifie aussi automatiquement la présence et le commit du SDK.

Pour ouvrir un shell Humble avec accès graphique et détection automatique du
LiDAR connecté :

```bash
./scripts/docker-shell.sh
```

Depuis `/workspace/ros2_ws`, la commande simple suivante compile uniquement les
six paquets ROS 2 autorisés :

```bash
colcon build
source install/setup.bash
```

Pour tester l’accès X11 avant RViz2 :

```bash
./scripts/gui-smoke-test.sh
```

Les commandes matérielles ne doivent être utilisées qu’après identification du
périphérique avec `./scripts/check-lidar.sh`.

## Lorsque le L1 sera connecté

La procédure complète et les précautions électriques sont dans
`docs/hardware-runbook.md`. Le chemin nominal est :

```bash
./scripts/check-lidar.sh
START_RVIZ=false ./scripts/lidar-launch.sh
# Dans un second terminal :
./scripts/lidar-validate.sh
```

Après validation des messages, relancer avec `START_RVIZ=true`, puis enregistrer
un essai borné :

```bash
BAG_LABEL=validation BAG_DURATION_SEC=30 ./scripts/record-bag.sh
```

Pour une carte OctoMap de banc avec le LiDAR parfaitement immobile :

```bash
./scripts/docker-shell.sh
# Dans Docker :
ros2 launch l1_octomap_bringup unitree_l1_octomap.launch.py \
  static_sensor:=true rviz:=true
```

Si le runtime nommé `unitree_l1_runtime` est déjà lancé par
`scripts/lidar-launch.sh`, la commande hôte courte suivante démarre uniquement
la couche OctoMap et RViz2 sans guillemets à recopier :

```bash
OCTOMAP_RVIZ=true ./scripts/octomap-launch.sh
```

Pendant la cartographie, une vérification automatique confirme que la carte
binaire et les voxels occupés sont non vides :

```bash
./scripts/verify-docker-only.sh
./scripts/evaluate-octomap.sh
```

Pour sauvegarder avec les contrôles du projet, puis rouvrir la carte sans le
LiDAR :

```bash
./scripts/save-octomap.sh my_room_01.bt
./scripts/inspect-octomap.sh my_room_01.bt
./scripts/view-octomap.sh my_room_01.bt
```

La commande officielle montrée dans le README OctoMap est appelée par
`save-octomap.sh`. Le texte `(path for saving octomap)` est un emplacement à
remplacer, et non du texte à saisir. Le tutoriel OctoMap donne aussi la variante
directe complète dans Docker.

Ne pas utiliser ce TF statique si le capteur bouge. Un robot mobile doit lancer
`static_sensor:=false` et fournir une TF dynamique issue d'une odométrie ou d'un
SLAM. OctoMap construit l'occupation 3D mais n'est pas lui-même l'estimateur de
pose : ATE, RPE, dérive et fermeture de boucle doivent être évaluées sur la
trajectoire publiée par cet estimateur externe.

## Documentation et traçabilité

- `docs/configuration-log.md` : chronologie des commandes et résultats.
- `docs/decisions.md` : choix techniques et justification.
- `docs/versions-lock.md` : versions, commits et digests.
- `docs/validation-matrix.md` : critères de test et verdicts.
- `docs/sources.md` : sources officielles consultées.
- `docs/hardware-runbook.md` : branchement, lancement, validation, bag et rejeu.
- `docs/report/pdf/` : tous les PDF canoniques, classés par étape.
- `docs/report/pdf/01_environment/CONFIGURATION_LOG_UNITREE_L1.pdf` : version PDF du journal
  chronologique de configuration.
- `docs/report/pdf/01_environment/COMPLETE_CONFIGURATION_REPORT_UNITREE_L1.pdf` : rapport
  anglais complet de la configuration depuis l'audit initial jusqu'aux données
  réelles, rosbag2, OctoMap, incidents, validations et limites.
- `docs/report/pdf/02_lidar_and_rviz/DOCKER_RVIZ2_USAGE_REPORT_UNITREE_L1.pdf` : rapport
  anglais complet sur l'utilisation de RViz2 exclusivement dans Docker, avec
  profils, modes live/replay/OctoMap, preuve du processus et dépannage.
- `docs/report/pdf/02_lidar_and_rviz/TUTORIAL_COLCON_RVIZ2_RECORD_UNITREE_L1.pdf` : tutoriel complet
  colcon, RViz2, rosbag2 et rejeu.
- `docs/report/pdf/03_octomap_mapping/TUTORIAL_DOCKER_LIDAR_RVIZ_OCTOMAP_UNITREE_L1.pdf` :
  guide de démarrage pas à pas, entièrement Docker, du L1 au nuage RViz2 puis
  à la carte OctoMap, sa validation, sa sauvegarde et sa réouverture.
- `docs/report/pdf/03_octomap_mapping/TUTORIAL_UNITREE_L1_OCTOMAP_MAPPING.pdf` : procédure
  de lancement OctoMap, RViz2 en direct, sauvegarde, réouverture et critères
  d'évaluation d'une carte.
- `docs/report/pdf/03_octomap_mapping/RAPPORT_CONFIGURATION_UNITREE_L1_OCTOMAP.pdf` : rapport
  de configuration et validation réelle de la chaîne L1 -> OctoMap.
- `docs/report/pdf/03_octomap_mapping/JOURNAL_MATERIEL_COMMANDES_UNITREE_L1_20260716_EN.pdf` : journal
  anglais exhaustif des 86 entrées et commandes terminal.
- `docs/report/pdf/03_octomap_mapping/TUTORIAL_UNITREE_L1_OCTOMAP_MAPPING_EN.pdf` et
  `RAPPORT_CONFIGURATION_UNITREE_L1_OCTOMAP_EN.pdf` : copies anglaises explicites
  des deux documents OctoMap.
- `docs/report/pdf/00_preparation/SYNTHESE_UNITREE_L1_PRE_MATERIEL.pdf` : synthèse A4 de
  trois pages.
- `scripts/build-synthesis-pdf.sh` : reconstruction locale de cette synthèse.
- `scripts/build-docker-lidar-rviz-octomap-tutorial-pdf.sh` : reconstruction du
  tutoriel Docker L1/RViz2/OctoMap.
- `scripts/build-complete-reports-pdf.sh` : reconstruction et contrôle A4 des
  deux rapports complets configuration et RViz2/Docker.
- `scripts/build-trace-archive.sh` : ZIP des documents, preuves et historique Git.
- `docs/archive/` : traces historiques conservées sans réécriture.

Les rapports PDF actuels sont produits à partir de ces preuves. La prochaine
version ajoutera les essais de pose et de cartographie mobile après validation
d'un estimateur SLAM.

## Dépôt Git

Le projet est déjà un dépôt Git local sur la branche `main`. Pour le publier
dans votre propre dépôt distant vide :

```bash
cd /home/isr/unitree_l1_project
git remote add origin URL_DE_VOTRE_DEPOT
git push -u origin main
```

Si `origin` existe déjà, utiliser `git remote set-url origin ...`. Le guide
`docs/report/pdf/01_environment/GUIDE_STRUCTURE_PROJET_UNITREE_L1.pdf` explique aussi le cas
d'un dépôt distant non vide et les fichiers volontairement exclus de Git.
