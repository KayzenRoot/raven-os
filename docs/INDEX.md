# Raven OS — Documentation Index

Operational and architecture docs for Raven OS V0.1 (VM Cognitive Seed).

## Versions

| Path | Purpose |
|------|---------|
| [versions/v0.1/FLUXO.md](versions/v0.1/FLUXO.md) | Frozen V0.1 module weights and increment queue |
| [versions/v0.1/CHECKPOINT.md](versions/v0.1/CHECKPOINT.md) | Current phase, progress, blockers, next step |
| [versions/v0.1/DEFINITION-OF-DONE.md](versions/v0.1/DEFINITION-OF-DONE.md) | V0.1 closure gates and success proof |
| [versions/v0.1/BUILDER-SETUP.md](versions/v0.1/BUILDER-SETUP.md) | Raven Builder VM setup and Layer B gate sequence |
| [versions/v0.1/CIRCLECI-OPERATOR.md](versions/v0.1/CIRCLECI-OPERATOR.md) | CircleCI CLI auth, validate, trigger, and monitor (developer-only) |

## Architecture maps

| Path | Purpose |
|------|---------|
| [architecture/CODE-ATLAS.md](architecture/CODE-ATLAS.md) | Repository areas, ownership, V0.1 boundaries |
| [architecture/MODULE-REGISTRY.md](architecture/MODULE-REGISTRY.md) | M01–M10 registry |
| [architecture/TEST-MAP.md](architecture/TEST-MAP.md) | Proof categories and automated tests |
| [adr/INDEX.md](adr/INDEX.md) | ADR convention; ADR-0001 CircleCI primary builder |

## Image source manifest

- [../os/image-source.toml](../os/image-source.toml) — Fedora/Kinoite base reference, digest pin state, QCOW2 rootfs, bootc-image-builder policy

## Root agent guidance

- [AGENTS.md](../AGENTS.md) — concise executor/Sol operating rules

## Command facade

Canonical facade: `just` (see root `Justfile`).

| Command | Underlying (when `just` is unavailable) |
|---------|------------------------------------------|
| `just test` | `uv run pytest -q` |
| `just lint` | `uv run ruff check .` |
| `just format-check` | `uv run ruff format --check .` |
| `just typecheck` | `uv run mypy src scripts tests` |
| `just ci` | test + lint + format-check + typecheck (fast; no image downloads) |
| `just builder-preflight` | `uv run python -m scripts.builder_preflight` |
| `just build-image` | `uv run python -m scripts.build_image` |
| `just image-check` | `uv run python -m scripts.image_check` |
| `just build-qcow2` | `uv run python -m scripts.build_qcow2` |
| `just artifact-metadata` | `uv run python -m scripts.artifact_metadata` |
| `just boot-smoke` | `uv run python -m scripts.boot_smoke` |
| `just ci-image` | builder-preflight → build-image → image-check → build-qcow2 → artifact-metadata → boot-smoke |
| `just run-m04-cloud` | `uv run python -m scripts.run_m04_cloud` |
| `just circleci-validate` | `circleci config validate` |
| `just review` | `uv run python scripts/create_review.py --increment INC-002` |
| `just format` | `uv run ruff format .` |

All checks run locally. No GitHub Actions or paid CI required. Real image gates require the Raven Builder VM.
