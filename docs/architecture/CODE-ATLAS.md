# Code Atlas — Raven OS V0.1

Compact map of repository areas. Distinguishes **present** from **planned**.

## Root

| Path | Status | Responsibility |
|------|--------|----------------|
| `AGENTS.md` | Present | Concise executor/Sol instructions |
| `Justfile` | Present | Quality facade + M04 image build commands |
| `pyproject.toml` / `uv.lock` | Present | Python project + locked dev deps |
| `.gitignore` | Present | Caches, secrets, review/build artifacts |
| `Containerfile` | Present (M04) | Raven bootc OCI derivative from Fedora Kinoite 44 |

## Image foundation (`os/` + build scripts)

| Path | Status | Responsibility |
|------|--------|----------------|
| `os/image-source.toml` | Present | Machine-readable base/tooling manifest |
| `scripts/raven_build_config.py` | Present | Build paths, manifest load, guards |
| `scripts/builder_preflight.py` | Present | Layer B capability diagnostics |
| `scripts/build_image.py` | Present | Podman OCI build |
| `scripts/build_qcow2.py` | Present | osbuild/image-builder QCOW2 path (ADR-0002) |
| `scripts/image_builder_cli.py` | Present | Current image-builder CLI args |
| `scripts/image_check.py` | Present | OCI inspection / Raven labels |
| `scripts/artifact_metadata.py` | Present | SHA-256 provenance metadata |
| `scripts/boot_smoke.py` | Present | Bounded UEFI QEMU boot smoke (KVM or TCG) |
| `scripts/boot_smoke_qemu.py` | Present | UEFI QEMU command builder (testable) |
| `scripts/run_m04_cloud.py` | Present | Ordered M04 gates + REVIEW ZIP (GitHub Actions/local; not CircleCI-triggered) |
| `scripts/github_actions_bootstrap.sh` | Present | GitHub Actions runner package/tool install + disk policy |
| `scripts/cirrus_bootstrap.sh` | Present | Historical Cirrus helper (retired operational path) |
| `.github/workflows/m04.yml` | Present | Manual M04 validation on standard public `ubuntu-24.04` runner |
| `.circleci/config.yml` | Present | Heavy M04 workflow **disabled** (`when: false`) |
| `.build/` | Generated (ignored) | `images/`, `qcow2/`, `evidence/`, Podman graphroot |

## Source packages (`src/`)

| Path | Status | Boundary |
|------|--------|----------|
| `src/raven_core/` | Skeleton | Core services (M05+) |
| `src/raven_ui/` | Skeleton | PySide6/QML UI boundary (M09) |
| `src/raven_adapters/` | Skeleton | External adapters (M06) |

## Planned integration trees

| Path | Status | Notes |
|------|--------|-------|
| `ui/qml/` | Planned placeholder | QML sources for M09 |
| `db/migrations/` | Planned placeholder | SQLite migrations for M07 |
| `systemd/` | Planned placeholder | Unit files for ravend (M05+) |
| `dbus/` | Planned placeholder | Raven D-Bus contracts (M05) |

## Tooling

| Path | Status | Responsibility |
|------|--------|----------------|
| `scripts/create_review.py` | Present | Cross-platform review ZIP generator |
| `tests/` | Present | Bootstrap, review, M04 contract tests |

## Docs

| Path | Status |
|------|--------|
| `docs/INDEX.md` | Present |
| `docs/architecture/*` | Present |
| `docs/adr/INDEX.md` | Present |
| `docs/versions/v0.1/*` | Present |

## Ownership summary

- **Executor:** implements INC-* under frozen architecture; produces review evidence.
- **Sol:** architecture freeze, ADR acceptance, module ACCEPTED, version completion.
- **Builder authority:** Cirrus CI Community Cluster full VM (ADR-0003); local Fedora Server 44 Builder VM (fallback). CircleCI is not M04 disk-image authority.
