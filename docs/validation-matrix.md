# Matrice de validation

| ID | Exigence | Commande / méthode | Attendu | Verdict |
|---|---|---|---|---|
| TST-001 | Construction depuis les fichiers figés | `./scripts/docker-build.sh` | build sans erreur | PASS 2026-07-15, rc 0 |
| TST-002 | Ubuntu Jammy | `/etc/os-release` dans l’image | 22.04 | PASS |
| TST-003 | ROS 2 Humble | `$ROS_DISTRO`, `ros2` | Humble disponible | PASS |
| TST-004 | Outils ROS | `colcon`, `rosdep`, `rviz2` | commandes présentes | PASS |
| TST-005 | Pilote Unitree | `./scripts/workspace-build.sh` | compilation Humble/PCL réussie | PASS, 3 paquets |
| TST-006 | Lancement configurable | `./scripts/smoke-test.sh` | port et options exposés | PASS, rc 0 |
| TST-007 | X11/DRI | `./scripts/gui-smoke-test.sh` | X11 et rendu direct | PASS, Intel/OpenGL 4.6 |
| TST-008 | RViz2 | démarrage contrôlé 8 s | fenêtre initialisée sans erreur | PASS, timeout 124 attendu |
| TST-009 | Périphérique L1 | `check-lidar.sh` | port série stable | PASS 2026-07-16, CP2104 `02C90122`, `/dev/ttyUSB0` |
| TST-010 | Topics cloud/IMU | `lidar-validate.sh` sans puis avec RViz | messages cohérents | PASS x2, cloud ~8 Hz, IMU ~210 Hz |
| TST-011 | Rosbag2 | enregistrement/rejeu | données reproductibles | PASS, 29,34 s, 6 400 messages, rejeu rc 0 |
| TST-012 | Point-LIO/carte | bag puis PCD | trajectoire/carte cohérentes | PENDING |
| TST-013 | ABI du pilote | `readelf`, `ldd`, symboles GLIBCXX | aucune dépendance absente | PASS |
| TST-014 | Tests projet | `colcon test` et `test-result` | 0 échec | PASS, 8/8 |
| TST-015 | Graphe sans capteur | launch sur port absent | nœud/topics/paramètres observables | PASS_CONTRACT_ONLY |
| TST-016 | Arrêt du pilote | Ctrl-C sur runtime matériel avec RViz | arrêt avant SIGKILL | PASS, pilote/moniteur/RViz propres après correctif |
| TST-017 | Alarme sans données | `/diagnostics` après timeout | cloud et IMU en ERROR | PASS |
| TST-018 | Moniteur synthétique | publishers 10/30 Hz | deux diagnostics sains | PASS |
| TST-019 | Refus sans périphérique | `lidar-launch.sh` sans L1 | arrêt avant Docker | PASS, rc 2 attendu |
| TST-020 | Intégrité fournisseur | commit et `git status` vendor | commit attendu, dépôt propre | PASS |
| TST-021 | Style Python ROS 2 | `ament_flake8`, `ament_pep257` | aucun problème | PASS, 13 fichiers |
| TST-022 | RViz sur flux réel | `START_RVIZ=true ./scripts/lidar-launch.sh` | nuage consommé sans perte de flux | PASS, OpenGL 4.6 et validation complète |
| TST-023 | Horloge de rejeu | `replay-bag.sh` avec `/clock` | diagnostics sains sur timestamps enregistrés | PASS après `use_sim_time`, rc 0 |
| TST-024 | Commande `colcon build` simple | nouveau conteneur, racine du workspace | seulement les paquets ROS 2, build complet | PASS, 6 paquets, rc 0 |
| TST-025 | Shell GUI + LiDAR | `docker-shell.sh`, X11/DRI et tty ciblé | affichage direct et `/dev/unitree_lidar` accessible | PASS, OpenGL 4.6, rc 0 |
| TST-026 | OctoMap sur L1 réel immobile | launch complet, TF de banc, sonde MarkerArray | carte occupée non vide | PASS, ~7 Hz, 13 247 points |
| TST-027 | Tests des paquets projet | `colcon test` sur les trois paquets `l1_*` | aucun échec | PASS, 15/15 |
| TST-028 | Arrêt du graphe OctoMap | SIGINT, contrôle conteneur et tty | processus propres, port libéré | PASS |
| TST-029 | Journal PDF lisible | générateur, `pdftotext`, `pdfinfo`, inspection pages CMD-066 | titre et commande sur la même page, A4 | PASS, 17 pages |
| TST-030 | Tutoriel colcon/RViz2/rosbag2 | générateur, `pdftotext`, `pdfinfo`, inspection pages | commandes compile, record, replay et RViz2 | PASS, 9 pages A4 |
| TST-031 | L1 réel vers OctoMap | launch bench, topics/services, sonde MarkerArray | marqueurs occupés et TF valide | PASS, ~8.29 Hz, 17 marqueurs, 13 247 points |
| TST-032 | Sauvegarde carte OctoMap | `./scripts/save-octomap.sh l1_real_bench_20260716.bt` | fichier `.bt` non vide, service binaire | PASS, 18 902 octets, 67 533 noeuds |
| TST-033 | Documentation OctoMap classée | générateur OctoMap, `pdftotext`, `pdfinfo` | tutoriel + rapport A4 dans `03_octomap_mapping` | PASS, 2 PDF |
| TST-034 | Journal anglais exhaustif | `./scripts/build-english-command-journal-pdf.sh` | toutes les entrées/commandes, texte extractible, A4 | PASS, 86 entrées, 23 pages |
| TST-035 | Copies anglaises OctoMap | `./scripts/build-english-octomap-guides-pdf.sh` | tutoriel + rapport `_EN`, texte identique, A4 | PASS, 2 × 9 pages |
| TST-036 | Étape 3 OctoMap dans Docker | présence setups + `ros2 pkg prefix` + `ros2 launch ... --show-args` | overlay trouvé et commande résolue dans le runtime | PASS, contexte hôte/conteneur corrigé dans les 2 PDF |
| TST-037 | Wrapper de lancement OctoMap | `octomap-launch.sh --check`, syntaxe et cas d'erreur | aucune quote à copier, runtime/overlay validés, erreurs bornées | PASS, runtime réel; rc négatifs 2/3/2 |
| TST-038 | Inspection d'une carte sauvegardée | `./scripts/inspect-octomap.sh l1_bench_map_20260716.bt` | en-tête `.bt`, résolution, taille et hash valides | PASS, 58 202 noeuds, 0,10 m, 23 276 octets |
| TST-039 | Rejeu et visualisation d'une carte | `view-octomap.sh` headless puis RViz2 | serveur chargé, MarkerArray latched et GUI OpenGL | PASS, 13 672 points occupés, OpenGL 4.6 |
| TST-040 | Sonde de santé de cartographie | `RUNTIME_CONTAINER=unitree_l1_map_viewer ./scripts/evaluate-octomap.sh` | carte binaire et voxels non vides, mode identifié | PASS, `OCTOMAP_MAPPING_HEALTH_PASS` |
| TST-041 | Saver officiel du README | `ros2 run octomap_server octomap_saver_node --ros-args -p octomap_path:=/tmp/github_readme_validation.bt` | `.bt` valide reçu depuis le serveur | PASS, 58 202 noeuds, 23 276 octets |
| TST-042 | Régression paquet saved-map | `colcon test --packages-select l1_octomap_bringup` | launch/config installés et interfaces testées | PASS, 7/7 |
| TST-043 | Refus ROS/RViz sur l'hôte | garde shell au prompt Ubuntu 24.04 + garde `/.dockerenv` des trois launch files | arrêt avant toute commande ou graphe ROS | PASS, rc 40 `DOCKER_RUNTIME_ASSERT_FAIL` + tests launch |
| TST-044 | Identité du runtime Docker | garde dans l'image et `verify-docker-only.sh` | Ubuntu 22.04, Humble, binaires `/opt/ros/humble` | PASS, `DOCKER_ROS_RUNTIME_PASS` |
| TST-045 | Processus RViz conteneurisé | viewer `.bt`, `docker top`, racine `/proc/PID/root/.dockerenv` | RViz dans `unitree_l1_map_viewer`, aucun RViz natif hôte | PASS, chemin `/opt/ros/humble/lib/rviz2/rviz2` |
| TST-046 | Régression des wrappers Docker | workspace build, smoke, GUI smoke, monitor synthétique, bag info, OctoMap check et `colcon test` | garde commun puis commande fonctionnelle | PASS, 6 paquets, OpenGL 4.6, bag 6 400 messages, 15/15 tests |
| TST-047 | Tutoriel Docker L1 vers RViz2 et OctoMap | générateur, `pdfinfo`, `pdftotext`, inspection visuelle des 12 pages, `inspect-octomap.sh` et `view-octomap.sh --check` | A4, étapes hôte/conteneur explicites, verdicts et carte de référence valides | PASS, 12 pages; 58 202 nœuds à 0,10 m; viewer domaine 43 |
| TST-048 | Rapports complets configuration et RViz2/Docker | `build-complete-reports-pdf.sh`, `pdfinfo`, `pdftotext`, recherche de directives roff et inspection visuelle de toutes les pages | 2 PDF A4, marqueurs requis, commandes non tronquées, aucune directive de mise en page visible | PASS, 27 + 17 pages; 44 pages inspectées; aucun `.CMD` résiduel |
| TST-049 | Fiche d'accès direct au shell Docker L1/OctoMap/RViz2 | `build-docker-access-tutorial-pdf.sh`, `pdfinfo`, `pdftotext` et rendu visuel des 6 pages | A4, contexte `host$`/`ros$`, vérifications GUI/LiDAR et lancement combiné lisibles | PASS révisé, 6 pages; typo et runtime unique ajoutés; SHA-256 `da1cfb631403217c62f8e9fdf557655107990ba978918b47da04ca5efb70dbef` |
| TST-050 | Unicité du runtime live avant RViz2 | `docker ps`, `docker top`, logs moniteur et `ros2 node list` dans le domaine 42 | un conteneur, un pilote, un OctoMap et un flux cloud non nul | FAIL_DIAGNOSED 2026-07-23 : 3 conteneurs, 2 graphes dupliqués, cloud 0 Hz; redémarrage propre en attente |
| TST-051 | Conservation de `rviz:=true` dans le launch combiné | `GroupAction(scoped=True)`, test LaunchService, 9 tests paquet et launch headless sans LiDAR | enfants `false`, parent `true`, exactement un processus RViz au bon profil | PASS : 9/9; `COMBINED_RVIZ_SCOPE_PASS rviz_processes=1 launch_rc=124 lidar=absent` |
| TST-052 | Manuel ingénieur L1/Docker/RViz2/OctoMap | générateur, lint des blocs Bash, options ROS Humble, `pdfinfo`, `pdftotext`, 813 lignes de code et inspection visuelle | trois parties, A4, commandes copiables, aucune ligne/page perdue, frontière OctoMap/SLAM exacte | PASS : 30 pages, 813/813 lignes, 83 055 octets, SHA-256 `13b6dbee62957330f005d4a091d33e0720d2f6520db20e526027fba5d8f52fbf` |

`PASS_CONTRACT_ONLY` confirme uniquement le contrat ROS statique. TST-010 est
désormais validé séparément par réception de messages réels. Le paquet fournisseur
ne définit aucun test CTest ; les 15 tests comptés appartiennent à `l1_monitor`,
`l1_bringup` et `l1_octomap_bringup`. Le journal détaillé de la session matérielle se trouve dans
`docs/report/journal_materiel_commandes_20260716.md` et son PDF associé. Les
preuves OctoMap sont dans `logs/tests/20260716-existing-runtime-octomap-observation.log`
et `logs/tests/20260716-octomap-map-save.log`.
