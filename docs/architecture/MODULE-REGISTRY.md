# Module Registry — Raven OS V0.1

| ID | Responsibility | Points | Implementation location | Dependencies | Status | Owner / boundary notes |
|----|----------------|-------:|-------------------------|--------------|--------|------------------------|
| M01 | Repository structure + operational documentation | 8 | Root skeleton; `docs/`; `AGENTS.md` | None | ACCEPTED | Sol accepted via INC-001. |
| M02 | Development quality harness + stable commands | 7 | `Justfile`; `pyproject.toml`; ruff/mypy/pytest via uv | M01 | ACCEPTED | Sol accepted via INC-001. |
| M03 | Review ZIP/evidence packaging | 5 | `scripts/create_review.py`; `.review/` output | M01, M02 | ACCEPTED | Sol accepted via INC-001. |
| M04 | Raven bootc base image + QCOW2 build path | 12 | `Containerfile`; `os/`; `scripts/build_*.py`; `.circleci/config.yml` | M01 | BLOCKED | Primary authority: CircleCI Free (ADR-0001); local fallback optional. |
| M05 | ravend core service + D-Bus contract | 12 | Planned: `src/raven_core/`, `systemd/`, `dbus/` | M01, M04 | TODO | User/session service. |
| M06 | CognitiveBackend + configurable provider/Hermes adapter | 12 | Planned: `src/raven_core/`, `src/raven_adapters/` | M05 | TODO | Hermes behind adapter. |
| M07 | SQLite persistence + minimal memory/profile/session state | 10 | Planned: `db/migrations/`, `src/raven_core/` | M05 | TODO | SQLite WAL + explicit migrations. |
| M08 | Safe user-context system tools + correlation/audit | 8 | Planned: `src/raven_core/` | M05, M07 | TODO | Narrow user-context only. |
| M09 | Minimal PySide6/QML Raven UI | 10 | Planned: `src/raven_ui/`, `ui/qml/` | M05, M06 | TODO | PySide6 + QML/Qt Quick. |
| M10 | Integrated VM acceptance flow + reboot persistence proof | 16 | Planned: tests + Builder/VM flow | M04–M09 | TODO | End-to-end V0.1 DoD proof chain. |

**COMPLETED POINTS:** 20 (M01–M03 Sol-accepted). M04 not counted until Sol acceptance after Builder proof.
