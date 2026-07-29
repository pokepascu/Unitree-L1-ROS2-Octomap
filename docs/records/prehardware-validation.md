# Jalon de validation avant matériel — 15 juillet 2026

## Portée

Ce jalon prouve l'environnement Docker Jammy/Humble, la compilation et l'ABI du
pilote, le launch configurable, le moniteur, X11/DRI et RViz2. Il ne prouve aucune
donnée Unitree : aucun port série L1 n'était présent.

## Résultats figés

| Contrôle | Résultat | Code |
|---|---|---:|
| Build image `unitree-l1:humble-v1.0.16` | image ID `sha256:60dfcef…` | 0 |
| Build initial pilote + bringup | 2 paquets, 21,0 s | 0 |
| Build final pilote + monitor + bringup | 3 paquets, 2,84 s | 0 |
| Smoke test ROS/launch/ldd | `SMOKE_TEST_PASS` | 0 |
| Tests projet | 8 réussis, 0 échec | 0 |
| Linters Python ROS 2 | flake8/pep257, 13 fichiers, aucun problème | 0 |
| Moniteur sans données | 2 statuts ERROR attendus | 0 |
| Moniteur avec données synthétiques | cloud ~10 Hz, IMU ~30 Hz, 2 statuts OK | 0 |
| X11/DRI | rendu direct Intel, OpenGL 4.6 | 0 |
| RViz2 réel | vivant 8 s, arrêt SIGINT | 124 attendu |
| Pilote sur port absent | nœud vivant, zéro message | 124 attendu |
| Script matériel sans port | refus avant Docker | 2 attendu |

## Hashes

- PDF d'entrée :
  `848185726cf4899efac63df62cfdef21985ec3b042eec9e52ae26113b5b84661`.
- Manuel Unitree officiel :
  `4d816cdf6197a51c5e87e6e7876da822b2d0e52e0bf63df306b40ac32fb13a74`.
- Archive SDK Unitree x86_64 :
  `295efc9d55192483c66be291fe74ba0c3795c049c5e5286f650c6e7cf2d79cdf`.
- Binaire Unitree Humble :
  `c7ed1cf9d632bb7cf04b95018a0395819578816fc81a821ac241e3278cbb61b0`.
- Log build initial :
  `6f54f2197b21c352d535eefd9bd1954b5d79f75afb014049c0dc56b9c0eab2b6`.
- Log build final :
  `127859e73be1e24af7886efaccfac6a274000f7d0877bc3c1dc7c6c176d8b014`.
- Log tests :
  `30355dad29b2912bfedb59f7a3e330dede7ad19002f9edc847332316e218172c`.
- Log résultat tests :
  `66d6208d839956313fd9decb8031f46f18e2f6671f3ff9ecdd743a3ffa6f566a`.

## Interprétation

La compatibilité de compilation Humble/PCL 1.12 est démontrée sans modification
du vendor. Le binaire associe une archive GCC 9.4 à un runtime GCC 11.4 dont la
version GLIBCXX couvre les symboles requis. La qualité des points, l'IMU et les
performances restent à mesurer physiquement.

Un processus Unitree vivant n'est pas une preuve : le retour d'initialisation
série est ignoré. Le prochain verdict nécessite donc un message cloud, un message
IMU et des fréquences non nulles obtenus par `lidar-validate.sh`.

## Référence Git

Le contenu logiciel et les preuves de ce jalon ont été figés dans le commit local
`a844ba737bc8775bff97ea2263adfc2a26ee3c71`. Le commit documentaire suivant ajoute
uniquement cette référence au journal ; aucun dépôt distant n'a été configuré.
