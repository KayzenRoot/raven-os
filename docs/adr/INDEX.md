# Architecture Decision Records — Index

## Naming convention

- Files: `docs/adr/NNNN-short-kebab-title.md` (zero-padded 4-digit sequence).
- Status values: `Proposed` | `Accepted` | `Superseded` | `Rejected`.
- Create an ADR only for material decisions that are not already frozen externally, or when changing a frozen decision (requires Sol + objective reason).

## Externally frozen context (V0.1)

The V0.1 architecture freeze (product scope, bootc/Fedora 44/Kinoite family, kernel policy, Plasma/Wayland, systemd, D-Bus contracts, Python/uv, CognitiveBackend/Hermes adapter plan, PySide6/QML, SQLite WAL, XDG TOML config, zero-paid-infrastructure, Builder VM authority) is **external frozen context**, not restated as individual ADRs in INC-001.

## ADR log

| ID | Title | Status | Notes |
|----|-------|--------|-------|
| — | *(none yet)* | — | INC-001 made only local tooling choices documented in `pyproject.toml` / REVIEW (Python ≥3.12, ruff, mypy, pytest, uv). |
