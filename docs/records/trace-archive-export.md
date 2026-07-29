# Export des traces avant matériel

- Date : 15 juillet 2026.
- Archive : `unitree_l1_traces_pre_materiel_20260715.zip`.
- Taille : 2 592 472 octets.
- Nombre de fichiers : 78.
- Commit du snapshot : `3a73506f85da3cf74c43392f7235b1eb7fb03b78`.
- SHA-256 du ZIP :
  `7a317fa5add7d189bd2d210345631048a1da32ad8d309e5ab1115145dda8d682`.

## Contrôles réussis

1. `sha256sum -c` sur le sidecar externe.
2. `unzip -tq` sur la totalité de l'archive.
3. Extraction dans un dossier temporaire.
4. `sha256sum -c SHA256SUMS.txt` sur chaque fichier interne manifesté.
5. Contrôle PDF : 3 pages A4 et texte attendu extractible.
6. Comparaison binaire entre le PDF racine et sa copie dans le snapshot.
7. `git bundle verify` depuis le dépôt projet.
8. Clone du bundle puis vérification du commit HEAD exact.

Verdict : `ARCHIVE_DEEP_VALIDATION_PASS`, 78 fichiers et 2 845 519 octets après
extraction. Les erreurs de harnais et leurs corrections sont détaillées sous
`ERR-20260715-016` dans le journal principal.

## Vérification après téléchargement

Placer le ZIP et le fichier `.zip.sha256` dans le même dossier, puis exécuter :

```bash
sha256sum -c unitree_l1_traces_pre_materiel_20260715.zip.sha256
unzip -t unitree_l1_traces_pre_materiel_20260715.zip
```
