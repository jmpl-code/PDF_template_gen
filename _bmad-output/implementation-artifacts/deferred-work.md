# Deferred Work

## Deferred from: code review of stories 1-1 & 1-2 (2026-04-06)

- **Timeout subprocess** — `run_external()` n'a pas de `timeout=`. A ajouter quand les renderers Typst/Pandoc seront implementes (Story 2.3+).
- **matplotlib/pydantic/pyyaml non utilises** — Dependances planifiees pour les stories suivantes (2.1, 2.7, etc.).
- **Zero appels logging** — Pas de logique a logger dans la phase scaffolding. A ajouter des Story 2.1.
- **Validation path CLI build** — cli.py est un placeholder, sera remplace en Story 2.9.
- **Encodage Unicode stderr Windows** — `text=True` utilise l'encodage locale. A considerer lors de l'implementation des renderers.

## Deferred from: code review of story 2-9 (2026-04-07)

- **organize_output non-atomique** — `shutil.copy2` séquentiel dans export.py peut laisser un dossier de sortie incohérent si copie échoue à mi-parcours. Pre-existing depuis Story 2.8.
- **Path traversal via chap_config.fichier** — `load_book_config` valide l'existence du fichier chapitre mais ne vérifie pas qu'il reste dans book_root. Un chemin `../../etc/passwd` serait accepté. Pre-existing depuis Story 2.1.
- **Artefacts intermédiaires dans book_root** — Le pipeline rend les .typ et .pdf dans book_root (nécessaire pour la résolution relative des images). Ces fichiers polluent le répertoire source. Accepté pour MVP0.
