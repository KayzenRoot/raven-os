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
| 0001 | [Use CircleCI Free as primary V0.1 cloud build authority](0001-use-circleci-free-as-primary-v0.1-cloud-build-authority.md) | Superseded (M04 disk-image) | Prompt 002C; QCOW2/osbuild authority superseded by ADR-0003 |
| 0002 | [Migrate Raven disk-image builds to current osbuild/image-builder](0002-migrate-disk-image-builds-to-osbuild-image-builder.md) | Accepted | Prompt 002D — archived BIB is not the preferred tool |
| 0003 | [Use Cirrus CI full VM as primary zero-cost M04 build authority](0003-use-cirrus-ci-full-vm-as-primary-m04-build-authority.md) | Accepted (activation blocked) | Requires public repo for Cirrus OSS free; no `.cirrus.yml` while private |
