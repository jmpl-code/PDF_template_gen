# Deferred Work

## Deferred from: code review of stories 1-1 & 1-2 (2026-04-06)

- **Timeout subprocess** — `run_external()` n'a pas de `timeout=`. A ajouter quand les renderers Typst/Pandoc seront implementes (Story 2.3+).
- **matplotlib/pydantic/pyyaml non utilises** — Dependances planifiees pour les stories suivantes (2.1, 2.7, etc.).
- **Zero appels logging** — Pas de logique a logger dans la phase scaffolding. A ajouter des Story 2.1.
- **Validation path CLI build** — cli.py est un placeholder, sera remplace en Story 2.9.
- **Encodage Unicode stderr Windows** — `text=True` utilise l'encodage locale. A considerer lors de l'implementation des renderers.
