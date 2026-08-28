# Raven OS V0.1 — Checkpoint

- **STATUS:** IN PROGRESS
- **VERSION:** V0.1
- **PHASE:** Image Foundation (M04) — Layer B passed on GHA; awaiting Sol audit
- **OBJECTIVE:** Deliver a small VM Cognitive Seed (local-first cognitive Linux OS seed), not the full long-term product.
- **VERSION PROGRESS:** 20% (20/100 Sol-accepted points; M04 Layer B proven, not Sol-accepted)
- **COMPLETED POINTS:** 20

## Sol state transition (INC-001)

Per Prompt 002 instruction from Sol (not executor self-acceptance):

- M01, M02, M03 = **ACCEPTED**
- INC-001 = **ACCEPTED**
- COMPLETED POINTS = **20**
- VERSION PROGRESS = **20%**

## Current scope

INC-002 / Prompt 002E-R2 — boot-smoke harness hardened; **Layer B passed** on GitHub Actions
run `33200940474` (`b6acd45`). M04 may be marked **REVIEW** by Sol only after REVIEW ZIP audit.
Executor does **not** mark ACCEPTED. Points remain 20 / 20%.

## Completed (Sol-accepted)

| Item | Status |
|------|--------|
| INC-001 / M01–M03 | ACCEPTED (20 points) |

## In progress / blocked

| Item | Status |
|------|--------|
| INC-002 / M04 | **REVIEW candidate** — Layer B passed GHA `33200940474`; awaiting Sol audit |

## Prompt 002E-R2 harness changes (applied in source)

- QCOW2 static preboot (`qemu-img info/check`, owner/mode evidence)
- UEFI/OVMF preboot with paired CODE/VARS validation
- QEMU `-snapshot` + explicit virtio-blk boot disk (base QCOW2 immutable)
- Popen-based observable process control; launch error vs boot timeout classification
- Guest-level serial markers required (EFI-only fails)
- Serial console kargs via `os/image-builder-config.toml` mounted at `/config.toml`
- Failure diagnostics ZIP (`raven-m04-diagnostics` artifact on GHA failure)
- CLI timeout contract fixed (omit → 300s cloud / 120s local)
- Preflight pull retry (3×, 5s) after transient pull failure on run 1

## GitHub M04 attempt history on `main`

| Run | SHA | Result | Notes |
|-----|-----|--------|-------|
| `33191087333` | `ce093ec`/`f462879` | FAIL (~2m) | `builder-preflight` / podman path |
| `33191467126` | `f462879` | FAIL (~11m) | `image-check` — conmon journald log driver |
| `33192739565` | `0e3d57e` | FAIL (~11m) | `image-check` — same conmon/journald error |
| `33193783890` | `1f603e8` (002E-R1 #1) | FAIL (~18m) | `boot-smoke` — no serial markers (KVM) |
| `33195816360` | `d2439ab` (002E-R1 #2) | FAIL (~0.14s) | `boot-smoke` — TCG immediate exit; old harness |
| `33200468426` | `3e127c6` (002E-R2 #1) | FAIL (~1m) | `builder-preflight` — transient base image pull |
| `33200940474` | `b6acd45` (002E-R2 #2) | **PASS** (~18m) | All gates including `boot-smoke`; REVIEW ZIP produced |

Run `33200940474` facts:

- `just ci` PASS (94 tests)
- All cloud gates PASS through `boot-smoke`
- Acceleration: TCG (cloud-forced)
- `run-m04-cloud: PASS_REVIEW_READY`
- REVIEW ZIP: `RAVEN-OS-V0.1-INC-002-REVIEW.zip` (SHA-256 `5e2ba24164ba47db01bbfa86ffb388d722445a64ad3fa6240ce3ddbcf3c1a82`)

002E-R2 heavy retry budget **exhausted (2/2)**. Do not trigger another GHA M04 run. Do not start M05.

## Next step

Sol: audit REVIEW ZIP from run `33200940474` and evidence in `.build/evidence/` (from GHA logs).
If accepted, mark M04 **ACCEPTED** (+12 points → 32 / 32%).

## Decisions

- See [ADR-0002](../../adr/0002-migrate-disk-image-builds-to-osbuild-image-builder.md)
- See [ADR-0004](../../adr/0004-use-public-github-standard-runner-as-m04-build-authority.md)
- Base: `quay.io/fedora/fedora-kinoite:44` (no silent fallback)
- QCOW2 rootfs remains **btrfs** (`--bootc-default-fs btrfs`)

## Validation evidence

### Layer A (local)

- `just ci` — 94 tests PASS

### Layer B (real QCOW2 + UEFI boot)

- GHA run `33200940474` (`b6acd45`): all gates PASS including `boot-smoke`
- REVIEW ZIP downloaded locally under `.review/`

## DoD status summary

V0.1 DoD success proof chain: not started (M05–M10). M04: **REVIEW candidate** (Sol audit pending).

## Backlog (future versions only)

No new features. V0.2+ remains out of scope.
