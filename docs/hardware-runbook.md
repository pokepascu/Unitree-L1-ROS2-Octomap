# Procédure de raccordement et de validation du Unitree L1

Cette procédure commence seulement quand le L1 et son adaptateur Unitree sont
disponibles. La préparation logicielle, le build et les tests sans données sont
déjà réalisables sans capteur.

## 1. Sécurité avant alimentation

- Immobiliser le L1 et dégager sa zone mécanique.
- Couper l'alimentation avant toute modification de câblage.
- Utiliser le câble et l'adaptateur Unitree décrits par le manuel.
- Respecter l'alimentation séparée 12 V / 1 A et sa polarité.
- Ne pas alimenter le L1 depuis le 5 V USB.
- Ne jamais relier directement le TTL 3,3 V à de l'USB ou du RS-232.
- Le pilote utilise 2 000 000 bauds ; ne pas modifier cette valeur sans preuve.

Le branchement attendu est : L1 vers l'adaptateur série Unitree, adaptateur vers
USB du PC, et alimentation 12 V séparée. La mécanique peut démarrer ; garder les
mains, câbles et objets hors de sa zone.

## 2. Identifier le nouveau port sans modifier l'hôte

Avant le branchement, puis après la connexion USB et l'alimentation :

```bash
cd /home/isr/unitree_l1_project
./scripts/check-lidar.sh
```

Le script attend `udev`, affiche USB, `/dev/serial/by-id`, le vrai `ttyUSB*` ou
`ttyACM*`, VID/PID, numéro de série, groupe et éventuel processus utilisateur. Il
ne change ni permissions, ni service, ni règle `udev`.

Si plusieurs adaptateurs existent, sélectionner explicitement le lien stable et
résoudre son vrai périphérique :

```bash
export LIDAR_DEVICE="$(readlink -e /dev/serial/by-id/<adaptateur-identifié>)"
test -c "$LIDAR_DEVICE"
export LIDAR_GID="$(stat -Lc '%g' "$LIDAR_DEVICE")"
```

Ne pas utiliser `chmod 777`. `group_add` transmet uniquement le GID du tty au
conteneur. ModemManager est actif sur ce PC : ne pas le désactiver préventivement.
Si `check-lidar.sh` prouve qu'il ouvre durablement ce seul adaptateur, documenter
d'abord VID/PID/numéro de série, puis envisager une règle ciblée
`ID_MM_DEVICE_IGNORE`. Aucun processus ne doit être tué par supposition.

## 3. Premier lancement, sans RViz

Le premier essai réduit le nombre de variables :

```bash
START_RVIZ=false ./scripts/lidar-launch.sh
```

Le script :

1. refuse un port absent, ambigu, inattendu ou déjà occupé ;
2. calcule le GID sur le vrai périphérique ;
3. teste lecture/écriture dans un conteneur éphémère non privilégié ;
4. lance `unitree_lidar_ros2_node` et `l1_monitor` dans le conteneur nommé
   `unitree_l1_runtime`.

La simple présence du nœud ou des publishers n'est pas une réussite : le pilote
fournisseur ignore le retour de `initialize()` et peut rester vivant sans données.

Dans un second terminal, exiger des messages et des fréquences non nulles :

```bash
cd /home/isr/unitree_l1_project
./scripts/lidar-validate.sh
```

La sortie est aussi conservée dans `logs/tests/`. Le verdict
`LIDAR_DATA_VALIDATION_PASS` exige un message PointCloud2, un message Imu, une
mesure de fréquence pour chacun et un message `/diagnostics`.

Si le port s'ouvre mais qu'aucune donnée ne paraît, arrêter proprement avec
`Ctrl-C`. Le pilote ROS 2 fournisseur ne demande pas explicitement le mode
`NORMAL`; vérifier l'état du L1 avant toute adaptation. Une éventuelle correction
devra rester dans le code du projet, vérifier le retour d'initialisation et être
testée/documentée, jamais appliquée silencieusement au vendor figé.

## 4. Visualisation RViz2

Après validation des flux :

```bash
START_RVIZ=true ./scripts/lidar-launch.sh
```

Le profil projet utilise `/unilidar/cloud`, le QoS Reliable/Volatile et le repère
fixe `unilidar_lidar`. Le pilote ne publie aucun TF ; ce repère est donc volontaire
pour la visualisation brute. L'override GUI monte uniquement le cookie X11 en
lecture seule et les périphériques `/dev/dri`, sans `xhost +` ni mode privilégié.

## 5. Enregistrement d'un bag court

Pendant que `lidar-launch.sh` tourne, lancer dans un second terminal :

```bash
BAG_LABEL=validation BAG_DURATION_SEC=30 ./scripts/record-bag.sh
```

Le script refuse de commencer si cloud ou IMU ne délivrent aucun message. Il
enregistre obligatoirement `/unilidar/cloud` et `/unilidar/imu`, puis ajoute
`/diagnostics`, `/tf` et `/tf_static` seulement s'ils existent. L'arrêt borné est
envoyé par `SIGINT` afin que rosbag2 finalise `metadata.yaml`.

Inspection :

```bash
./scripts/bag-info.sh bags/l1_validation_<date_heure>
```

Un bag n'est validé que si ses compteurs cloud et IMU sont strictement positifs.

## 6. Rejeu sans LiDAR

Après avoir arrêté le runtime matériel avec `Ctrl-C` et débranché si souhaité :

```bash
START_RVIZ=true ./scripts/replay-bag.sh bags/l1_validation_<date_heure>
```

Le rejeu démarre le moniteur et RViz dans le même conteneur que `ros2 bag play`.
Comparer types, fréquences, timestamps, frames, champs et nombre de points au test
réel. Le bag de validation court sera conservé séparément du futur parcours de
cartographie.

## 7. Arrêt et reconnexion

- Arrêter le launch et chaque enregistrement avec `Ctrl-C`.
- Vérifier `docker ps` : aucun runtime projet ne doit rester actif.
- Après déconnexion/reconnexion USB, relancer `check-lidar.sh` puis recréer le
  conteneur ; ne pas supposer que `/dev/ttyUSB0` désigne encore le même appareil.
- Inscrire résultats, erreurs, corrections et conditions d'essai dans
  `docs/configuration-log.md` avant de passer à Point-LIO.

Point-LIO ne sera choisi et réglé qu'après validation des messages réels, notamment
les champs PointCloud2, timestamps, unités et extrinsèques LiDAR-IMU.
