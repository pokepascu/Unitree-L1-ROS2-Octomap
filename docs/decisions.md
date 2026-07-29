# Registre des décisions

## DEC-001 — Isoler ROS 2 Humble dans Docker

- Statut : acceptée.
- Contrainte : l’hôte est Ubuntu 24.04 Noble alors que les binaires Humble ciblent
  Ubuntu 22.04 Jammy.
- Options examinées : dépôts Jammy sur l’hôte, compilation native Noble, conteneur
  Jammy/Humble.
- Décision : conserver l’hôte Noble intact et utiliser Docker Jammy/Humble.
- Justification : compatibilité, isolation et reconstruction documentée.
- Réexamen : seulement si Humble doit ultérieurement fonctionner sans Docker.

## DEC-002 — Conserver le SDK fournisseur intact

- Statut : acceptée.
- Décision : figer `unilidar_sdk` sur un commit et placer les adaptations dans un
  paquet `l1_bringup` séparé.
- Justification : différencier clairement le code Unitree et le code du projet.

## DEC-003 — Séparer le Compose matériel

- Statut : acceptée.
- Décision : le Compose principal démarre sans LiDAR ; un override ajoute ensuite
  un seul périphérique série et son GID.
- Justification : un chemin `/dev/ttyUSB0` absent empêcherait sinon tout test et
  encouragerait l’usage injustifié du mode privilégié.

## DEC-004 — Ne pas utiliser le réseau hôte par défaut

- Statut : acceptée.
- Décision : utiliser le réseau bridge Docker tant que tous les nœuds ROS résident
  dans le même conteneur et que le L1 utilise l’interface série.
- Justification : réduire l’exposition ; `network_mode: host` sera réévalué seulement
  pour DDS inter-hôte ou un adaptateur série-vers-UDP explicitement identifié.

## DEC-005 — Monter l’autorisation X11 en lecture seule

- Statut : acceptée.
- Décision : monter `${XAUTHORITY}` et `/tmp/.X11-unix`, sans `xhost +`.
- Justification : tester RViz2 sans ouvrir globalement le serveur X.

## DEC-006 — Ajouter un paquet `l1_bringup`

- Statut : acceptée.
- Décision : encapsuler le nœud Unitree dans un launch projet paramétrable.
- Justification : le launch fournisseur fixe le port et les topics en littéral ;
  une couche séparée conserve le vendor propre et permet `/dev/unitree_lidar`.

## DEC-007 — Accepter provisoirement Humble/PCL 1.12

- Statut : acceptée pour la phase matérielle.
- Contexte : Unitree documente Ubuntu 20.04, Foxy et PCL 1.10 pour cette version.
- Preuves : compilation et lien réussis sans patch, aucune bibliothèque manquante,
  archive GCC 9.4 compatible avec le runtime GCC 11.4/GLIBCXX disponible.
- Limite : seule la réception de vraies données validera le comportement complet.

## DEC-008 — Ajouter un moniteur non intrusif

- Statut : acceptée.
- Décision : `l1_monitor` s'abonne sans republier ni filtrer les données brutes et
  publie deux statuts sur `/diagnostics`.
- QoS : Reliable, Volatile, KeepLast(10), identique au contrat du pilote.
- Seuils provisoires : rapport 2 s, timeout 3 s, âge d'en-tête 1 s, cloud 5 Hz,
  IMU 20 Hz, fenêtre 100 messages.
- Justification : ces valeurs sont des seuils d'alarme conservateurs, pas des
  spécifications Unitree ; elles seront réglées après mesure réelle.

## DEC-009 — Isoler le domaine ROS du projet

- Statut : acceptée.
- Décision : `ROS_DOMAIN_ID=42` par défaut pour éviter de mélanger le graphe du
  projet avec d'autres expériences ROS locales. L'audit isolé a utilisé 187.
- Limite : tous les processus qui doivent communiquer doivent partager le domaine.

## DEC-010 — Ignorer deux clés rosdep seulement

- Statut : acceptée.
- Décision : `workspace-build.sh` ignore `ament_python` et `pcl`, sans définition
  rosdep exploitable dans ces manifestes, après vérification de leur installation.
- Justification : conserver le manifeste fournisseur intact et laisser `rosdep`
  contrôler toutes les autres dépendances.

## DEC-011 — Séparer GUI et matériel

- Statut : acceptée.
- Décision : `compose.yaml` reste utilisable sans affichage ni capteur ;
  `compose.gui.yaml` ajoute X11/DRI et `compose.lidar.yaml` ajoute un seul tty/GID.
- Justification : fonctionnement headless, moindre privilège et erreurs explicites.

## DEC-012 — Différer Point-LIO jusqu'au bag réel

- Statut : acceptée.
- Décision : ne pas figer ou adapter un port Point-LIO avant validation des champs
  PointCloud2, timestamps, fréquences, unités et extrinsèques du L1 réel.
- Justification : ces propriétés déterminent la branche et les paramètres utiles ;
  un choix anticipé créerait une fausse validation sans données.

## DEC-013 — Conserver les preuves avant matériel

- Statut : acceptée.
- Décision : versionner journal, matrices, PDF d'entrée, scripts, hashes et extraits
  `colcon`; laisser bags/cartes volumineux hors Git.
- Justification : le futur rapport PDF doit distinguer commande, résultat, erreur,
  correction, interprétation et limites.

## DEC-014 — Restreindre la découverte `colcon` au workspace ROS 2

- Statut : acceptée et validée.
- Problème : le dépôt Unitree contient aussi `unitree_lidar_ros` (ROS 1/catkin)
  et un SDK CMake brut sans cible d'installation.
- Décision : utiliser `ros2_ws/colcon_defaults.yaml` avec des `base-paths`
  explicites et conserver les mêmes racines dans `workspace-build.sh`.
- Justification : la commande simple `colcon build` reste utilisable depuis la
  racine, sans installer catkin ni modifier le fournisseur.

## DEC-015 — Intégrer OctoMap dans une couche projet séparée

- Statut : acceptée et validée sur données réelles.
- Décision : figer `octomap_mapping` 2.3.1 comme dépendance externe et placer
  remappage, paramètres, launch et profil RViz dans `l1_octomap_bringup`.
- Justification : Unitree et OctoMap restent intacts ; le projet contrôle
  explicitement `/unilidar/cloud -> cloud_in`, les frames et la résolution.

## DEC-016 — Séparer carte de banc et cartographie mobile

- Statut : acceptée.
- Banc : `static_sensor:=true` publie une identité `map -> unilidar_lidar`,
  uniquement lorsque le capteur est immobile.
- Mobile : `static_sensor:=false` exige une TF dynamique fournie par une
  odométrie ou un SLAM externe.
- Justification : OctoMap construit l'occupation 3D mais n'est pas, seul, un
  estimateur de pose.

## DEC-017 — Définir clairement la frontière OctoMap / SLAM

- Statut : acceptée et validée sur données réelles immobiles.
- Décision : considérer `octomap_server` comme la couche de cartographie 3D ;
  ne pas l'annoncer comme un estimateur de pose ou un SLAM complet.
- Justification : la chaîne validée reçoit un `PointCloud2` et demande une TF
  `map -> unilidar_lidar`. La pose dynamique doit venir d'une odométrie ou d'un
  futur SLAM (Point-LIO/SLAM Toolbox).

## DEC-018 — Encadrer la sauvegarde des cartes

- Statut : acceptée et validée.
- Décision : utiliser `scripts/save-octomap.sh` pour appeler le saver officiel,
  refuser l'écrasement et vérifier un fichier `.bt` ou `.ot` non vide dans
  `maps/`.
- Justification : une carte est une donnée générée et peut être volumineuse ;
  elle reste hors Git tandis que la commande et sa preuve sont versionnées.
