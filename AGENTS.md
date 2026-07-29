# Règles durables du projet

1. Travailler depuis `/home/isr/unitree_l1_project`.
2. Expliquer avant chaque commande importante son but, ses effets et ses risques.
3. Journaliser la commande exacte, le résultat utile, les erreurs, la correction
   et la validation dans `docs/configuration-log.md`.
4. Ne jamais inscrire de mot de passe, cookie X11, token ou secret dans les logs.
5. Ne pas installer ROS 2 Humble directement sur l’hôte Ubuntu 24.04.
6. Ne jamais utiliser `chmod 777`, `privileged: true` ou des droits globaux.
7. Ne pas modifier le code sous `ros2_ws/src/unilidar_sdk`; créer une couche projet
   séparée et documenter tout correctif exceptionnel sous forme de patch.
8. Figer les dépôts par commit et les images par digest.
9. Conserver les petits fichiers de configuration dans Git, mais exclure les bags,
   cartes, builds et logs lourds.
10. Un test bloqué par l’absence du LiDAR vaut `BLOCKED_HW`, pas `FAIL`.
11. Ne pas toucher aux conteneurs/images ROS existants hors de ce projet.
12. Mettre à jour la matrice de validation après chaque essai reproductible.
