# Architecture Decision Records — Index

## Naming convention

- Files: `docs/adr/NNNN-short-kebab-title.md` (zero-padded 4-digit sequence).
- Status values: `Proposed` | `Accepted` | `Superseded` | `Rejected`.
- Create an ADR only for material decisions that are not already frozen externally, or when changing a frozen decision (requires Sol + objective reason).

## Externally frozen context (V0.1)

The V0.1 architecture freeze (product scope, bootc/Fedora 44/Kinoite family, kernel policy, Plasma/Wayland, systemd, D-Bus contracts, Python/uv, CognitiveBackend/Hermes adapter plan, PySide6/QML, SQLite WAL, XDG TOML config, zero-paid-infrastructure) is **external frozen context**.

ADR-0001 supersedes **only** the mandatory-local-VM Builder authority for the current M04 phase.

## ADR log

| ID | Title | Status | Notes |
|----|-------|--------|-------|
| 0001 | [Use CircleCI Free as primary V0.1 cloud build authority](0001-use-circleci-free-as-primary-v0.1-cloud-build-authority.md) | Accepted | Prompt 002C — primary cloud Builder; local Fedora Builder fallback |
