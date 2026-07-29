# Journal de configuration — Unitree L1

Ce journal est chronologique. Il conserve les commandes, buts, effets, résultats,
erreurs, corrections et validations nécessaires au futur rapport PDF.

L’ancien journal issu d’un environnement restreint est conservé intact dans
`docs/archive/configuration-log.initial-incorrect.20260715.md` avec le SHA-256
`fa834c17d0f520e59fac194f00d9c591d160ee79c14d4049680d95e0bb2b35f8`.
Ses observations invalidées ne servent pas de référence hôte.

## LOG-20260715-001 — Lecture du dossier fourni

- Phase : P0 — cadrage.
- Type : inspection.
- Statut : SUCCÈS.
- But : lire la synthèse PDF fournie et sa feuille de route. L'agent n'a pas un
  accès séparé à une autre conversation ; le document est la source de continuité.
- Commandes :

```bash
pdfinfo dossier_configuration_unitree_l1_ros2.pdf
pdftotext -layout dossier_configuration_unitree_l1_ros2.pdf -
```

- Résultat : document de 11 pages lu intégralement ; phases P0 à P7, contraintes
  de sécurité et livrables identifiés.
- Effet : aucun fichier système modifié.

## LOG-20260715-002 — Inventaire direct de l’hôte

- Phase : P0 — inventaire.
- Type : inspection.
- Statut : SUCCÈS.
- But : établir l’état réel du PC avant installation.
- Commandes principales :

```bash
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
git --version
command -v gcc g++ make cmake colcon ros2 python3 pip3 rviz2
```

- Résultat : Ubuntu 24.04.2 LTS, noyau 6.17.0-35, x86_64, Intel i7-5500U,
  15 Gio de RAM, 850 Gio libres, Docker 29.6.1 et Compose 5.3.1 fonctionnels.
- Outils hôte : Git 2.43.0, Make 4.3 et Python 3.12.3 présents ; GCC, G++, CMake,
  colcon et ROS 2 absents.
- Matériel : aucun `ttyUSB*`/`ttyACM*` Unitree ; Ethernet sans porteuse.
- Décision : ne rien installer sur l’hôte ; compiler dans Docker Jammy/Humble.

## ERR-20260715-001 — Invalidations du journal préliminaire

- Statut : CORRIGÉ.
- Cause : les premières commandes avaient été exécutées dans un contexte restreint
  qui masquait des composants de l’hôte.
- Corrections démontrées :

| Observation initiale | Observation directe corrigée |
|---|---|
| Ubuntu Core 24 | Ubuntu 24.04.2 LTS Noble classique |
| Docker absent | Docker client/serveur 29.6.1 opérationnel |
| Compose inconnu | Docker Compose 5.3.1 |
| `lsusb` absent | `/usr/bin/lsusb` présent |
| Make absent | GNU Make 4.3 présent |
| espace disque ambigu | `/dev/sda2`, environ 850 Gio libres |

L’archive n’a pas été supprimée ni réécrite.

## LOG-20260715-003 — Vérification Docker existant

- Statut : SUCCÈS.
- Commandes : `docker ps -a`, `docker images --digests`, `docker system df`,
  `docker compose version`, `docker buildx version`.
- Résultat : un ancien environnement `ros2_ws:foxy` existe et reste hors périmètre ;
  aucun conteneur existant n’a été démarré, arrêté ou supprimé par l’agent principal.
- Décision : créer une image distincte `unitree-l1:humble-v1.0.16`.

## LOG-20260715-004 — Sources officielles et interface matérielle

- Statut : SUCCÈS.
- Résultat : le chemin standard Unitree est UART TTL 3,3 V à 2 000 000 bit/s vers
  l’adaptateur fourni, puis USB série, avec alimentation séparée 12 V/1 A.
- Conséquence : aucun adressage IP ni réseau hôte n’est requis pour le pilote série.
- Compatibilité : le fournisseur documente Foxy/PCL 1.10 ; Humble/PCL 1.12 doit être
  validé par compilation et tests locaux.

## LOG-20260715-005 — Création de la structure du projet

- Type : modification locale réversible.
- Statut : SUCCÈS.
- Commandes :

```bash
mkdir -p docker ros2_ws/src config launch scripts bags maps logs docs/records docs/references
git init
git branch -m main
```

- Résultat : arborescence créée sous `/home/isr/unitree_l1_project`, dépôt Git local
  initialisé sans publication ni commit.

## LOG-20260715-006 — Image de base ROS figée

- Statut : SUCCÈS.
- Commande :

```bash
docker buildx imagetools inspect ros:humble-ros-base-jammy
```

- Résultat amd64 : digest
  `sha256:5c793b92e0b12d6babb438cb20eed7766495fde6419a21e3d2e918464f09dc17`.
- Justification : éviter qu’un tag mutable change silencieusement la base du build.

## LOG-20260715-007 — SDK Unitree figé

- Statut : SUCCÈS.
- Commande :

```bash
git clone --branch v1.0.16 --depth 1 \
  https://github.com/unitreerobotics/unilidar_sdk.git \
  ros2_ws/src/unilidar_sdk
git -C ros2_ws/src/unilidar_sdk rev-parse HEAD
git -C ros2_ws/src/unilidar_sdk describe --tags --exact-match
```

- Résultat : tag `v1.0.16`, commit
  `1bd7d95d8ab7ce7a22058d2bb07e39fd62612aa6`, dépôt propre.
- Précaution : le vendor est exclu du dépôt parent et recréable via
  `config/dependencies.repos`.

## LOG-20260715-008 — Fichiers reproductibles initiaux

- Type : modification locale réversible.
- Statut : SUCCÈS.
- But : préparer Docker, Compose, scripts, configurations et traces sans LiDAR.
- Fichiers affectés : `README.md`, `AGENTS.md`, `.gitignore`, `.dockerignore`,
  `docker/`, `scripts/`, `config/` et `docs/`.
- Précautions : pas de `privileged`, pas de `chmod 777`, pas de ROS hôte, pas de
  périphérique obligatoire dans le Compose principal, cookie X11 monté en lecture
  seule et jamais journalisé.

## LOG-20260715-009 — Paquet de lancement configurable

- Type : développement projet.
- Statut : SUCCÈS, build et launch validés.
- But : éviter de modifier le `launch.py` fournisseur qui fixe `/dev/ttyUSB0`.
- Résultat : paquet `l1_bringup` avec arguments `port`, `cloud_topic`, `imu_topic`,
  `cloud_frame`, `imu_frame` et `rviz` ; paramètres Unitree originaux conservés.
- Effet matériel : aucun ; le launch ne sera pas exécuté avant la compilation.

## ERR-20260715-002 — Exclusion logique du paquet ROS 1

- Statut : CORRIGÉ AVANT EXÉCUTION.
- Symptôme anticipé : un `rosdep`/`colcon` global découvrirait aussi
  `unilidar_sdk/unitree_lidar_ros`, qui utilise ROS 1 `catkin`.
- Correction : limiter `--from-paths` et `--base-paths` au pilote ROS 2 et à
  `l1_bringup`.
- Justification : ne pas altérer le dépôt fournisseur avec un `COLCON_IGNORE`.

## ERR-20260715-003 — Cohérence du port et reconstruction des dépendances

- Statut : CORRIGÉ AVANT TEST MATÉRIEL.
- Problème 1 : l’override Compose expose `/dev/unitree_lidar` alors que le launch
  utilisait encore `/dev/ttyUSB0` par défaut.
- Correction 1 : la valeur par défaut du launch lit désormais `LIDAR_PORT`, avec
  repli sur `/dev/ttyUSB0` hors override.
- Problème 2 : le manifeste `dependencies.repos` n’était pas encore consommé.
- Correction 2 : `fetch-dependencies.sh` importe le SDK si absent et refuse de
  continuer si son commit ne correspond pas au verrou attendu.

## LOG-20260715-010 — Construction de l'image Humble

- Type : modification Docker locale ; aucune installation sur l'hôte.
- Statut : SUCCÈS.
- Commande : `./scripts/docker-build.sh`.
- Durée observée : environ 16 min 14 s au premier build.
- Résultat : image `unitree-l1:humble-v1.0.16`, ID
  `sha256:60dfcef73d6c3cd6efbb4842c946f25305ff460d8e9f9c8d1fdd8976a346de64`.
- Environnement obtenu : Ubuntu 22.04, ROS 2 Humble, GCC/G++ 11.4.0,
  CMake 3.22.1, Python 3.10.12, PCL 1.12.1 et RViz2 11.2.27.
- Taille affichée par Docker : 4,04 Go d'usage disque, contenu 914 Mo.

## ERR-20260715-004 — Détection de version PCL par `pkg-config`

- Statut : CORRIGÉ.
- Commande initiale : `pkg-config --modversion pcl_common`.
- Symptôme : aucun fichier `pcl_common.pc` n'est fourni par le paquet Jammy.
- Correction : lecture par `dpkg-query -W libpcl-dev` et
  `PCLConfigVersion.cmake` ; version confirmée : `1.12.1`.
- Conclusion : défaut de la méthode de contrôle, pas de l'image Docker.

## ERR-20260715-005 — Expansion prématurée dans une requête `dpkg`

- Statut : CORRIGÉ.
- Symptôme : `${Package}` a été interprété par le shell avec `set -u` avant
  d'être transmis à `dpkg-query`.
- Correction : utiliser la sortie par défaut de `dpkg-query` sans format contenant
  une expansion shell.
- Effet : aucun changement système ; simple commande de lecture relancée.

## ERR-20260715-006 — Ordre de chargement ROS et mode `nounset`

- Statut : CORRIGÉ.
- Symptôme : lors d'un diagnostic éphémère, `set -u` exécuté avant
  `source /opt/ros/humble/setup.bash` a provoqué
  `AMENT_TRACE_SETUP_FILES: unbound variable`.
- Correction : sourcer ROS avant d'activer `nounset`, ou laisser l'entrypoint de
  l'image sourcer ROS avant le script.
- Effet : aucun défaut de l'image et aucun fichier du projet modifié par l'essai.

## ERR-20260715-007 — Clés sans définition `rosdep` exploitable

- Statut : CORRIGÉ POUR LE BUILD.
- Symptôme : `rosdep check` signale les clés `ament_python` dans `l1_bringup` et
  `pcl` dans le manifeste fournisseur, bien que les composants requis soient déjà
  installés dans l'image.
- Vérification : une simulation avec
  `--skip-keys "ament_python pcl"` termine avec le code 0 et ne propose aucun
  paquet supplémentaire.
- Correction : le script de build ignore explicitement ces deux clés seulement ;
  toutes les autres dépendances restent contrôlées par `rosdep`.

## LOG-20260715-011 — Compilation Humble/PCL du pilote

- Phase : P2 — pilote.
- Statut : SUCCÈS.
- Commande : `./scripts/workspace-build.sh`.
- Résultat initial : code 0, `unitree_lidar_ros2` puis `l1_bringup`, 2 paquets en
  21,0 s ; édition de liens du binaire Unitree réussie avec PCL 1.12.
- Résultat final après ajout du moniteur : code 0, 3 paquets en 2,84 s.
- Preuves : `logs/builds/20260715-initial-colcon-build.log` et
  `logs/builds/20260715-final-colcon-build.log`.
- Intégrité : aucun patch dans `unilidar_sdk`, commit fournisseur toujours propre.

## ERR-20260715-008 — Avertissement CMake fournisseur CMP0074

- Statut : ACCEPTÉ, NON BLOQUANT.
- Sortie : `find_package(PCL)` ignore `PCL_ROOT=/usr` car la politique CMP0074
  n'est pas fixée par le CMake fournisseur.
- Résultat : CMake trouve PCL 1.12, compile et lie le binaire ; aucune correction
  vendor n'est nécessaire. L'avertissement reste visible dans la preuve brute.

## LOG-20260715-012 — Audit ABI et liaison du binaire

- Statut : SUCCÈS.
- Commandes principales : `readelf`, `strings`, `nm`, `ldd`, `sha256sum` dans
  l'image Humble ou sur le binaire de build.
- Résultats : ELF64 PIE x86_64, 1 554 464 octets, SHA-256
  `c7ed1cf9d632bb7cf04b95018a0395819578816fc81a821ac241e3278cbb61b0`.
- `ldd` : aucune bibliothèque manquante. La bibliothèque Unitree est incorporée
  statiquement ; son symbole `createUnitreeLidarReader()` est présent.
- ABI : archive compilée avec GCC 9.4, nœud avec GCC 11.4 ; GLIBCXX requis au plus
  3.4.29 et runtime disponible jusqu'à 3.4.30.
- Archive x86_64 : SHA-256
  `295efc9d55192483c66be291fe74ba0c3795c049c5e5286f650c6e7cf2d79cdf`.

## ERR-20260715-009 — Utilitaire `file` absent dans l'image minimale

- Statut : CORRIGÉ.
- Symptôme : première commande d'identification ELF, code 127, car `file` n'est
  pas installé dans l'image minimale.
- Correction : utiliser `readelf`, déjà disponible via la chaîne de compilation.
- Décision : ne pas agrandir l'image pour un utilitaire de diagnostic remplaçable.

## LOG-20260715-013 — Audit auxiliaire de référence Foxy

- Statut : TERMINÉ ET NETTOYÉ ; résultat non utilisé comme validation matérielle.
- Démarche : clone d'audit sous `/tmp`, tentative CMake hôte (code 127, CMake
  absent), puis build éphémère Foxy dans Docker : 1 paquet réussi en ~22,8 s.
- Essai sans port : nœud vivant sous timeout 124 attendu, aucune donnée.
- Incident : deux conteneurs temporaires se sont brièvement chevauchés ; un
  `Publisher count: 2` observé alors est invalidé et ne sert à aucune conclusion.
- Nettoyage : conteneurs temporaires arrêtés/supprimés, aucun vendor du projet
  modifié. Un pull auxiliaire du tag mutable `ros:humble-ros-base-jammy` a aussi
  ajouté l'image locale `sha256:afb40d6…`; elle ne remplace pas le digest amd64
  `sha256:5c793b9…` explicitement figé dans le Dockerfile.

## LOG-20260715-014 — Contrat ROS sans capteur

- Statut : SUCCÈS POUR LE CONTRAT, PAS POUR LE MATÉRIEL.
- Méthode : lancement isolé sur domaine ROS 187 avec
  `LIDAR_PORT=/dev/unitree_absent_audit`.
- Résultat : `/unitree_lidar_ros2_node` vivant ; un publisher
  `/unilidar/cloud` de type `sensor_msgs/msg/PointCloud2` et un publisher
  `/unilidar/imu` de type `sensor_msgs/msg/Imu` ; port paramétré correctement.
- QoS observé : Reliable, Volatile, liveliness Automatic ; KeepLast(10) confirmé
  dans le source, bien que la profondeur soit affichée `UNKNOWN` par ros2cli.
- Données : `ros2 topic echo --once` expire après 3 s, code 124 et 0 octet, comme
  attendu sans L1. Les logs signalent le port inexistant puis
  `Unilidar is not initialized!`.
- Conclusion : la présence du nœud et des publishers n'est jamais un healthcheck
  matériel, car le retour de `initialize()` est ignoré par le pilote.

## ERR-20260715-010 — Harnais d'arrêt du launch

- Statut : CORRIGÉ.
- Symptôme : SIGINT adressé au processus launch en arrière-plan n'a pas été
  propagé de façon fiable ; TERM après 3 s, code launch 143.
- Correction : tester directement l'ELF avec un timeout envoyant SIGINT ; le
  gestionnaire rclcpp apparaît et le processus sort environ 1,1 s plus tard,
  avant le SIGKILL de garde.
- Interprétation : latence cohérente avec `runParse()` bloquant ; premier verdict
  d'arrêt gracieux du harnais invalidé, test direct retenu.

## LOG-20260715-015 — Paquet `l1_monitor`

- Phase : P4 — surveillance.
- Statut : SUCCÈS SANS MATÉRIEL.
- Fichiers : paquet Python `ros2_ws/src/l1_monitor`, paramètres dans
  `l1_bringup/config/unitree_l1.yaml`, démarrage par défaut dans le launch.
- Fonction : fréquence d'arrivée, âge, timestamps non croissants ou nuls, frame,
  nombre de points et champs ; deux statuts publiés sur `/diagnostics`.
- QoS : Reliable/Volatile/KeepLast(10), aligné avec le pilote.
- Seuils provisoires : rapport 2 s, timeout 3 s, âge 1 s, cloud 5 Hz, IMU 20 Hz,
  fenêtre de 100 messages. Ils seront validés sur les flux réels.

## ERR-20260715-011 — Nettoyage du premier test moniteur en arrière-plan

- Statut : CORRIGÉ ET NETTOYÉ.
- Symptôme : le processus Python en arrière-plan avait hérité d'un SIGINT ignoré ;
  le trap attendait indéfiniment.
- Correction : suppression forcée du seul conteneur éphémère
  `unitree-l1-dev-run-60b5b6c62f02` (code final 137), puis harnais borné par TERM
  et KILL de garde. Aucun processus n'est resté actif.
- Validation séparée : exécution avant-plan 4 s, timeout 124 attendu, alarmes
  `no messages received` émises toutes les 0,5 s.

## ERR-20260715-012 — Sérialisation du niveau DiagnosticStatus

- Statut : CORRIGÉ.
- Symptôme : le premier grep cherchait `level: 2`, tandis que ros2cli affiche
  l'octet ERROR sous la forme `level: "\\x02"`; la commande fonctionnelle a donc
  terminé avec code 1 après avoir reçu le bon message.
- Correction : assertion sur la représentation octet et sur les deux textes
  `no messages received`.
- Résultat : `MONITOR_NO_DATA_ALARM_PASS`, code 0.

## LOG-20260715-016 — Tests du code projet et moniteur synthétique

- Statut : SUCCÈS.
- Commande : `colcon test --packages-select l1_monitor l1_bringup
  unitree_lidar_ros2`, puis `colcon test-result --all --verbose`.
- Résultat final : 3 tests statistiques, 1 test du launch et 4 tests de lint
  intégrés, soit 8/8, 0 erreur, 0 échec, 0 ignoré. Le paquet fournisseur ne
  fournit aucun CTest.
- Preuves : `logs/tests/20260715-final-colcon-test.log` et
  `logs/tests/20260715-final-colcon-test-result.log`.
- Test DDS synthétique : PointCloud2 à ~10 Hz, Imu à ~30 Hz, frames attendues,
  quatre points et champs x/y/z ; deux diagnostics `stream healthy`, code 0,
  `MONITOR_SYNTHETIC_HEALTH_PASS`.

## LOG-20260715-017 — X11, DRI et RViz2

- Statut : SUCCÈS.
- Commandes : `./scripts/gui-smoke-test.sh`, puis démarrage de RViz2 sous timeout
  SIGINT de 8 s avec le profil projet.
- Résultat : `xdpyinfo` réussi, rendu direct accéléré Intel HD Graphics 5500,
  Mesa 23.2.1, OpenGL 4.6 ; RViz reste actif 8 s puis s'arrête au signal.
- Code RViz : 124 attendu du timeout, harnais global code 0.
- Profil : `/unilidar/cloud`, Fixed Frame et Target Frame `unilidar_lidar`.

## ERR-20260715-013 — RViz sans accès DRM initial

- Statut : CORRIGÉ.
- Symptôme initial : RViz fonctionnait 8 s et annonçait OpenGL 4.5, mais Mesa ne
  pouvait pas ouvrir `/dev/dri/card1` et utilisait un repli graphique.
- Correction : déplacer X11/DRI dans `compose.gui.yaml`, ajouter seulement
  `/dev/dri` et les GID video/render, garder `compose.yaml` headless.
- Résultat : rendu direct Intel/OpenGL 4.6, plus d'erreur DRI au test final.
- Avertissement restant : `Stereo is NOT SUPPORTED`, informatif et sans impact.

## LOG-20260715-018 — Scripts matériels et runbook

- Statut : PRÊTS, NON EXÉCUTÉS SUR MATÉRIEL.
- Fichiers : `check-lidar.sh`, `lidar-launch.sh`, `lidar-validate.sh`,
  `record-bag.sh`, `bag-info.sh`, `replay-bag.sh` et
  `docs/hardware-runbook.md`.
- Sécurité : vrai tty résolu avec `readlink -e`, GID lu avec `stat -L`, refus des
  ports inattendus/occupés, un seul device Compose, pas de privileged/chmod 777,
  pas d'arrêt automatique de ModemManager.
- Contrôle sans L1 : 0 candidat détecté ; `lidar-launch.sh` refuse avant Docker,
  code 2 attendu et `LIDAR_ABSENT_REFUSAL_PASS`.
- État hôte observé : ModemManager 1.23.4 actif/activé ; `brltty` installé mais
  inactif/désactivé. Aucune configuration de ces services n'a été changée.

## LOG-20260715-019 — Conservation du dossier d'entrée et des preuves

- Statut : SUCCÈS.
- PDF copié sans conversion dans
  `docs/references/dossier_configuration_unitree_l1_ros2.pdf`.
- Métadonnées : titre « Projet Unitree 4D LiDAR L1 sous ROS 2 Humble », Pascual,
  11 pages A4, 108 212 octets, création PDF 15 juillet 2026 15:11:24 WEST.
- SHA-256 :
  `848185726cf4899efac63df62cfdef21985ec3b042eec9e52ae26113b5b84661`.
- Hashes des logs bruts :
  - build initial : `6f54f2197b21c352d535eefd9bd1954b5d79f75afb014049c0dc56b9c0eab2b6` ;
  - build final : `127859e73be1e24af7886efaccfac6a274000f7d0877bc3c1dc7c6c176d8b014` ;
  - tests : `30355dad29b2912bfedb59f7a3e330dede7ad19002f9edc847332316e218172c` ;
  - résultat tests : `66d6208d839956313fd9decb8031f46f18e2f6671f3ff9ecdd743a3ffa6f566a`.

## LOG-20260715-020 — Limites connues avant branchement

- Le pilote ignore le code de retour de `initialize()` et peut rester vivant sans
  données ; le moniteur, pas le graphe seul, doit constater les flux.
- Le destructeur fournisseur est vide, `runParse()` est bloquant et aucun TF n'est
  publié.
- Le pilote ROS 2 n'appelle explicitement ni le mode `NORMAL` au démarrage ni
  `STANDBY` à l'arrêt. Ce point sera qualifié sans patch au premier essai.
- Les frames, champs, timestamps, fréquences, unités, IMU, permissions réelles,
  rosbag2, extrinsèques, Point-LIO et carte restent `BLOCKED_HW`.
- Décision : ne pas sélectionner/adapter Point-LIO avant d'avoir un bag court
  contenant les messages réels du L1.

## LOG-20260715-021 — Archivage du manuel Unitree officiel

- Statut : SUCCÈS.
- Commande : téléchargement HTTPS depuis le CDN officiel, copie locale inchangée,
  contrôle par `pdfinfo`, `pdftotext` et `sha256sum`.
- Fichier : `docs/references/unitree_l1_user_manual.pdf`, 18 pages A4,
  1 163 168 octets, SHA-256
  `4d816cdf6197a51c5e87e6e7876da822b2d0e52e0bf63df306b40ac32fb13a74`.
- Vérifications documentaires : p. 3 (11 Hz azimutal, IMU reportée à 250 Hz),
  p. 7 (12 V et RX/TX 3,3 V), p. 11 (adaptateur, alimentation et câble fournis),
  p. 15 (12 V/1 A), p. 16 (TTL UART, 2 000 000 bit/s).

## LOG-20260715-022 — Linters ROS 2 du code projet

- Statut : SUCCÈS.
- Commandes : `ament_flake8 src/l1_monitor src/l1_bringup` et
  `ament_pep257 src/l1_monitor src/l1_bringup` dans l'image Humble.
- Résultat : 13 fichiers Python contrôlés, aucun problème de style ou docstring,
  code 0 pour les deux outils.
- Avertissement de test : l'outillage ament/Humble utilise encore l'ancienne
  interface `SelectableGroups` de `importlib_metadata` ; quatre warnings au total,
  sans erreur de lint ni effet sur le code projet.

## LOG-20260715-023 — Jalon Git avant matériel

- Statut : SUCCÈS.
- Configuration : identité Git définie uniquement dans ce dépôt comme
  `Codex <codex@localhost>` ; aucune configuration globale changée.
- Commandes : `git add --all`, contrôle de la liste indexée, puis
  `git commit -m 'Prepare and validate Unitree L1 Humble environment'`.
- Résultat : commit racine local
  `a844ba737bc8775bff97ea2263adfc2a26ee3c71`, 66 fichiers et 4 453 lignes
  ajoutées. Aucune publication distante.
- Portée : ce commit est la référence logicielle validée avant connexion du L1 ;
  le présent ajout documentaire sera son commit fils.

## ERR-20260715-014 — Chaîne PDF disponible sur l'hôte

- Statut : CORRIGÉ SANS INSTALLATION.
- Inventaire : Pandoc, LibreOffice, WeasyPrint, ReportLab et le device PDF direct
  de groff sont absents ; `groff -Tpdf` échoue faute de fichier `DESC`, et les
  macros `-ms` ne sont pas installées.
- Correction : source roff autonome, sortie PostScript par `groff -Kutf8 -Tps`,
  puis conversion A4 par Ghostscript `ps2pdf`.
- Justification : aucune installation hôte, accents français conservés et chaîne
  de génération versionnée dans le projet.

## ERR-20260715-015 — Premier rendu de la synthèse

- Statut : CORRIGÉ.
- Problème 1 : le suffixe roff `m` signifie « em » et non millimètre ; une largeur
  de ligne excessive plaçait le titre et une partie du texte hors page.
- Problème 2 : les tableaux `tbl` avec bordure produisaient un fond noir persistant
  dans le rendu Ghostscript.
- Problème 3 : les commandes commençant par `./` étaient interprétées comme des
  requêtes roff, et disparaissaient du PDF.
- Problème 4 : `pdftotext | grep -q` sous `pipefail` pouvait terminer la validation
  sur SIGPIPE après une correspondance pourtant correcte.
- Corrections : dimensions en centimètres, tableaux texte sans bordure, préfixe
  shell `$` devant les commandes et validation via un fichier texte temporaire.

## LOG-20260715-024 — PDF de synthèse avant matériel

- Statut : SUCCÈS.
- Commande : `./scripts/build-synthesis-pdf.sh`.
- Fichiers : source lisible Markdown, source de mise en page roff et PDF sous
  `docs/report/`.
- Résultat : 3 pages A4, PDF 1.4, texte français extractible, commandes matérielles
  présentes, pagination correcte ; les trois pages ont été rendues en PNG et
  inspectées visuellement.
- SHA-256 :
  `6ae9f7bb0ce5fa17f6e98c26f09e8f5b151a0241277337b9477f8ebcd2f6db8f`.
- Portée : résumé rapide du jalon logiciel, pas le rapport final après cartographie.

## LOG-20260715-025 — Archive ZIP de traçabilité

- Statut : SUCCÈS.
- Commande : `./scripts/build-trace-archive.sh HEAD`.
- Commit archivé : `3a73506f85da3cf74c43392f7235b1eb7fb03b78`.
- Fichier : `exports/unitree_l1_traces_pre_materiel_20260715.zip`.
- Résultat : 2 592 472 octets, 78 fichiers, SHA-256
  `7a317fa5add7d189bd2d210345631048a1da32ad8d309e5ab1115145dda8d682`.
- Contenu : PDF de synthèse à la racine, snapshot Git du projet, documents et PDF
  de référence, sources projet, scripts, configurations, logs bruts, index,
  manifeste SHA-256 et bundle Git complet restaurable.
- Exclusions : image Docker, build/install/log générés par colcon, SDK fournisseur
  recréable au commit figé, bags et cartes encore absents, secrets/cookie X11.
- Sidecar : le fichier `.zip.sha256` permet de vérifier le téléchargement.

## ERR-20260715-016 — Harnais de vérification approfondie du ZIP

- Statut : CORRIGÉ ; aucune corruption de l'archive.
- Essai 1 : `sha256sum -c` lancé depuis le dossier projet ne trouvait pas le nom
  relatif du ZIP contenu dans le sidecar. Correction : contrôler depuis `exports/`.
- Essai 2 : répétition du piège `pdftotext | grep -q` sous `pipefail`, code 141.
  Correction : extraire le texte dans un fichier temporaire avant `grep`.
- Essai 3 : `git bundle verify` lancé hors d'un dépôt renvoie
  `need a repository to verify a bundle`. Correction : `git -C <projet> bundle
  verify <bundle>`.
- Validation finale : SHA externe OK, `unzip -t` OK, tous les SHA internes OK,
  PDF 3 pages et copie identique, bundle valide, clone restauré exactement au
  commit archivé ; `ARCHIVE_DEEP_VALIDATION_PASS`.

## LOG-20260716-026 — Mise à disposition locale sous `docs/report`

- Statut : SUCCÈS.
- Demande : rendre les dossiers et PDF directement consultables sur l'ordinateur,
  sans dépendre des liens de téléchargement de l'interface.
- Dossier créé : `docs/report/traces_pre_materiel_20260715/`.
- Commande principale : `unzip -oq
  docs/report/archives/unitree_l1_traces_pre_materiel_20260715.zip -d
  docs/report/traces_pre_materiel_20260715`.
- PDF d'accès rapide :
  `docs/report/pdf/SYNTHESE_UNITREE_L1_PRE_MATERIEL.pdf`.
- Archive locale :
  `docs/report/archives/unitree_l1_traces_pre_materiel_20260715.zip` avec son
  fichier `.sha256`.
- Contrôles : somme SHA-256 externe correcte et `unzip -tq` sans erreur.
- Organisation documentée dans `docs/report/README.md`.
- Raisonnement : les copies locales sont des dérivés reproductibles ; elles sont
  ignorées par Git afin de ne pas dupliquer le ZIP, son snapshot et son bundle
  dans l'historique principal.

## LOG-20260716-027 — Détection et première validation matérielle

- Statut : SUCCÈS.
- Détection : Silicon Labs CP2104 `10c4:ea60`, série `02C90122`, lien stable sous
  `/dev/serial/by-id`, résolu vers `/dev/ttyUSB0`, groupe 20, aucun processus
  concurrent.
- Lancement : `START_RVIZ=false ./scripts/lidar-launch.sh` ; accès ciblé au tty
  dans un conteneur non privilégié, `LIDAR_CONTAINER_ACCESS_PASS`.
- Validation : `./scripts/lidar-validate.sh`, puis une seconde fois avec RViz.
- Résultat : deux `LIDAR_DATA_VALIDATION_PASS`; cloud PointCloud2 ~8 Hz, IMU
  ~210 Hz, environ 2 140 points, champs `x,y,z,intensity,ring,time`, timestamps
  non nuls et monotones, diagnostics sains.
- Preuves : `logs/tests/lidar-validation-20260716_140938.log` et
  `logs/tests/lidar-validation-20260716_141319.log`.

## LOG-20260716-028 — Bag réel et visualisation

- Statut : SUCCÈS.
- Enregistrement : `BAG_LABEL=validation BAG_DURATION_SEC=30
  ./scripts/record-bag.sh`.
- Bag : `bags/l1_validation_20260716_141042`, 29,339711292 s, 18,0 Mio,
  6 400 messages : 233 cloud, 6 152 IMU et 15 diagnostics.
- RViz : démarrage réel avec OpenGL 4.6 ; deuxième validation complète pendant
  que RViz était abonné au cloud.
- SHA-256 base DB3 :
  `9c87d26fc2014346d38f6a7d40a5859d5a6127ca2215f288f3af222114c34074`.
- SHA-256 métadonnées :
  `a97e32b37775ab1a4e07435699e6cd307f6357da6f5f3753be21a37fcd4221dd`.

## ERR-20260716-017 — Double arrêt ROS 2 de `l1_monitor`

- Statut : CORRIGÉ ET VALIDÉ SUR MATÉRIEL.
- Symptôme : au premier Ctrl-C, le pilote terminait proprement mais le moniteur
  levait `rcl_shutdown already called on the given context`.
- Cause : le gestionnaire SIGINT de ROS 2 avait déjà fermé le contexte avant
  l'appel inconditionnel à `rclpy.shutdown()` dans le bloc `finally`.
- Correction projet : n'appeler `rclpy.shutdown()` que si `rclpy.ok()` est vrai.
- Validation : reconstruction réussie, 8/8 tests, puis nouveau lancement avec
  L1 et RViz ; pilote, moniteur et RViz ont tous terminé proprement au Ctrl-C.
- Le code fournisseur Unitree n'a pas été modifié.

## ERR-20260716-018 — Horloge murale lors du premier rejeu

- Statut : CORRIGÉ.
- Symptôme : le bag se relisait entièrement avec code 0 et les bonnes fréquences,
  mais le moniteur signalait un âge de header d'environ 215 s.
- Cause : comparaison des timestamps enregistrés à l'heure murale de la relecture.
- Correction : `ros2 bag play --clock` et paramètre `use_sim_time:=true` pour
  `l1_monitor` et RViz dans `scripts/replay-bag.sh`.
- Validation : second rejeu code 0, diagnostics `stream healthy`, fréquences
  cloud ~8 Hz et IMU ~210 Hz ; disparition de la fausse alerte d'âge.

## LOG-20260716-029 — Registre matériel exhaustif

- Source : `docs/report/journal_materiel_commandes_20260716.md`.
- Sortie :
  `docs/report/pdf/JOURNAL_MATERIEL_COMMANDES_UNITREE_L1_20260716.pdf`.
- Contenu : commandes exactes, résultats utiles, preuves, incidents, correctifs,
  empreintes et raisonnement de la session matérielle du 16 juillet 2026.
- Générateur : `scripts/build-hardware-journal-pdf.sh`.
- Résultat final : 10 pages A4, PDF 1.4, texte extractible et marqueurs des
  commandes CMD-032 à CMD-051 vérifiés. Les sept pages initiales puis les trois
  nouvelles pages ont été rendues et inspectées, sans texte coupé.
- SHA-256 final :
  `9f797ca0717dc6d21ef12ba8629fe44ffd3d3535467a5301e9b34f0ef75157f7`.

## LOG-20260716-030 — Rapport pédagogique sur la lecture des données

- Statut : SUCCÈS.
- Fichier :
  `docs/report/pdf/RAPPORT_LISIBLE_LECTURE_DONNEES_UNITREE_L1.pdf`.
- Organisation : partie 1 en langage simple (chemin des données, dix étapes,
  résultats et limites), puis partie 2 technique (architecture, topics, QoS,
  commandes, critères, mesures, bag, incidents et preuves).
- Résultat : 10 pages A4, texte extractible, mise en page Helvetica avec
  commandes monospace ; toutes les pages ont été rendues et inspectées.
- SHA-256 :
  `39970c3e1d040523ba2e972287b7c498c03f50b41bf29bd21c1123cd843b2f2c`.
- Sources : `docs/report/rapport_lisible_donnees_unitree_l1.md` et `.roff`.

## LOG-20260716-031 — Tutoriel débutant RViz

- Statut : SUCCÈS.
- Fichier : `docs/report/pdf/TUTORIEL_RVIZ_UNITREE_L1.pdf`.
- Contenu : sécurité, détection, lancement, contenu attendu de RViz, navigation,
  validation dans un second terminal, arrêt propre, rejeu du bag et dépannage.
- Résultat : 6 pages A4, commandes directement copiables, marqueurs textuels
  contrôlés et toutes les pages inspectées visuellement.
- Contrôle fonctionnel : cinq scripts cités présents, exécutables et valides avec
  `bash -n`; bag de rejeu présent ; aucun `unitree_l1_runtime` actif.
- SHA-256 :
  `df728f269726e9116c051139532623391f7c32582e5b7098539a4dbb9833aced`.
- Sources : `docs/report/tutoriel_rviz_unitree_l1.md` et `.roff`.

## ERR-20260716-019 — Finition des deux PDF lisibles

- Statut : CORRIGÉ.
- Premier rendu : titres de couverture trop serrés, un grand titre héritait
  d'une indentation et les libellés de pied de page étaient parfois tronqués.
- Corrections : interlignes dédiés aux couvertures, remise à zéro de l'indentation
  dans les macros de titres, alignement du corps à gauche et numéro de page
  centré sans libellé variable.
- Validation : nouvelle génération, extraction des marqueurs, contrôle A4, puis
  inspection des couvertures, pages intermédiaires et dernières pages.
- Générateur commun : `scripts/build-readable-guides-pdf.sh`.

## ERR-20260716-020 — `colcon build` découvrait le paquet ROS 1 Unitree

- Statut : CORRIGÉ ET VALIDÉ.
- Symptôme photographié : `find_package(catkin)` ne trouvait ni
  `catkinConfig.cmake` ni `catkin-config.cmake`.
- Cause : la commande lancée à la racine explorait aussi
  `unilidar_sdk/unitree_lidar_ros`, qui est le pilote ROS 1, ainsi que le SDK
  CMake brut sans cible d'installation.
- Correction : `ros2_ws/colcon_defaults.yaml` fixe cinq racines de sources
  contenant six paquets ROS 2. Le fournisseur n'a pas été modifié et catkin
  n'a pas été installé.
- Validation : la commande exacte `colcon build` a terminé six paquets avec
  code 0 ; preuve `logs/builds/20260716-plain-colcon-build.log`.

## ERR-20260716-021 — Bibliothèques OctoMap absentes de l'ancienne image

- Statut : CORRIGÉ ET VALIDÉ.
- Symptôme distinct dans le journal CMake : `OCTOMAPConfig.cmake` absent.
- Diagnostic `rosdep` : `liboctomap-dev`, `ros-humble-octomap-msgs` et
  `ros-humble-octomap-ros` manquaient.
- Correction : ajout explicite au Dockerfile puis reconstruction complète de
  l'image. Nouvelle image :
  `sha256:2e9707a45f0ef0dfa3a8e37ecd28cd89c873493aacde3494fda2cc33115a8978`.
- Preuve brute : `logs/builds/20260716-octomap-image-build.log`.

## LOG-20260716-032 — Dépendance OctoMap reproductible

- Dépôt externe : `OctoMap/octomap_mapping`, tag 2.3.1, commit
  `f79da9a9a1fcdf82e72dab4df288d6cc27c6e163`.
- `config/dependencies.repos`, `fetch-dependencies.sh`, `.gitignore` et
  `workspace-build.sh` gèrent maintenant Unitree et OctoMap sans versionner
  leurs checkouts imbriqués.
- Les deux dépôts fournisseurs sont restés propres.

## LOG-20260716-033 — Shell Docker avec écran, GPU et LiDAR

- `docker-shell.sh` charge par défaut les profils GUI et LiDAR lorsque le port
  stable unique est présent ; `--no-gui` et `--no-lidar` restent disponibles.
- Sécurité conservée : cookie X11 en lecture seule, groupes vidéo/rendu/tty
  ciblés, aucun `privileged`, aucun `xhost +`, aucun `chmod 777`.
- Validation : rendu direct Intel, OpenGL 4.6, affichage `:1` et
  `/dev/unitree_lidar` lisible/écrivable.
- Preuve : `logs/tests/20260716-combined-gui-lidar-access.log`.

## LOG-20260716-034 — Paquet projet `l1_octomap_bringup`

- Contenu : launch OctoMap seul, launch complet pilote + moniteur + OctoMap +
  RViz, paramètres YAML, profil RViz et six tests.
- Entrée : remappage `cloud_in -> /unilidar/cloud`.
- Sorties RViz : `/occupied_cells_vis_array` et nuage brut dans le repère `map`.
- Mode banc : TF identité explicite et avertissement si le capteur bouge.
- Mode mobile : aucune fausse TF statique ; une pose externe horodatée est
  obligatoire.

## LOG-20260716-035 — Tests du code projet après OctoMap

- Commande : `colcon test --packages-select l1_monitor l1_bringup
  l1_octomap_bringup`, puis `colcon test-result --all --verbose`.
- Résultat : 14 tests, 0 erreur, 0 échec, 0 ignoré.
- Preuve : `logs/tests/20260716-octomap-project-tests.log`.

## LOG-20260716-036 — Chaîne réelle L1 vers OctoMap

- Launch : `unitree_l1_octomap.launch.py rviz:=false`, capteur immobile.
- Nœuds observés : pilote Unitree, moniteur, TF statique et OctoMap server.
- Mesures : cloud 9,57–9,84 Hz, IMU environ 235–260 Hz, marqueurs OctoMap
  environ 7 Hz.
- Sonde QoS fiable/transient-local : 17 marqueurs, 2 marqueurs occupés et
  13 247 points ; `OCTOMAP_MARKER_PROBE_PASS`.
- Arrêt : SIGINT propre, conteneur supprimé et port série libéré.
- Preuves : `logs/tests/20260716-real-lidar-octomap-launch.log` et
  `logs/tests/20260716-real-lidar-octomap-observation.log`.

## ERR-20260716-022 — Ordre du mode Bash strict dans la sonde ROS

- Statut : CORRIGÉ immédiatement ; aucune incidence sur le graphe actif.
- Premier essai : `set -u` précédait `source /opt/ros/humble/setup.bash` et
  provoquait `AMENT_TRACE_SETUP_FILES: unbound variable`.
- Correction : sourcer ROS et l'overlay avant d'activer `set -u`.
- Résultat corrigé : liste des cinq nœuds et fréquences cloud/OctoMap
  obtenues normalement.

## LOG-20260716-037 — Dossier PDF unique et guide de structure

- Tous les PDF canoniques ont été regroupés dans `docs/report/pdf/` ; les
  scripts de génération et l'archive de trace utilisent ce nouvel emplacement.
- Nouveau guide : `GUIDE_STRUCTURE_PROJET_UNITREE_L1.pdf`, 13 pages A4,
  SHA-256
  `8614f97d82154d155758ba3ca4b6c1b387f59c30106baeafc0476b9a5bd9a46b`.
- Contrôles : bornes peintes par page, marqueurs textuels, extraction, format A4
  et inspection visuelle de pages représentatives.

## LOG-20260716-038 — Dépôt Git local et publication future

- Le projet était déjà initialisé sur la branche `main`, sans remote.
- Le guide de structure et le README expliquent `git remote add origin`,
  `git remote set-url` et `git push -u origin main`.
- Aucun remote n'a été ajouté et aucun envoi réseau n'a été effectué :
  l'URL et l'autorisation de l'utilisateur restent nécessaires.

## LOG-20260716-039 — Reconstruction des PDF dans le dossier canonique

- `SYNTHESE_UNITREE_L1_PRE_MATERIEL.pdf` : 3 pages,
  SHA-256 `13bdf314d64bcebb9c2098fac8e81d852e576cbce5a63757819a259c277aa2d7`.
- `RAPPORT_LISIBLE_LECTURE_DONNEES_UNITREE_L1.pdf` : 10 pages,
  SHA-256 `64741a7e082046fae3a3184de0952eacc28ca5a4ff3b1a8febbaab2306401134`.
- `TUTORIEL_RVIZ_UNITREE_L1.pdf` : 6 pages,
  SHA-256 `f3b61762e2774e168f177dd66f4b6ba707adb01e57e96ba5d2c4e80503128316`.
- `GUIDE_STRUCTURE_PROJET_UNITREE_L1.pdf` : 13 pages,
  SHA-256 `8614f97d82154d155758ba3ca4b6c1b387f59c30106baeafc0476b9a5bd9a46b`.
- Tous sont A4, texte extractible et produits par les scripts versionnés.

## ERR-20260716-023 — Titre de commande séparé de son bloc dans le journal PDF

- Statut : CORRIGÉ ET VALIDÉ.
- Symptôme : lors de la relecture des pages 11 à 15, le titre `CMD-066` pouvait
  rester en bas d'une page et son bloc de commande commencer sur la suivante.
- Cause : le générateur roff ne réservait pas d'espace avant les titres Markdown.
- Correction : `scripts/build-hardware-journal-pdf.sh` ajoute `.ne` avant les
  titres de niveau 2 et 3 et vérifie maintenant aussi les marqueurs `CMD-066`,
  `CMD-079` et `OCTOMAP_MARKER_PROBE_PASS`.
- Validation : génération réussie, extraction `pdftotext`, contrôle A4 et
  inspection visuelle des pages 12 à 14 ; le titre et le code `CMD-066` sont
  réunis.
- Preuve : `logs/tests/20260716-journal-pagination-fix.log`.

## LOG-20260716-040 — Journal matériel final après correction de pagination

- Fichier : `docs/report/pdf/03_octomap_mapping/JOURNAL_MATERIEL_COMMANDES_UNITREE_L1_20260716.pdf`.
- Résultat : 17 pages A4, texte extractible et marqueurs historiques, LiDAR et
  OctoMap contrôlés automatiquement.
- SHA-256 :
  `d4fcd4c132b7e714fa8982344e44d23a95b04ac1be2bf84d5fe759eee7c6c880`.

## LOG-20260716-041 — Vérification finale des dépendances et du workspace

- `scripts/fetch-dependencies.sh` a confirmé les commits Unitree et OctoMap
  épinglés.
- `scripts/workspace-build.sh` a réinstallé les rosdeps déjà présentes et
  reconstruit les six paquets ROS 2 avec code 0 en 4,48 s.
- Preuves : `logs/tests/20260716-dependency-pin-verification.log` et
  `logs/builds/20260716-workspace-script-build.log`.

## ERR-20260716-024 — Option `compileall` invalide dans l'audit final

- Statut : CORRIGÉ immédiatement.
- Premier essai : `python3 -m compileall -q --dir
  ros2_ws/src/l1_octomap_bringup` ; cette version de Python ne reconnaît pas
  `--dir`.
- Correction : `python3 -m compileall -q ros2_ws/src/l1_octomap_bringup`.
- Résultat : `PYTHON_SYNTAX_PASS`; le projet n'a pas été modifié par l'erreur.

## LOG-20260716-042 — Audit statique avant commit

- `bash -n` sur les scripts, parse XML du paquet projet et parse YAML des
  dépendances, des defaults colcon et de la configuration OctoMap : succès.
- Scan de sécurité : aucun `privileged: true`, `chmod 777` ou `xhost +`.
- Les checkouts Unitree et OctoMap sont propres et le ZIP préexistant conserve
  son SHA-256 `d7fa9348e9790b7c5c5b81474641c02dd66a4400890d03f5a8d1c8574570295b`.

## LOG-20260716-043 — Commit Git local créé

- Commit principal :
  `3dbe4c6b278079573d395bf437629e30c326f614` (`main`).
- Contenu : intégration OctoMap, configuration colcon, shell Docker GUI/LiDAR,
  guide de structure, PDF regroupés et preuves sélectionnées.
- Aucun remote ni push n'a été effectué. Le ZIP utilisateur et les checkouts
  externes restent hors du commit.

## LOG-20260716-044 — Version PDF du journal de configuration

- Commande : `./scripts/build-configuration-log-pdf.sh`.
- Sortie : `docs/report/pdf/01_environment/CONFIGURATION_LOG_UNITREE_L1.pdf`.
- Contrôles : texte extractible, marqueurs de validation présents et format A4.
- L'index `docs/report/pdf/README.md` et les README du projet pointent désormais
  vers cette copie PDF ; la source reste `docs/configuration-log.md`.

## LOG-20260716-045 — Tutoriel colcon, RViz2 et rosbag2

- Sources : `docs/report/tutorial_colcon_rviz2_record_unitree_l1.md` et `.roff`.
- Commande : `bash -n scripts/build-readable-guides-pdf.sh` puis
  `./scripts/build-readable-guides-pdf.sh`.
- Sortie : `docs/report/pdf/02_lidar_and_rviz/TUTORIAL_COLCON_RVIZ2_RECORD_UNITREE_L1.pdf`.
- Contenu : compilation avec `colcon build`, démarrage du pilote et de RViz2,
  validation, enregistrement borné avec `ros2 bag record` via
  `record-bag.sh`, inspection, arrêt propre, rejeu avec `ros2 bag play --clock`
  et sauvegarde d'une configuration RViz2.
- Résultat : 9 pages A4, texte extractible et inspection visuelle des pages de
  couverture, d'enregistrement et de checklist. SHA-256 :
  `606019af93230c6d3de064d955db6385a7ffc05cc9649ecfb796049efa352efb`.

## ERR-20260716-025 — Guillemet imbriqué dans une sonde shell

- Statut : CORRIGÉ immédiatement ; aucune incidence sur le runtime.
- Premier essai : une commande `docker exec ... bash -lc` entourée de guillemets
  simples contenait aussi `grep -E 'octomap|reset|clear'`. Le shell hôte a
  fermé la chaîne trop tôt et la sonde n'a pas exécuté le filtre attendu.
- Correction : utiliser des guillemets doubles dans la commande imbriquée :
  `grep -E "octomap|reset|clear"`.
- Résultat : la liste complète des topics et services OctoMap a été recueillie
  dans `logs/tests/20260716-existing-runtime-octomap-observation.log`.

## LOG-20260716-046 — Audit OctoMap sur le runtime existant

- Commande de lancement :
  `docker exec -it unitree_l1_runtime bash -lc 'source /opt/ros/humble/setup.bash && source /workspace/ros2_ws/install/setup.bash && exec ros2 launch l1_octomap_bringup l1_octomap.launch.py cloud_topic:=/unilidar/cloud world_frame:=map lidar_frame:=unilidar_lidar static_sensor:=true'`.
- Le pilote, le moniteur et RViz2 existants ont été conservés ; seul le serveur
  OctoMap et son TF de banc ont été ajoutés.
- Résultat : `/octomap_server`, `/l1_static_lidar_transform`,
  `/occupied_cells_vis_array`, `/octomap_binary`, `/octomap_full`,
  `/octomap_point_cloud_centers`, `/projected_map` et les services reset/clear
  observés. Fréquence MarkerArray : environ 8,29 Hz.
- Preuves : `logs/tests/20260716-existing-runtime-octomap-launch.log`,
  `logs/tests/20260716-existing-runtime-octomap-observation.log` et
  `logs/tests/20260716-existing-runtime-octomap-audit.log`.

## LOG-20260716-047 — Sauvegarde réelle de la carte

- Commande : `./scripts/save-octomap.sh l1_real_bench_20260716.bt`.
- Le saver a reçu 67 533 noeuds à résolution 0,10 m et a créé
  `maps/l1_real_bench_20260716.bt` de 18 902 octets.
- Verdict : `OCTOMAP_SAVE_PASS`. Le dossier `maps/` reste ignoré par Git car il
  contient des données générées.
- Preuve : `logs/tests/20260716-octomap-map-save.log`.

## LOG-20260716-048 — Arrêt ciblé de la session OctoMap

- Le processus launch OctoMap a reçu SIGINT via son PID dans
  `unitree_l1_runtime`. Le serveur et le TF statique ont disparu ; le pilote,
  le moniteur et RViz2 sont restés actifs dans le runtime déjà utilisé.
- Aucun conteneur utilisateur indépendant n'a été arrêté. Preuve :
  `logs/tests/20260716-existing-runtime-octomap-shutdown.log`.

## LOG-20260716-049 — Classement des PDF par étape et nouveaux guides

- Les dossiers `docs/report/pdf/00_preparation`, `01_environment`,
  `02_lidar_and_rviz` et `03_octomap_mapping` ont été créés.
- Les sept PDF historiques ont été déplacés par `git mv` dans le sous-dossier
  correspondant ; le ZIP utilisateur préexistant n'a pas été modifié.
- Nouvelles sources :
  `docs/report/tutorial_unitree_l1_octomap_mapping.md`/`.roff` et
  `docs/report/rapport_configuration_unitree_l1_octomap.md`/`.roff`.
- Nouveau générateur : `scripts/build-octomap-guides-pdf.sh`. Il contrôle le
  format A4, le texte extractible et les marqueurs `OCTOMAP_SAVE_PASS` et
  `OCTOMAP_MARKER_PROBE_PASS`.
- Les sorties canoniques sont les deux PDF du dossier
  `docs/report/pdf/03_octomap_mapping/`.

## LOG-20260716-050 — Rebuild et audit documentaire final

- Générateurs exécutés : `build-synthesis-pdf.sh`,
  `build-configuration-log-pdf.sh`, `build-structure-guide-pdf.sh`,
  `build-readable-guides-pdf.sh`, `build-hardware-journal-pdf.sh` et
  `build-octomap-guides-pdf.sh`.
- Les neuf PDF canoniques sont A4, texte extractible et rangés dans les quatre
  sous-dossiers. Les deux nouveaux guides font chacun 9 pages.
- SHA-256 des nouveaux guides : tutoriel
  `b3a7ce35f99d3fa4f35ed456a0adb609550b00b64fa648bc0f476a4e0f938a76` ;
  rapport `11fadff1a296729663136778a5ea0a646a4e829da898921d85bbb5a8674bc83d`.
- Contrôles complémentaires : `git diff --check`, `bash -n` des scripts et
  `python3 -m compileall -q ros2_ws/src/l1_octomap_bringup` réussis.
- Inspection visuelle : couvertures, page RViz/topics du tutoriel et pages
  validation/sauvegarde du rapport rendues en PNG et contrôlées.

## LOG-20260717-051 — Journal anglais exhaustif des commandes

- Demande : produire une édition anglaise beaucoup plus détaillée du journal
  matériel, avec toutes les commandes terminal et leur explication.
- Vérification de la source : le journal historique contient 86 entrées, 72
  blocs `bash`, 18 blocs de sortie/patch et 307 lignes de transcript exact.
- Commandes de génération :
  `python3 -m py_compile scripts/generate-english-command-journal.py`, puis
  `./scripts/build-english-command-journal-pdf.sh`.
- Sources générées :
  `docs/report/journal_materiel_commandes_20260716_en.md` et `.roff`.
- Sortie :
  `docs/report/pdf/03_octomap_mapping/JOURNAL_MATERIEL_COMMANDES_UNITREE_L1_20260716_EN.pdf`,
  23 pages A4, texte extractible, tous les identifiants `CMD-001` à `CMD-086`
  et les marqueurs `OCTOMAP_MARKER_PROBE_PASS` / `OCTOMAP_SAVE_PASS` présents.
- Les très longues lignes sont seulement enveloppées visuellement dans le PDF;
  la source Markdown conserve les commandes originales non coupées.
- Le constructeur détecte et retire la page finale vide créée par le piège de
  pied de page groff, sans supprimer une page contenant du contenu.
- Preuve de construction : la sortie du générateur contient
  `ENGLISH_COMMAND_JOURNAL_PDF_PASS`.

## LOG-20260717-052 — Copies anglaises explicites des deux documents OctoMap

- Le tutoriel et le rapport OctoMap étaient déjà rédigés en anglais ; des copies
  PDF nommées explicitement `_EN` ont été produites pour éviter toute ambiguïté.
- Commande : `./scripts/build-english-octomap-guides-pdf.sh`.
- Sorties :
  `TUTORIAL_UNITREE_L1_OCTOMAP_MAPPING_EN.pdf` et
  `RAPPORT_CONFIGURATION_UNITREE_L1_OCTOMAP_EN.pdf`, chacun 9 pages A4.
- Contrôle : texte extrait identique à la version anglaise de référence, avec
  les marqueurs `static_sensor:=true`, `static_sensor:=false`,
  `OCTOMAP_MARKER_PROBE_PASS` et `OCTOMAP_SAVE_PASS`.
- Les trois nouveaux PDF sont indexés dans `docs/report/pdf/README.md`.

## LOG-20260717-053 — Correction du contexte Docker dans l'étape 3 OctoMap

- Symptôme observé sur la photo : la commande
  `docker exec -it unitree_l1_runtime bash -lc 'source /opt/ros/humble/setup.bash'`
  se terminait immédiatement, puis
  `source /workspace/ros2_ws/install/setup.bash` était exécuté au prompt hôte
  `isr@...`. Le chemin `/workspace` n'existe que dans le conteneur.
- Les tentatives d'exécuter `setup.bash` directement produisaient
  `Permission denied`; ce fichier doit être chargé avec `source` et ne demande
  jamais `sudo`.
- Contrôle non destructif du runtime : `unitree_l1_runtime` était actif, les
  deux fichiers `/opt/ros/humble/setup.bash` et
  `/workspace/ros2_ws/install/setup.bash` étaient lisibles, et
  `ros2 pkg prefix l1_octomap_bringup` retournait
  `/workspace/ros2_ws/install/l1_octomap_bringup`.
- Validation de la commande corrigée avec
  `ros2 launch l1_octomap_bringup l1_octomap.launch.py --show-args` : les
  arguments `cloud_topic`, `world_frame`, `lidar_frame`, `resolution`,
  `max_range` et `static_sensor` sont résolus. Aucun nouveau graphe n'a été
  laissé actif pendant ce contrôle.
- Le tutoriel Markdown et sa source roff montrent désormais une commande hôte
  unique, puis une alternative interactive où le prompt doit passer de
  `isr@...` à `ros@...` avant les commandes `source`.
- Les PDF canonique et `_EN` ont été reconstruits : 9 pages A4, texte
  extractible, avertissements hôte/Docker présents et pages 4/9 contrôlées
  visuellement.

## LOG-20260717-054 — Commande OctoMap sans guillemets à recopier

- Une seconde photo a montré deux corruptions de collage indépendantes :
  `^[[200~docker` (séquence de collage bracketed-paste devenue visible) et
  `’source` (guillemet typographique provenant du PDF). Bash interprétait alors
  `’source` comme un nom de commande et retournait `command not found`.
- Nouveau wrapper hôte : `scripts/octomap-launch.sh`. La commande utilisateur
  est maintenant simplement `./scripts/octomap-launch.sh`, sans guillemet ni
  commande `source` à recopier.
- Le wrapper vérifie le nom et l'état de `unitree_l1_runtime`, valide
  `STATIC_SENSOR`, source ROS 2 et l'overlay uniquement dans Docker, confirme le
  préfixe de `l1_octomap_bringup`, refuse un second `/octomap_server`, puis
  lance OctoMap avec propagation de Ctrl-C.
- Commandes de contrôle : `bash -n scripts/octomap-launch.sh` et
  `./scripts/octomap-launch.sh --check`. Résultat :
  `OCTOMAP_LAUNCH_CHECK_PASS` sur le runtime réel actif, sans démarrer de noeud
  OctoMap pendant le test.
- Tests négatifs réussis : `STATIC_SENSOR=maybe` retourne 2, un runtime absent
  retourne 3, et un argument inconnu retourne 2 avec le message d'usage.
- Le tutoriel Markdown, sa source roff, le README et les deux PDF ont été mis à
  jour. Les autres commandes `bash -lc` à recopier dans les étapes 4, 6 et 7
  ont aussi été remplacées par le wrapper ou une entrée interactive dans le
  conteneur. Les PDF restent A4 sur 9 pages; les pages 4, 5, 7, 8 et 9 ont été
  rendues et inspectées visuellement.

## LOG-20260717-055 — Audit avant visualisation et évaluation des cartes

- Commandes de lecture seules : `docker ps -a`, `ros2 node list` et
  `ros2 topic list` dans le conteneur de développement actif, inventaire de
  `maps/`, lecture des sept lignes d'en-tête des fichiers `.bt`, `stat` et
  `sha256sum`.
- Le runtime nommé `unitree_l1_runtime` était arrêté au moment de l'audit. Le
  conteneur de développement encore actif n'avait aucun noeud ni topic LiDAR;
  aucun graphe utilisateur n'a donc été interrompu.
- Une sauvegarde plus récente créée par l'utilisateur a été trouvée :
  `maps/l1_bench_map_20260716.bt`, 23 276 octets, 58 202 noeuds stockés,
  résolution 0,10 m, SHA-256
  `5a205ca4746e497c40f7681dfb38ffa08a92f7b2aa4bf4e28f67e69e99965cd9`.
- La carte précédente `l1_real_bench_20260716.bt` reste valide : 18 902 octets,
  45 149 noeuds stockés dans l'en-tête et résolution 0,10 m.

## LOG-20260717-056 — Outils de visualisation et d'évaluation ajoutés

- `view_saved_octomap.launch.py` recharge un fichier `.bt` ou `.ot` dans
  `octomap_server_node`; `saved_octomap.rviz` affiche la MarkerArray avec
  Fixed Frame `map` et QoS Reliable + Transient Local.
- `scripts/inspect-octomap.sh` lit l'en-tête, la taille, la date et le SHA-256
  sans modifier la carte.
- `scripts/view-octomap.sh MAP.bt` ouvre un conteneur isolé nommé
  `unitree_l1_map_viewer` sur `ROS_DOMAIN_ID=43`, charge la carte et lance le
  profil RViz dédié. L'option `--check` valide le fichier sans créer de
  conteneur; `MAP_VIEWER_RVIZ=false` permet un rejeu sans GUI.
- `scripts/evaluate-octomap.sh` vérifie le serveur, reçoit
  `/occupied_cells_vis_array` et `/octomap_binary` avec le QoS approprié, puis
  affiche `OCTOMAP_MAPPING_HEALTH_PASS`. Il classe explicitement le test comme
  cartographie de banc, carte sauvegardée ou cartographie mobile dépendante
  d'une pose externe; il ne présente jamais ce contrôle comme une mesure de
  précision de trajectoire.
- `scripts/octomap-launch.sh` accepte désormais `OCTOMAP_RVIZ=true` et vérifie
  l'accès X11/DRI avant de demander `rviz:=true` au launch live.

## ERR-20260717-026 — Jointure Python mal protégée dans la sonde

- Statut : CORRIGÉ immédiatement.
- Premier lancement de `evaluate-octomap.sh` : l'expression Python embarquée
  `','.join(frames)` se trouvait dans une commande shell déjà délimitée par des
  apostrophes. Bash a retiré ces apostrophes et Python a signalé une erreur de
  syntaxe; aucun noeud ni fichier n'a été modifié.
- Correction : calculer d'abord `frame_text = ",".join(frames)`, puis utiliser
  `frame_text` dans la chaîne de résultat.
- Le second lancement a produit le verdict PASS décrit ci-dessous.

## LOG-20260717-057 — Build et tests du paquet mis à jour

- Commande workspace : `./scripts/workspace-build.sh`.
- Résultat : les six paquets ROS 2 ont terminé sans erreur en 4,45 s; le nouveau
  launch et le nouveau profil RViz sont installés dans l'overlay.
- Commande ciblée dans Docker :
  `colcon test --packages-select l1_octomap_bringup --event-handlers console_direct+`,
  suivie de
  `colcon test-result --test-result-base build/l1_octomap_bringup --verbose`.
- Résultat : 7 tests, 0 erreur, 0 échec, 0 test ignoré. Les deux avertissements
  `SelectableGroups` sont des dépréciations Python sans incidence.
- Contrôles statiques : `bash -n` sur les quatre wrappers concernés,
  `python3 -m compileall -q ros2_ws/src/l1_octomap_bringup`, puis validation
  `--check` des variantes live et saved-map; tous ont réussi.

## LOG-20260717-058 — Rejeu réel d'une carte et RViz2 validés

- Rejeu sans GUI :
  `MAP_VIEWER_RVIZ=false ./scripts/view-octomap.sh l1_bench_map_20260716.bt`.
  `octomap_server_node` a chargé 58 202 noeuds à 0,10 m.
- Sonde exécutée pendant ce rejeu :
  `RUNTIME_CONTAINER=unitree_l1_map_viewer ./scripts/evaluate-octomap.sh`.
- Verdict : `mapping_mode=saved_map_replay` puis
  `OCTOMAP_MAPPING_HEALTH_PASS markers=17 occupied_markers=2
  occupied_points=13672 resolution_m=0.1 binary_payload_bytes=23136
  map_id=OcTree frames=map`.
- Le même viewer a ensuite été lancé avec GUI. RViz2 a démarré avec OpenGL 4.6,
  Fixed Frame `map`, et la même carte non vide. Ctrl-C a arrêté proprement
  RViz2, le serveur et supprimé le conteneur temporaire.

## LOG-20260717-059 — Commande exacte du README OctoMap vérifiée

- Source vérifiée : README officiel de la branche ROS 2 de
  `OctoMap/octomap_mapping`. Il demande
  `ros2 run octomap_server octomap_saver_node --ros-args -p
  octomap_path:=(path for saving octomap)` et impose une extension `.bt` ou
  `.ot`; le texte entre parenthèses est un emplacement à remplacer.
- Essai exact sur le serveur de carte isolé :
  `ros2 run octomap_server octomap_saver_node --ros-args -p
  octomap_path:=/tmp/github_readme_validation.bt`.
- Résultat : `Map received (58202 nodes, 0.100000 m res)` et
  `OFFICIAL_SAVER_COMMAND_PASS bytes=23276`. L'en-tête `.bt` était valide;
  le fichier temporaire a disparu avec le conteneur d'essai.
- Pour un usage réel persistant, le tutoriel remplace le chemin par
  `/workspace/maps/github_readme_map.bt`, qui correspond sur l'hôte à
  `/home/isr/unitree_l1_project/maps/github_readme_map.bt`. Le wrapper
  `save-octomap.sh` reste recommandé car il ajoute le refus d'écrasement et le
  contrôle d'un fichier non vide.

## LOG-20260717-060 — Limite de l'évaluation SLAM explicitée

- OctoMap fusionne les nuages dans une grille d'occupation 3D mais n'est pas un
  estimateur de pose. Le mode `static_sensor=true` valide donc la chaîne LiDAR
  vers carte sur banc; il ne permet pas de mesurer une trajectoire.
- Une évaluation mobile nécessite un estimateur externe fournissant une TF
  dynamique et une pose/odométrie horodatée. Les mesures proposées sont ATE,
  RPE, dérive par distance, erreur de fermeture de boucle et cohérence visuelle
  de la carte, idéalement face à une vérité terrain.
- Aucun estimateur de pose mobile ni système de vérité terrain n'est encore
  sélectionné et validé dans ce projet; cette limite est affichée dans les
  scripts, le README et le tutoriel afin d'éviter un faux verdict de SLAM.

## LOG-20260717-061 — Tutoriel et audit final de la visualisation

- Les sources Markdown/roff du tutoriel décrivent maintenant le RViz live, la
  commande officielle du saver, la réouverture hors ligne, les critères
  qualitatifs de carte et les prérequis d'une évaluation SLAM quantitative.
- Les PDF canonique et `_EN` ont été reconstruits et comparés avec `cmp` : ils
  sont identiques, comptent 10 pages A4 et ont le SHA-256
  `dd73430cfa88142009d64df0e64980ae342f5f6332c04606f6ecca4bd6bd4347`.
- Les pages 7 à 10 ont été rendues en PNG et inspectées : commandes complètes,
  texte non coupé, marges lisibles et checklist complète.
- Contrôle final : `bash -n` sur les quatre wrappers, `compileall` du paquet,
  `git diff --check`, nouvelle inspection réelle du `.bt` et
  `view-octomap.sh ... --check` : succès. Aucun conteneur
  `unitree_l1_map_viewer` ou `unitree_l1_runtime` n'est resté actif.
- Le PDF chronologique `CONFIGURATION_LOG_UNITREE_L1.pdf` a été reconstruit en
  A4 afin de conserver ces démarches, commandes, résultats et limites.

## LOG-20260717-062 — Frontière Ubuntu hôte / Docker auditée

- Exigence confirmée : Ubuntu 24.04 ne doit exécuter ni ROS 2, ni le pilote,
  ni OctoMap, ni RViz2. Son rôle est limité au client Docker, au serveur X11,
  au partage `/dev/dri`, au port série ciblé et aux fichiers du projet.
- Audit statique de `lidar-launch.sh`, `octomap-launch.sh`,
  `view-octomap.sh`, `save-octomap.sh`, `evaluate-octomap.sh`, des scripts bag,
  build, smoke test et validation : chaque commande ROS existante est déjà
  exécutée par `docker compose run` ou `docker exec`.
- `docker/compose.gui.yaml` partage seulement le socket X11, un cookie Xauthority
  en lecture seule et `/dev/dri`. La fenêtre apparaît sur le bureau hôte, mais
  le processus RViz et son noeud ROS restent dans le conteneur.
- L'image `unitree-l1:humble-v1.0.16` dérive du digest figé
  `ros:humble-ros-base-jammy`; elle contient Ubuntu 22.04, ROS Humble et RViz2.
  Les commandes `command -v ros2` et `command -v rviz2` ne retournent aucun
  binaire sur l'hôte Ubuntu 24.04 actuel.

## LOG-20260717-063 — Refus explicite de ROS/RViz hors Docker

- Nouveau garde commun : `scripts/assert-ros-container.sh`.
- Avant de laisser démarrer une commande ROS, il vérifie `/.dockerenv`,
  `/etc/os-release` avec Ubuntu 22.04, `ROS_DISTRO=humble`, puis impose des
  chemins `ros2` et `rviz2` sous `/opt/ros/humble/`. En mode GUI, il vérifie
  aussi `DISPLAY`, le cookie X11 lisible et `/dev/dri/renderD128`.
- Appel direct sur l'hôte : refus contrôlé, code 40 et message
  `DOCKER_RUNTIME_ASSERT_FAIL: ROS 2 and RViz2 must not run on the Ubuntu 24.04
  host.` Verdict : `HOST_ROS_REFUSAL_PASS`.
- Le garde est maintenant appelé par les wrappers de shell, build, smoke test,
  lancement LiDAR, validation, record/replay/info bag, test synthétique,
  lancement/sauvegarde/évaluation OctoMap et visualisation de carte.
- Défense supplémentaire : les launch files `unitree_l1.launch.py`,
  `l1_octomap.launch.py` et `view_saved_octomap.launch.py` vérifient eux-mêmes
  `Path("/.dockerenv").is_file()` avant de générer un graphe. Ils refusent donc
  aussi un lancement direct qui contournerait les wrappers.
- Nouveau contrôle utilisateur : `scripts/verify-docker-only.sh`. Il imprime
  le rôle de l'hôte, l'image et le PID initial du conteneur, réexécute le garde,
  exige une ligne RViz issue de `docker top` et refuse tout processus `rviz2`
  dont la racine `/proc/PID/root` ne contient pas `/.dockerenv`.

## ERR-20260717-027 — Setup ROS incompatible avec nounset pendant la preuve

- Statut : CORRIGÉ immédiatement; aucun graphe ou fichier de données modifié.
- Premier essai du nouveau garde dans le conteneur :
  `/opt/ros/humble/setup.bash: line 8: AMENT_TRACE_SETUP_FILES: unbound
  variable` car `set -u` était actif avant le setup officiel.
- Correction : suspendre uniquement `nounset` autour de
  `source /opt/ros/humble/setup.bash`, puis le réactiver immédiatement. Les
  modes `errexit` et `pipefail` restent actifs.
- Second essai : `DOCKER_ROS_RUNTIME_PASS` avec Ubuntu 22.04, Humble,
  `/opt/ros/humble/bin/ros2` et `/opt/ros/humble/bin/rviz2`.

## LOG-20260717-064 — Preuve du processus RViz réellement conteneurisé

- Commande de visualisation :
  `./scripts/view-octomap.sh l1_bench_map_20260716.bt`.
- Le garde a confirmé `container=9d124c8092b6 os=ubuntu-22.04 ros=humble
  ros2=/opt/ros/humble/bin/ros2 rviz2=/opt/ros/humble/bin/rviz2 gui=true`.
- Le serveur a rechargé 58 202 noeuds et RViz2 a initialisé OpenGL 4.6.
- Commande de preuve pendant l'affichage :
  `RUNTIME_CONTAINER=unitree_l1_map_viewer ./scripts/verify-docker-only.sh`.
- `docker top` a retourné le PID hôte 39680 mais la commande racine du
  conteneur était
  `/opt/ros/humble/lib/rviz2/rviz2 -d .../saved_octomap.rviz --ros-args -r
  __node:=saved_octomap_rviz2`. Les racines `/proc` ont produit
  `HOST_NATIVE_RVIZ_ABSENT`, puis `DOCKER_ONLY_PIPELINE_PASS`.
- Ctrl-C a arrêté proprement RViz et OctoMap; le conteneur temporaire a été
  supprimé. Le PID hôte est seulement la vue du noyau sur le processus Docker,
  pas une exécution native Ubuntu 24.04.

## LOG-20260717-065 — Régressions après durcissement Docker

- `./scripts/workspace-build.sh` : garde PASS, rosdeps satisfaites et six
  paquets compilés en 4,45 s.
- `./scripts/smoke-test.sh` : garde PASS, chemins ROS/RViz sous
  `/opt/ros/humble`, launch résolu et `SMOKE_TEST_PASS`.
- `./scripts/gui-smoke-test.sh` : garde GUI PASS, X11 disponible, rendu Intel
  direct et OpenGL 4.6, puis `GUI_SMOKE_TEST_PASS`.
- `./scripts/monitor-synthetic-test.sh` : garde PASS et diagnostics sains à
  environ 10 Hz pour le cloud et 30 Hz pour l'IMU.
- `./scripts/bag-info.sh bags/l1_validation_20260716_141042` : garde PASS puis
  lecture des 6 400 messages du bag depuis Docker.
- `RUNTIME_CONTAINER=unitree-l1-dev-run-2516e2383922 OCTOMAP_RVIZ=true
  ./scripts/octomap-launch.sh --check` : contexte GUI Docker, overlay et launch
  validés sans démarrer un nouveau serveur.

## LOG-20260717-066 — PDF Docker-only reconstruits et relus

- Le tutoriel explique désormais la frontière Docker dès la couverture, ajoute
  `verify-docker-only.sh` après le lancement live et saved-map, et impose le
  garde avant chaque alternative interactive `ros2`.
- Les PDF tutoriel canonique et `_EN` sont identiques, font 10 pages A4 et ont
  le SHA-256
  `69947de5592ac7f03eb1e77e2eb76bd7bb63d0de27ee554bae3b9d70422d4edf`.
- Les pages 1, 3, 4, 7, 8 et 10 ont été rendues en PNG puis inspectées : limite
  Docker, commande de preuve, saver officiel, viewer, erreurs et checklist sont
  lisibles sans ligne tronquée.
- Le PDF chronologique a été reconstruit sur 16 pages A4; les marqueurs
  `LOG-20260717-062`, `ERR-20260717-027`, `LOG-20260717-064`,
  `HOST_NATIVE_RVIZ_ABSENT` et `LOG-20260717-065` sont extractibles.

## ERR-20260717-028 — Overlay colcon sourcé sous nounset dans l'essai final

- Statut : CORRIGÉ dans la commande de test; aucun test n'avait encore démarré
  et aucun runtime n'a été modifié.
- Premier essai : après le garde Docker, `set -u` était encore actif lors de
  `source install/setup.bash`; le setup colcon a signalé
  `COLCON_TRACE: unbound variable`.
- Correction : conserver `errexit` et `pipefail`, sourcer l'overlay, puis
  activer `nounset` avant `colcon test`. Les wrappers opérationnels étaient déjà
  corrects car ils sourcent les setups avant leur propre `set -u`.

## LOG-20260717-067 — Tests projet complets dans Docker

- Après ajout du garde directement dans les trois launch files,
  `./scripts/workspace-build.sh` a de nouveau compilé les six paquets en 4,46 s.
- Les commandes `ros2 launch ... --show-args` des launch live et saved-map ont
  produit `DOCKER_LAUNCH_GUARD_PASS` depuis Docker, sans démarrer de noeud.
- Commande corrigée : conteneur Compose éphémère, garde
  `assert-ros-container.sh`, `source install/setup.bash`, puis
  `colcon test --packages-select l1_monitor l1_bringup l1_octomap_bringup
  --event-handlers console_direct+` et `colcon test-result --verbose`.
- Résultat : 5 tests `l1_monitor`, 3 tests `l1_bringup` et 7 tests
  `l1_octomap_bringup`; total 15, 0 erreur, 0 échec, 0 ignoré en 3,10 s.
- Les six avertissements affichés sont la dépréciation Python connue
  `SelectableGroups`; ils n'affectent aucun verdict.

## LOG-20260717-068 — Tutoriel Docker pas à pas : L1, RViz2 et OctoMap

- Demande : produire un tutoriel autonome expliquant comment visualiser et
  utiliser le LiDAR, RViz2 puis OctoMap, avec ROS 2 Humble et RViz2 exclusivement
  dans Docker, jamais nativement sur l'hôte Ubuntu 24.04.
- Nouvelles sources :
  `docs/report/tutorial_docker_lidar_rviz_octomap_unitree_l1.md`,
  `docs/report/tutorial_docker_lidar_rviz_octomap_unitree_l1.roff` et
  `scripts/build-docker-lidar-rviz-octomap-tutorial-pdf.sh`.
- Le tutoriel distingue quatre terminaux hôte : A conserve le pilote et le
  premier RViz2 actifs; B prouve le confinement Docker et valide les messages;
  C ajoute OctoMap et son profil RViz2 combiné; D mesure puis sauvegarde la
  carte. Les invites `host$` et `ros$` rendent explicite le contexte de chaque
  commande. Une procédure quotidienne à une seule fenêtre est aussi fournie.
- Le document explique le flux `/dev/ttyUSB0` vers le pilote, les topics
  `/unilidar/cloud` et `/unilidar/imu`, le rôle purement visuel de RViz2, le TF
  nécessaire à OctoMap, les voxels occupés, le saver officiel, les chemins
  hôte/conteneur et la différence entre une carte de banc fixe et un véritable
  SLAM mobile avec estimateur de pose.
- Commandes de création et de contrôle exécutées :

  ```text
  chmod +x scripts/build-docker-lidar-rviz-octomap-tutorial-pdf.sh
  bash -n scripts/build-docker-lidar-rviz-octomap-tutorial-pdf.sh
  ./scripts/build-docker-lidar-rviz-octomap-tutorial-pdf.sh
  pdfinfo docs/report/pdf/03_octomap_mapping/TUTORIAL_DOCKER_LIDAR_RVIZ_OCTOMAP_UNITREE_L1.pdf
  pdftotext docs/report/pdf/03_octomap_mapping/TUTORIAL_DOCKER_LIDAR_RVIZ_OCTOMAP_UNITREE_L1.pdf -
  pdftoppm -png -r 100 docs/report/pdf/03_octomap_mapping/TUTORIAL_DOCKER_LIDAR_RVIZ_OCTOMAP_UNITREE_L1.pdf /tmp/unitree-combined-tutorial-review/page
  ./scripts/inspect-octomap.sh l1_bench_map_20260716.bt
  ./scripts/view-octomap.sh l1_bench_map_20260716.bt --check
  git diff --check
  ```

- Résultat final du générateur :
  `DOCKER_LIDAR_RVIZ_OCTOMAP_TUTORIAL_PDF_PASS`, 12 pages A4, SHA-256
  `c3a6cb2808ab5942d33988860b91cc845c94c10a9c2dda14d17a752a0e173a37`.
  Les marqueurs `HOST_NATIVE_RVIZ_ABSENT`, `LIDAR_DATA_VALIDATION_PASS`,
  `OCTOMAP_MAPPING_HEALTH_PASS` et `OCTOMAP_SAVE_PASS` sont extractibles.
- Les 12 pages ont été rendues en images et inspectées visuellement : aucune
  commande tronquée, aucun débordement, titres et distinctions hôte/conteneur
  lisibles.
- Contrôle hors ligne de la carte déjà validée : `OCTOMAP_INSPECT_PASS`, type
  `OcTree`, 58 202 nœuds, résolution 0,10 m, 23 276 octets; puis
  `VIEW_OCTOMAP_CHECK_PASS`, viewer isolé en domaine ROS 43. Aucun LiDAR, RViz2
  ou conteneur de cartographie n'a été démarré pendant ces contrôles.

## ERR-20260717-029 — Nettoyage temporaire refusé avant contrôle visuel

- Statut : CORRIGÉ sans modification du projet. La couche de sécurité du
  terminal a refusé avant exécution la commande contenant
  `rm -rf /tmp/unitree-configuration-log-review`; aucune suppression n'a donc
  eu lieu.
- Correction : création du nouveau dossier unique
  `/tmp/unitree-configuration-log-review-1784297761809`, sans supprimer un
  chemin antérieur, puis exécution de :

  ```text
  mkdir -p /tmp/unitree-configuration-log-review-1784297761809
  pdftoppm -f 17 -l 17 -png -r 120 docs/report/pdf/01_environment/CONFIGURATION_LOG_UNITREE_L1.pdf /tmp/unitree-configuration-log-review-1784297761809/page
  ls -l /tmp/unitree-configuration-log-review-1784297761809
  ```

- Résultat : `page-17.png`, 183 835 octets; la dernière page a été inspectée
  visuellement et l'entrée `LOG-20260717-068` est complète et non tronquée.

## LOG-20260717-069 — Journal PDF remis à jour

- Commandes exécutées après l'ajout du nouveau tutoriel :

  ```text
  bash -n scripts/build-configuration-log-pdf.sh
  ./scripts/build-configuration-log-pdf.sh
  pdfinfo docs/report/pdf/01_environment/CONFIGURATION_LOG_UNITREE_L1.pdf
  pdftotext docs/report/pdf/01_environment/CONFIGURATION_LOG_UNITREE_L1.pdf -
  ```

- Premier résultat : `CONFIGURATION_LOG_PDF_PASS`, 17 pages A4. Les marqueurs
  `LOG-20260717-068`, `TUTORIAL_DOCKER_LIDAR_RVIZ_OCTOMAP`, `58 202` et
  `VIEW_OCTOMAP_CHECK_PASS` sont extractibles. Le PDF a ensuite été régénéré
  après consignation de ce contrôle et de la correction temporaire ci-dessus.

## LOG-20260722-070 — Deux rapports complets demandés

- Demande : créer un rapport complet de la configuration depuis le début du
  projet et un second rapport consacré à l'utilisation de RViz2 exclusivement
  dans l'environnement Docker.
- Audit en lecture seule des sources : `AGENTS.md`, journal chronologique,
  décisions, versions, matrice, runbook, Dockerfile/Compose, scripts publics,
  launch files et trois profils RViz2. Aucun conteneur, LiDAR, RViz2, bag ou
  carte n'a été démarré ou modifié pendant cette tâche documentaire.
- Nouvelles sources anglaises :
  `docs/report/complete_configuration_report_unitree_l1.md` et `.roff`, puis
  `docs/report/docker_rviz2_usage_report_unitree_l1.md` et `.roff`.
- Le premier rapport contient 26 chapitres : preuves, chronologie, inventaire,
  architecture, sécurité, versions, dépendances, paquets ROS, build, matériel,
  données réelles, RViz2, rosbag2, OctoMap, Docker-only, les 29 incidents,
  validation, reproduction, limites, Git et conclusion.
- Le second contient 16 chapitres : rôle de RViz2, X11/GPU Docker, sécurité,
  lancement live, navigation, paramètres exacts des profils, preuve Docker,
  lecture du nuage, inspection interactive, enregistrement/rejeu, OctoMap live,
  carte sauvegardée, sauvegarde de profil, dépannage et arrêt propre.
- Générateur ajouté : `scripts/build-complete-reports-pdf.sh`. Il vérifie
  dépendances, bornes de pages, format A4, texte extractible, marqueurs de
  contenu et SHA-256 des deux sorties.

## ERR-20260722-030 — Variables shell interpolées par l'orchestrateur

- Statut : CORRIGÉ; aucune commande shell n'avait démarré et aucun fichier du
  projet n'a été modifié par les deux tentatives concernées.
- Symptôme : la construction JavaScript d'une commande de rendu référençait
  `${full_dir}` / `${full_fix_dir}` avant que Bash crée ces variables, causant
  `ReferenceError: full_dir is not defined`, puis la même erreur pour
  `full_fix_dir`.
- Correction : construire les lignes de commande sans interpolation JavaScript,
  puis laisser Bash développer ses propres variables après `mktemp -d`.
- Résultat : 27 images du rapport configuration et 17 images du rapport RViz2
  ont été produites dans des dossiers temporaires uniques, sans suppression.

## ERR-20260722-031 — Défauts détectés par l'inspection visuelle des PDF

- Statut : CORRIGÉ et revérifié.
- Premier rendu : un titre long du registre des incidents se superposait, un
  titre rosbag2 RViz2 débordait sur son sous-titre et les continuations shell
  terminées par `\` consommaient la macro roff suivante, affichant `.CMD >`.
- Correction : titres raccourcis et utilisation de l'échappement roff `\e` pour
  imprimer le caractère backslash sans absorber la ligne suivante.
- Validation ciblée : pages configuration 14, 20 et 23 puis pages RViz2 11 et
  14 rendues à 120 dpi et relues; titres, `\` et invites `>` sont désormais
  complets et séparés.
- Contrôle du journal : le marqueur final, placé seul exactement à une frontière
  de page, n'apparaissait pas dans son PDF. Il a été rattaché au début de la
  puce suivante avant reconstruction afin d'éviter cette ligne orpheline.

## LOG-20260722-071 — Construction et audit final des deux rapports

- Commandes principales exécutées :

  ```text
  chmod +x scripts/build-complete-reports-pdf.sh
  bash -n scripts/build-complete-reports-pdf.sh
  ./scripts/build-complete-reports-pdf.sh
  pdftoppm -png -r 90 COMPLETE_CONFIGURATION_REPORT_UNITREE_L1.pdf /tmp/.../page
  pdftoppm -png -r 90 DOCKER_RVIZ2_USAGE_REPORT_UNITREE_L1.pdf /tmp/.../page
  pdftotext COMPLETE_CONFIGURATION_REPORT_UNITREE_L1.pdf /tmp/...txt
  pdftotext DOCKER_RVIZ2_USAGE_REPORT_UNITREE_L1.pdf /tmp/...txt
  pdfinfo COMPLETE_CONFIGURATION_REPORT_UNITREE_L1.pdf
  pdfinfo DOCKER_RVIZ2_USAGE_REPORT_UNITREE_L1.pdf
  rg '^\.(CMD|CODE|H1|H2|BU|NOTE|EXPECT|STATUS)' /tmp/...txt
  ```

- Rapport configuration final : 27 pages A4 (couverture + 26 chapitres),
  SHA-256
  `75f0bc68ec8dc0774d3661d242f7338fc67e1cf8f19b9449ab284a9e482bf146`.
- Rapport RViz2 final : 17 pages A4 (couverture + 16 chapitres), SHA-256
  `2441086549e858f3ee8363de785f57575a73381877218b70649e20659f675c78`.
- Les 44 pages ont été inspectées visuellement. Aucun texte/commande n'est
  tronqué, aucune page accidentellement vide n'existe et les contextes `host$`
  et `ros$` sont explicites.
- Verdict `NO_LEAKED_ROFF_DIRECTIVES_PASS`; les nouveaux PDF sont classés sous
  `docs/report/pdf/01_environment/` et `02_lidar_and_rviz/`, puis ajoutés aux
  deux index documentaires. TST-048 consigne ce verdict.

## ERR-20260722-032 — Espaces finaux dans les sources Markdown

- Statut : CORRIGÉ avant commit; aucun PDF de rapport ni résultat technique
  n'était affecté.
- Détection : `git diff --cached --check` a signalé cinq espaces finaux utilisés
  comme sauts de ligne Markdown sur les métadonnées des deux nouveaux rapports.
- Correction : suppression de ces espaces; les informations restent sur des
  lignes distinctes dans la source et la mise en page PDF provient des fichiers
  roff séparés.
- Validation demandée : nouveau `git diff --cached --check` en mode fail-fast
  après remise à jour de l'index.

## ERR-20260723-033 — Marqueur puis retours de ligne du tutoriel d'accès

- Statut : CORRIGÉ pendant la construction documentaire; aucun conteneur, nœud
  ROS, RViz2, OctoMap ou périphérique matériel n'a été démarré.
- La première exécution du générateur a produit un PDF mais s'est arrêtée avec
  le verdict voulu :

  ```text
  Required tutorial marker is missing: Daily command card
  ```

- Cause : le titre visible était `Every-day sequence` tandis que le générateur
  exigeait le marqueur plus explicite `Daily command card`.
- Correction : harmonisation du titre puis nouvelle construction. L'inspection
  des images a ensuite détecté une quote visuelle non appariée et deux lignes de
  commandes accolées. Les guillemets ont été rendus avec `\(dq`, les backslashes
  avec `\(rs`, et l'arrêt propre a été reformulé en texte suivi de `ros$ exit`.
- Validation finale : les pages 4 à 6 ont été rendues à 120 dpi et relues; les
  continuations shell, quotes, invites `host$`/`ros$`, `Ctrl+C` et `exit` sont
  distincts et non tronqués.

## LOG-20260723-072 — Fiche d'accès Docker vers L1, RViz2 et OctoMap

- Demande : expliquer comment rejoindre depuis l'hôte la partie
  `ros@...:/workspace/ros2_ws`, puis lancer le LiDAR, RViz2 et OctoMap depuis
  ce shell, et produire un tutoriel PDF dans le dossier de rapports.
- Vérification en lecture seule du contrat réel des launch files et scripts :
  le lancement combiné expose `port`, `static_sensor` et `rviz`; le shell public
  `docker-shell.sh --gui --lidar` monte X11, `/dev/dri`, le projet et seulement
  le port série sélectionné.
- Livrables ajoutés :
  `docs/report/tutorial_access_docker_lidar_rviz_octomap_unitree_l1.md`,
  `docs/report/tutorial_access_docker_lidar_rviz_octomap_unitree_l1.roff`,
  `scripts/build-docker-access-tutorial-pdf.sh` et
  `docs/report/pdf/03_octomap_mapping/TUTORIAL_ACCESS_DOCKER_LIDAR_RVIZ_OCTOMAP_UNITREE_L1.pdf`.
  Les deux index de rapports ont été mis à jour.
- Le guide anglais de six pages distingue les invites hôte/conteneur, explique
  les chemins bind-mountés, vérifie Docker/GUI/LiDAR, lance le graphe complet
  avec une seule commande, décrit les displays RViz2, corrige `rviz` en
  `rviz2`, explique la queue TF et distingue le banc fixe d'un SLAM mobile.
- Commandes de vérification documentaire et du contrat exécutées :

  ```text
  rg -n "DeclareLaunchArgument|LaunchConfiguration|IncludeLaunchDescription|launch_arguments|LIDAR_PORT|static_sensor|rviz|port" ros2_ws/src/l1_octomap_bringup/launch/unitree_l1_octomap.launch.py
  sed -n '1,240p' ros2_ws/src/l1_octomap_bringup/launch/unitree_l1_octomap.launch.py
  sed -n '1,260p' scripts/docker-shell.sh
  sed -n '1,180p' scripts/gui-smoke-test.sh
  sed -n '1,180p' scripts/check-lidar.sh
  sed -n '1,260p' scripts/assert-ros-container.sh
  sed -n '1,220p' docker/compose.gui.yaml
  sed -n '1,180p' docker/compose.lidar.yaml
  sed -n '1,240p' docker/compose.yaml
  ```

- Commandes exactes de construction et de validation :

  ```text
  chmod +x scripts/build-docker-access-tutorial-pdf.sh
  bash -n scripts/build-docker-access-tutorial-pdf.sh
  ./scripts/build-docker-access-tutorial-pdf.sh
  pdfinfo docs/report/pdf/03_octomap_mapping/TUTORIAL_ACCESS_DOCKER_LIDAR_RVIZ_OCTOMAP_UNITREE_L1.pdf
  pdftotext docs/report/pdf/03_octomap_mapping/TUTORIAL_ACCESS_DOCKER_LIDAR_RVIZ_OCTOMAP_UNITREE_L1.pdf - | rg -n "docker-shell\.sh --gui --lidar|REQUIRE_GUI=true|LIDAR_DEVICE_OK|unitree_l1_octomap\.launch\.py|rviz2|Daily command card"
  review_dir="$(mktemp -d /tmp/unitree-l1-access-pdf.XXXXXX)"
  pdftoppm -png -r 120 docs/report/pdf/03_octomap_mapping/TUTORIAL_ACCESS_DOCKER_LIDAR_RVIZ_OCTOMAP_UNITREE_L1.pdf "${review_dir}/page"
  review_dir="$(mktemp -d /tmp/unitree-l1-access-pdf-fixed.XXXXXX)"
  pdftoppm -f 5 -l 6 -png -r 120 docs/report/pdf/03_octomap_mapping/TUTORIAL_ACCESS_DOCKER_LIDAR_RVIZ_OCTOMAP_UNITREE_L1.pdf "${review_dir}/page"
  review_dir="$(mktemp -d /tmp/unitree-l1-access-pdf-final.XXXXXX)"
  pdftoppm -png -r 120 docs/report/pdf/03_octomap_mapping/TUTORIAL_ACCESS_DOCKER_LIDAR_RVIZ_OCTOMAP_UNITREE_L1.pdf "${review_dir}/page"
  ```

- Résultat final :
  `DOCKER_ACCESS_TUTORIAL_PDF_PASS`, 6 pages A4, 25 639 octets, SHA-256
  `4f939e4aeaad30dd47fb79d239f8ea390b57c67c569e3f342e10192c52af7089`.
  Les six pages ont été inspectées visuellement. Aucun ROS, RViz2, OctoMap ou
  matériel n'a été lancé pour cette tâche documentaire.
- Contrôles finaux et remise à jour du journal PDF :

  ```text
  stat -c '%n %s bytes' docs/report/pdf/03_octomap_mapping/TUTORIAL_ACCESS_DOCKER_LIDAR_RVIZ_OCTOMAP_UNITREE_L1.pdf
  sha256sum docs/report/pdf/03_octomap_mapping/TUTORIAL_ACCESS_DOCKER_LIDAR_RVIZ_OCTOMAP_UNITREE_L1.pdf
  bash -n scripts/build-configuration-log-pdf.sh
  ./scripts/build-configuration-log-pdf.sh
  pdfinfo docs/report/pdf/01_environment/CONFIGURATION_LOG_UNITREE_L1.pdf
  pdftotext docs/report/pdf/01_environment/CONFIGURATION_LOG_UNITREE_L1.pdf -
  git diff --check
  git status --short
  ```

- Résultat du journal : `CONFIGURATION_LOG_PDF_PASS`, 20 pages A4; les marqueurs
  `ERR-20260723-033`, `LOG-20260723-072`,
  `DOCKER_ACCESS_TUTORIAL_PDF_PASS` et le SHA-256 final sont extractibles.

## ERR-20260723-034 — RViz2 vide, profil invalide et runtimes dupliqués

- Statut : DIAGNOSTIQUÉ, correction opératoire à effectuer par l'utilisateur.
  Aucun conteneur, processus, périphérique ou fichier de données n'a été arrêté
  ou modifié pendant ce diagnostic.
- Symptôme visible : RViz2 s'ouvre avec uniquement `Global Options` et `Grid`;
  aucun `PointCloud2` ni `MarkerArray` n'est chargé et la vue reste vide.
- Première erreur : la commande saisie contient
  `l1_octomap_bingup` au lieu de `l1_octomap_bringup`. Le `r` de `bringup`
  manque. `ros2 pkg prefix` répond donc `Package not found`; sa substitution
  devient vide et le processus réel observé est :

  ```text
  rviz2 -d /config/l1_octomap.rviz
  ```

  Ce chemin n'est pas le profil installé du projet. RViz2 ouvre alors sa
  configuration par défaut, ce qui explique la grille seule.
- La première tentative `rviz2 -d` est également incomplète : l'option `-d`
  exige immédiatement un chemin de fichier, d'où le message normal
  `Missing value after '-d'`.
- Les avertissements `XDG_RUNTIME_DIR not set` et
  `Stereo is NOT SUPPORTED` ne sont pas la cause. RViz2 annonce OpenGL 4.6 et
  sa fenêtre s'affiche : la chaîne X11/GPU fonctionne.
- Deuxième erreur indépendante : trois conteneurs one-shot du projet sont
  simultanément actifs sur `ROS_DOMAIN_ID=42` et le réseau
  `unitree-l1_default` :

  ```text
  5c499351756c  unitree-l1-dev-run-ed82f19c9730  Up 14 minutes
  6697f2587cfb  unitree-l1-dev-run-4aadde0048ea  Up 44 minutes
  62e9627c4042  unitree-l1-dev-run-2516e2383922  Up 6 days
  ```

- `5c499...` et `6697...` exécutent chacun un pilote L1, `l1_monitor`, un TF
  statique et `octomap_server`; `62e962...` exécute le RViz2 au mauvais chemin.
  Tous exposent `/dev/ttyUSB0` comme `/dev/unitree_lidar`.
- Le graphe ROS confirme deux exemplaires de
  `/unitree_lidar_ros2_node`, `/l1_monitor`, `/l1_static_lidar_transform` et
  `/octomap_server`, avec l'avertissement ROS
  `nodes in the graph that share an exact name`.
- Les deux moniteurs signalent maintenant
  `cloud=no messages received (0.00Hz, points=None)`. Un moniteur ne reçoit plus
  non plus d'IMU; l'autre montre uniquement un dernier message vieux de plus de
  2 600 s. RViz2 ne peut donc afficher aucun nuage ou voxel valide.
- Vérifications en lecture seule exécutées :

  ```text
  docker ps --no-trunc --format 'ID={{.ID}} NAME={{.Names}} IMAGE={{.Image}} STATUS={{.Status}} NETWORKS={{.Networks}}'
  docker ps -a --filter 'ancestor=unitree-l1:humble-v1.0.16' --format 'ID={{.ID}} NAME={{.Names}} STATUS={{.Status}}'
  docker inspect --format 'workdir={{.Config.WorkingDir}} network_mode={{.HostConfig.NetworkMode}} ros_domain={{range .Config.Env}}{{if eq . "ROS_DOMAIN_ID=42"}}{{.}}{{end}}{{end}}' CONTAINER
  docker top CONTAINER -eo pid,args
  docker exec CONTAINER bash -lc 'source /opt/ros/humble/setup.bash; source /workspace/ros2_ws/install/setup.bash; ros2 pkg prefix --share l1_octomap_bringup'
  docker logs --tail 16 CONTAINER
  docker logs CONTAINER | rg -n -i 'rviz|process has died|exception|error|failed|serial|port|device|cloud=stream healthy'
  docker top unitree-l1-dev-run-ed82f19c9730 -eo pid,ppid,stat,args
  docker top unitree-l1-dev-run-4aadde0048ea -eo pid,ppid,stat,args
  docker inspect --format '{{range .HostConfig.Devices}}{{.PathOnHost}} -> {{.PathInContainer}}{{println}}{{end}}' unitree-l1-dev-run-ed82f19c9730 unitree-l1-dev-run-4aadde0048ea unitree-l1-dev-run-2516e2383922
  docker exec CONTAINER bash -lc 'source /opt/ros/humble/setup.bash; source /workspace/ros2_ws/install/setup.bash; timeout 6 ros2 node list; timeout 6 ros2 topic list -t'
  ./scripts/check-lidar.sh
  ```

- Correction sûre prescrite : arrêter proprement chaque ancien launch avec
  `Ctrl+C`, fermer son RViz2, exécuter `exit` dans chaque shell `ros@`, puis
  créer un seul shell avec `docker-shell.sh --gui --lidar`. Dans ce shell,
  sourcer Humble et l'overlay puis exécuter un unique
  `unitree_l1_octomap.launch.py` avec `rviz:=true`.
- Commande standalone durcie si le graphe est déjà sain dans le même conteneur :

  ```text
  RVIZ_CONFIG="$(ros2 pkg prefix --share l1_octomap_bringup)/config/l1_octomap.rviz"
  test -r "$RVIZ_CONFIG" && rviz2 -d "$RVIZ_CONFIG"
  ```

  Le `&&` empêche RViz2 de démarrer avec un faux chemin si la recherche du
  paquet échoue.

## ERR-20260723-035 — `COLCON_TRACE` non défini pendant le premier test

- Statut : CORRIGÉ; la construction du paquet avait réussi et aucun test de
  code n'avait encore commencé au moment de l'arrêt.
- Commande concernée : construction puis test de `l1_octomap_bringup` dans un
  conteneur Docker temporaire, headless et sans périphérique LiDAR.
- Symptôme après `Summary: 1 package finished` :

  ```text
  install/setup.bash: line 11: COLCON_TRACE: unbound variable
  ```

- Cause : le wrapper utilisait `set -u` pendant le `source
  install/setup.bash`; le setup Colcon consulte la variable optionnelle
  `COLCON_TRACE`.
- Correction : exécuter `set +u`, sourcer l'overlay, puis rétablir `set -u`.
- Résultat : 8 tests ont d'abord passé, puis 9/9 après ajout du test de
  régression dynamique final; 0 erreur, 0 échec, 0 test ignoré.

## LOG-20260723-073 — Correction du lancement combiné `rviz:=true`

- La photo montrait d'abord la faute utilisateur
  `l1_octomap_bingup` et le faux chemin `/config/l1_octomap.rviz`. L'audit du
  processus combiné a ensuite révélé un défaut distinct dans le projet :
  malgré le message annonçant RViz, aucun enfant `rviz2` ne démarrait.
- Cause dans `unitree_l1_octomap.launch.py` : le parent et ses deux launch files
  inclus utilisaient tous l'argument `rviz`. Le premier enfant recevait
  `rviz=false`; cette configuration non scopée restait dans le contexte, donc
  la condition RViz du parent était finalement évaluée à `false`.
- Correction rétrocompatible :
  - conserver l'interface publique `rviz:=true`;
  - entourer chaque `IncludeLaunchDescription` d'un
    `GroupAction(scoped=True)`;
  - forcer `rviz=false` dans chacun des deux enfants;
  - laisser un seul nœud RViz2 parent charger le profil combiné.
- Test de régression permanent ajouté à
  `ros2_ws/src/l1_octomap_bringup/test/test_launch_file.py`. Il exécute un
  `LaunchService` avec deux enfants synthétiques et vérifie :

  ```text
  child_values  = ["false", "false"]
  parent_values = ["true"]
  final rviz    = "true"
  ```

- Construction et tests dans Docker headless, sans LiDAR :

  ```text
  export HOST_UID="$(id -u)"
  export HOST_GID="$(id -g)"
  docker compose -f docker/compose.yaml run --rm dev bash -lc '
    set -euo pipefail
    /workspace/scripts/assert-ros-container.sh
    cd /workspace/ros2_ws
    colcon build --packages-select l1_octomap_bringup \
      --symlink-install --event-handlers console_direct+
    set +u
    source install/setup.bash
    set -u
    colcon test --packages-select l1_octomap_bringup \
      --event-handlers console_direct+
    colcon test-result \
      --test-result-base build/l1_octomap_bringup --verbose
  '
  ```

- Verdict final du paquet : 9 tests, 0 erreur, 0 échec, 0 ignoré. Les deux
  avertissements `SelectableGroups` sont la dépréciation Python connue.
- Preuve d'exécution sans matériel : un conteneur temporaire sans
  `/dev/unitree_lidar` a lancé le graphe sur le port volontairement absent
  `/tmp/NO_UNITREE_LIDAR_FOR_RVIZ_SCOPE_TEST`. Le log contient exactement :

  ```text
  [INFO] [rviz2-5]: process started
  /opt/ros/humble/lib/rviz2/rviz2
  -d /workspace/ros2_ws/install/l1_octomap_bringup/share/
     l1_octomap_bringup/config/l1_octomap.rviz
  COMBINED_RVIZ_SCOPE_PASS rviz_processes=1 launch_rc=124 lidar=absent
  ```

  L'erreur Qt `could not connect to display` était attendue, car ce test était
  volontairement headless; elle prouve néanmoins que la condition lance un
  unique processus avec le bon profil installé. Le timeout envoie ensuite
  SIGINT et le conteneur `--rm` disparaît.
- Le tutoriel d'accès a été complété avec la correction
  `bringup`/`bingup`, le sourcing de l'overlay et la règle « un LiDAR, un
  pilote, un conteneur ». Commandes documentaires :

  ```text
  bash -n scripts/build-docker-access-tutorial-pdf.sh
  ./scripts/build-docker-access-tutorial-pdf.sh
  pdftoppm -png -r 120 docs/report/pdf/03_octomap_mapping/TUTORIAL_ACCESS_DOCKER_LIDAR_RVIZ_OCTOMAP_UNITREE_L1.pdf /tmp/unitree-l1-access-rviz-fix.XXXXXX/page
  pdftoppm -f 6 -l 6 -png -r 120 docs/report/pdf/03_octomap_mapping/TUTORIAL_ACCESS_DOCKER_LIDAR_RVIZ_OCTOMAP_UNITREE_L1.pdf /tmp/unitree-l1-access-rviz-fix-final.XXXXXX/page
  sha256sum docs/report/pdf/03_octomap_mapping/TUTORIAL_ACCESS_DOCKER_LIDAR_RVIZ_OCTOMAP_UNITREE_L1.pdf
  stat -c '%s bytes' docs/report/pdf/03_octomap_mapping/TUTORIAL_ACCESS_DOCKER_LIDAR_RVIZ_OCTOMAP_UNITREE_L1.pdf
  ```

- PDF final : 6 pages A4, 25 819 octets, inspection visuelle des pages
  modifiées réussie, SHA-256
  `da1cfb631403217c62f8e9fdf557655107990ba978918b47da04ca5efb70dbef`.
- Limite restante : les trois anciens conteneurs visibles dans la photo n'ont
  volontairement pas été stoppés. TST-050 reste en échec diagnostiqué jusqu'au
  redémarrage propre d'un seul runtime et à la validation du flux réel.

## ERR-20260723-036 — Faux fichier installé absent depuis l'hôte

- Statut : CORRIGÉ sans changement de code.
- Symptôme : après le build `--symlink-install`, un `rg` exécuté depuis l'hôte
  sur
  `ros2_ws/install/l1_octomap_bringup/share/l1_octomap_bringup/launch/`
  a répondu `No such file or directory`.
- Cause : les liens symboliques Colcon pointent volontairement vers
  `/workspace/ros2_ws/build/...`, chemin Docker qui n'existe pas dans l'espace
  de noms de l'hôte. Ce projet est Docker-only; tester ce lien depuis Ubuntu
  24.04 est donc un contrôle invalide.
- Correction : répéter le contrôle dans le conteneur, après sourcing de Humble
  et de l'overlay :

  ```text
  docker exec unitree-l1-dev-run-2516e2383922 bash -lc '
    source /opt/ros/humble/setup.bash
    source /workspace/ros2_ws/install/setup.bash
    launch_file="$(ros2 pkg prefix --share l1_octomap_bringup)/launch/unitree_l1_octomap.launch.py"
    test -r "${launch_file}"
    grep -nE "GroupAction|scoped=True|\"rviz\": \"false\"" "${launch_file}"
    ros2 launch l1_octomap_bringup unitree_l1_octomap.launch.py --show-args
  '
  ```

- Résultat : fichier installé lisible sous `/workspace`, deux
  `GroupAction(scoped=True)`, deux enfants `rviz=false`, et les arguments
  publics `port`, `static_sensor` et `rviz` correctement résolus. Aucun nœud
  n'a été lancé par `--show-args`.

## LOG-20260723-074 — Manuel ingénieur complet L1, Docker, RViz2 et OctoMap

- Demande : produire un PDF unique, compréhensible par un ingénieur, permettant
  de reconstruire et d'exécuter manuellement toute la chaîne depuis le prompt
  `ros@...:/workspace/ros2_ws`, en trois parties strictes :
  environnement L1/Docker, RViz2, puis OctoMap.
- Sources réelles relues avant rédaction :
  - `docker/Dockerfile`, les trois fichiers Compose et l'entrypoint;
  - `docker-shell.sh`, les gardes Docker/GUI/LiDAR et les scripts de build;
  - `colcon_defaults.yaml` et `dependencies.repos`;
  - YAML, launch files, profils RViz et tests des trois paquets `l1_*`;
  - code fournisseur concernant le nom interne, le port UART et les publishers;
  - code amont `octomap_server` concernant topics, services, QoS, insertion,
    saver et paramètres;
  - décisions, versions, runbook matériel, rapports existants et preuves.
- Correction technique importante intégrée au manuel : le nom interne du nœud
  fournisseur est `unitre_lidar_sdk_node`, tandis que le YAML projet est sous
  `unitree_lidar_ros2_node`. La commande directe documentée contient donc :

  ```text
  ros2 run unitree_lidar_ros2 unitree_lidar_ros2_node \
    --ros-args \
    -r __node:=unitree_lidar_ros2_node \
    --params-file "$L1_CONFIG" \
    -p port:=/dev/unitree_lidar
  ```

  Sans le remapping de nom, la section YAML ne sélectionne pas le nœud direct
  comme prévu. Le launch projet fixe déjà explicitement le bon nom.
- Le manuel distingue chaque bloc `HOST` et `DOCKER`, explique but, entrée,
  sortie, effet et interprétation, et décompose l'expérience OctoMap sur cinq
  shells du même conteneur : pilote, moniteur, TF, serveur et RViz2.
- Frontière scientifique explicitée : l'identité
  `map -> unilidar_lidar` est uniquement valable sur banc immobile. OctoMap ne
  calcule pas la pose; le mobile exige `static_sensor:=false`, une chaîne TF
  horodatée externe et une évaluation de trajectoire.
- Fichiers ajoutés :

  ```text
  docs/report/engineering_manual_unitree_l1_docker_rviz_octomap.md
  docs/report/engineering_manual_unitree_l1_docker_rviz_octomap.roff
  scripts/generate-engineering-manual-roff.py
  scripts/build-engineering-manual-pdf.sh
  docs/report/pdf/03_octomap_mapping/
    ENGINEERING_MANUAL_UNITREE_L1_DOCKER_RVIZ_OCTOMAP.pdf
  ```

- Commande de construction finale :

  ```text
  ./scripts/build-engineering-manual-pdf.sh
  ```

- Le générateur :
  - transforme mécaniquement la source Markdown contrainte en source groff;
  - préserve les apostrophes ASCII des commandes;
  - produit un PDF couleur A4;
  - exige 30 à 55 pages;
  - extrait le texte et vérifie les marqueurs des trois parties, du runtime,
    du pilote, de RViz, du correctif de scope, d'OctoMap et du saver;
  - refuse le faux chemin `src/install/setup.bash` étiqueté comme correct.

## ERR-20260723-037 — Délimiteur Python du gabarit groff

- Statut : CORRIGÉ.
- Premier essai :

  ```text
  ./scripts/build-engineering-manual-pdf.sh
  ```

- Erreur :

  ```text
  SyntaxError: unexpected character after line continuation character
  ```

- Cause : le pied de page groff contenait trois apostrophes consécutives dans
  une chaîne Python délimitée elle-même par trois apostrophes.
- Correction : employer une chaîne brute délimitée par trois guillemets
  doubles. La source groff est ensuite générée sans erreur.

## ERR-20260723-038 — Marqueur PDF trop long après retour typographique

- Statut : CORRIGÉ.
- Symptôme : le PDF de 30 pages était produit, mais le build refusait :

  ```text
  Required engineering-manual marker is missing:
  Part 1 — Unitree L1 configuration and Docker environment
  ```

- Cause : `pdftotext` insérait un retour de ligne dans le grand titre de partie.
- Correction : tester le préfixe stable de chaque titre plutôt que la ligne
  complète. Les autres marqueurs techniques restent stricts.

## ERR-20260723-039 — Ligne sous le pied de page et apostrophe non copiable

- Statut : CORRIGÉ.
- Le premier contrôle `pdftotext -raw` a montré que
  `docker compose version` tombait sous le pied de page et qu'une apostrophe
  de format telle que `'%g'` devenait typographique.
- Corrections du gabarit :
  - le piège de pied de page provoque le changement de page;
  - les lignes de code convertissent l'apostrophe source vers le glyphe groff
    ASCII `\(aq`;
  - le build exige désormais aussi le marqueur `docker compose version`.
- Vérification :

  ```text
  pdftotext -raw \
    docs/report/pdf/03_octomap_mapping/ENGINEERING_MANUAL_UNITREE_L1_DOCKER_RVIZ_OCTOMAP.pdf \
    /tmp/engineering-manual-final.txt
  ```

  Les commandes extraites contiennent bien `stat -Lc '%g'`.

## ERR-20260723-040 — Placeholders Bash et page blanche du piège

- Statut : CORRIGÉ.
- Le lint des blocs `bash` a détecté :

  ```text
  syntax error near unexpected token `newline'
  readlink -e /dev/serial/by-id/<YOUR_UNITREE_ADAPTER>
  ```

- Cause : un placeholder entre chevrons est interprété par Bash comme une
  redirection si le lecteur oublie de le remplacer.
- Correction : utiliser des mots factices valides et très explicites :

  ```text
  PASTE_STABLE_UNITREE_LINK_NAME_HERE
  CONTAINER_ID_OR_NAME
  THE_SINGLE_CONTAINER_NAME
  ```

- Deuxième symptôme : après ajout d'une ligne, la forme `.bp` du saut dans le
  piège groff pouvait créer une page vide. La forme sans rupture `'bp` a
  supprimé le double saut.
- Lint final :

  ```text
  awk '
    /^```bash[[:space:]]*$/ {in_bash=1; next}
    /^```[[:space:]]*$/ && in_bash {
      in_bash=0; print ""; next
    }
    in_bash {print}
  ' docs/report/engineering_manual_unitree_l1_docker_rviz_octomap.md |
    bash -n
  ```

  Résultat : `ENGINEERING_MANUAL_BASH_SYNTAX_PASS`.

## LOG-20260723-075 — Validation finale du manuel ingénieur

- Compatibilité des options ROS contrôlée en lecture seule dans le conteneur
  Humble existant :

  ```text
  docker exec 5c499351756c bash -lc '
    source /opt/ros/humble/setup.bash
    source /workspace/ros2_ws/install/setup.bash
    ros2 topic echo --help
    ros2 pkg executables octomap_server
    ros2 pkg executables unitree_lidar_ros2
  '
  ```

- Le `--help` réel confirme `--field`, `--truncate-length`, `--filter`,
  `--once` et les options QoS utilisées. Les exécutables réels confirment
  `octomap_saver_node`, `octomap_server_node` et
  `unitree_lidar_ros2_node`.
- Le code source amont confirme les noms de services
  `/octomap_server/reset` et `/octomap_server/clear_bbox`, les publishers de
  carte et `SensorDataQoS`.
- Validation du document :

  ```text
  ./scripts/build-engineering-manual-pdf.sh
  pdfinfo \
    docs/report/pdf/03_octomap_mapping/ENGINEERING_MANUAL_UNITREE_L1_DOCKER_RVIZ_OCTOMAP.pdf
  pdftoppm -png -r 96 \
    docs/report/pdf/03_octomap_mapping/ENGINEERING_MANUAL_UNITREE_L1_DOCKER_RVIZ_OCTOMAP.pdf \
    /tmp/engineering-manual-render.XXXXXX/page
  ```

- Les 30 pages ont un contenu non vide; la couverture et toutes les pages ont
  été inspectées visuellement par planches de contact. Aucun débordement, pied
  de page superposé ou directive groff visible.
- Un contrôle indépendant a normalisé les 813 lignes significatives des blocs
  de code de la source et les a recherchées dans le texte brut extrait du PDF :

  ```text
  PDF_CODE_LINE_CHECK checked=813 missing=0
  ```

- Résultat final :

  ```text
  ENGINEERING_MANUAL_PDF_PASS
  pages=30
  bytes=83055
  sha256=13b6dbee62957330f005d4a091d33e0720d2f6520db20e526027fba5d8f52fbf
  ```

- Les index `docs/report/README.md` et `docs/report/pdf/README.md` placent le
  nouveau manuel en première lecture.
- Limite matérielle inchangée : les trois conteneurs live observés restent
  actifs parce que leur arrêt nécessite l'action explicite de l'utilisateur.
  Le manuel commence donc par la procédure d'arrêt propre; TST-050 demeure
  `FAIL_DIAGNOSED`.
