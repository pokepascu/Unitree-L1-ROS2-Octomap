#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export_dir="${project_root}/exports"
archive_name="unitree_l1_traces_pre_materiel_20260715"
zip_path="${export_dir}/${archive_name}.zip"
commit="${1:-HEAD}"
commit="$(git -C "${project_root}" rev-parse --verify "${commit}^{commit}")"
staging_parent="$(mktemp -d)"
archive_root="${staging_parent}/${archive_name}"
trap 'rm -rf "${staging_parent}"' EXIT

command -v git >/dev/null
command -v zip >/dev/null
command -v unzip >/dev/null
command -v sha256sum >/dev/null

mkdir -p "${export_dir}" "${archive_root}/git"
git -C "${project_root}" archive --format=tar \
  --prefix="${archive_name}/projet/" "${commit}" | tar -xf - -C "${staging_parent}"
git -C "${project_root}" bundle create \
  "${archive_root}/git/unitree_l1_project.bundle" --all
git -C "${project_root}" bundle verify \
  "${archive_root}/git/unitree_l1_project.bundle" >/dev/null

cp "${archive_root}/projet/docs/report/pdf/00_preparation/SYNTHESE_UNITREE_L1_PRE_MATERIEL.pdf" \
  "${archive_root}/SYNTHESE_PREPARATION_UNITREE_L1.pdf"

printf '%s\n' \
  'ARCHIVE DE TRAÇABILITÉ — UNITREE 4D LIDAR L1' \
  '' \
  'État : jalon logiciel avant branchement du LiDAR.' \
  "Commit archivé : ${commit}" \
  'Date : 15 juillet 2026.' \
  '' \
  'Lecture rapide :' \
  '  1. SYNTHESE_PREPARATION_UNITREE_L1.pdf' \
  '  2. projet/README.md' \
  '  3. projet/docs/configuration-log.md' \
  '  4. projet/docs/hardware-runbook.md' \
  '' \
  'Le dossier projet/ contient tous les documents, sources, configurations,' \
  'scripts et journaux bruts suivis par Git à ce commit.' \
  '' \
  'Le bundle git/unitree_l1_project.bundle conserve l’historique complet.' \
  'Restauration : git clone git/unitree_l1_project.bundle projet_restaure' \
  '' \
  'Exclusions volontaires :' \
  '  - image Docker et répertoires ROS générés build/install/log ;' \
  '  - SDK fournisseur, recréable par projet/scripts/fetch-dependencies.sh ;' \
  '  - bags et cartes, encore absents avant le test matériel ;' \
  '  - secrets et cookie X11.' \
  '' \
  'Le PDF d’entrée conserve la métadonnée auteur Pascual. Vérifier ce point' \
  'avant une éventuelle diffusion publique de cette archive privée.' \
  > "${archive_root}/LIRE_EN_PREMIER.txt"

git -C "${project_root}" show -s \
  --format='commit=%H%nsubject=%s%nauthor=%an <%ae>%ndate=%aI' "${commit}" \
  > "${archive_root}/COMMIT_ARCHIVE.txt"

(
  cd "${archive_root}"
  find . -type f ! -name SHA256SUMS.txt -print0 | sort -z | \
    xargs -0 sha256sum > SHA256SUMS.txt
  find . -type f -printf '%P\n' | sort > INDEX_FICHIERS.txt
)

rm -f "${zip_path}" "${zip_path}.sha256"
(
  cd "${staging_parent}"
  zip -X -q -r "${zip_path}" "${archive_name}"
)
unzip -tq "${zip_path}" >/dev/null
(
  cd "${export_dir}"
  sha256sum "$(basename "${zip_path}")" > "$(basename "${zip_path}").sha256"
)

printf 'TRACE_ARCHIVE_PASS file=%s bytes=%s files=%s sha256=%s commit=%s\n' \
  "${zip_path}" \
  "$(stat -c '%s' "${zip_path}")" \
  "$(unzip -Z1 "${zip_path}" | grep -vc '/$')" \
  "$(sha256sum "${zip_path}" | awk '{print $1}')" \
  "${commit}"
