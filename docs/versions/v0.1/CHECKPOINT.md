# Raven OS V0.1 — Checkpoint

- **STATUS:** IN PROGRESS
- **VERSION:** V0.1
- **PHASE:** Image Foundation (M04) — Prompt 002E-R2 boot-smoke harness hardening
- **OBJECTIVE:** Deliver a small VM Cognitive Seed (local-first cognitive Linux OS seed), not the full long-term product.
- **VERSION PROGRESS:** 20% (20/100 Sol-accepted points; M04 pending real Builder Layer B)
- **COMPLETED POINTS:** 20

## Sol state transition (INC-001)

Per Prompt 002 instruction from Sol (not executor self-acceptance):

- M01, M02, M03 = **ACCEPTED**
- INC-001 = **ACCEPTED**
- COMPLETED POINTS = **20**
- VERSION PROGRESS = **20%**

## Current scope

INC-002 / Prompt 002E-R2 — boot-smoke harness comprehensively hardened before new
heavy GHA attempts. M04 build authority remains **GitHub Actions** standard public
`ubuntu-24.04` runner (`workflow_dispatch` + `confirm_m04=true`).
Repository `KayzenRoot/raven-os` is **PUBLIC**. M04 remains **BLOCKED** until a
real QCOW2 + UEFI boot passes on GitHub Actions and Sol audits the REVIEW ZIP.
Points stay 20 / 20%.

## Completed (Sol-accepted)

| Item | Status |
|------|--------|
| INC-001 / M01–M03 | ACCEPTED (20 points) |

## In progress / blocked

| Item | Status |
|------|--------|
| INC-002 / M04 | **BLOCKED** — harness hardened (002E-R2); Layer B boot-smoke not yet proven on GHA |

## Prompt 002E-R2 harness changes (applied in source)

- QCOW2 static preboot (`qemu-img info/check`, owner/mode evidence)
- UEFI/OVMF preboot with paired CODE/VARS validation
- QEMU `-snapshot` + explicit virtio-blk boot disk (base QCOW2 immutable)
- Popen-based observable process control; launch error vs boot timeout classification
- Guest-level serial markers required (EFI-only fails)
- Serial console kargs via `os/image-builder-config.toml` mounted at `/config.toml`
- Failure diagnostics ZIP (`raven-m04-diagnostics` artifact on GHA failure)
- CLI timeout contract fixed (omit → 300s cloud / 120s local)
- Operator: [GITHUB-ACTIONS-OPERATOR.md](GITHUB-ACTIONS-OPERATOR.md)

## Blockers

M04 Layer B (real QCOW2 + UEFI boot smoke) has not yet passed on GitHub Actions
after 002E-R2 harness fix. Prior attempt history on `main`:

| Run | SHA | Result | Failed step |
|-----|-----|--------|-------------|
| `33191087333` | `ce093ec`/`f462879` | FAIL (~2m) | `builder-preflight` / podman path |
| `33191467126` | `f462879` | FAIL (~11m) | `image-check` — conmon journald log driver |
| `33192739565` | `0e3d57e` (crun only) | FAIL (~11m) | `image-check` — same conmon/journald error |
| `33193783890` | `1f603e8` (002E-R1 #1) | FAIL (~18m) | `boot-smoke` — no serial markers (KVM) |
| `33200468426` | `3e127c6` (002E-R2 #1) | FAIL (~1m) | `builder-preflight` — transient base image pull |

Run `33195816360` facts (verified via `gh run view --log-failed`):

- GitHub runner exposed `/dev/kvm` during bootstrap
- Raven intentionally forced TCG for cloud (`RAVEN_CLOUD_BUILDER=1`)
- `builder-preflight` reported acceleration `tcg`
- All gates through `artifact-metadata` passed; `boot-smoke` failed in ~0.14s
- Old harness misclassified immediate QEMU exit as "serial markers not observed"
- Root cause class: QEMU launch failure (likely disk permission / missing snapshot), not guest boot timeout

Prompt 002E-R1 retry budget **exhausted (2/2)**. Prompt 002E-R2 authorizes **2 NEW**
heavy attempts (run 1 `33200468426` blocked at preflight pull; pull retry added for run 2).
Do not start M05.

## Next step

Executor: trigger GHA M04 run 1 with 002E-R2 harness; monitor; on failure download
`raven-m04-diagnostics` and apply at most one evidence-backed correction before run 2.
Sol: audit REVIEW ZIP on full pass; M04 may become **REVIEW** only after Layer B passes.

## Decisions

- See [ADR-0002](../../adr/0002-migrate-disk-image-builds-to-osbuild-image-builder.md)
- See [ADR-0004](../../adr/0004-use-public-github-standard-runner-as-m04-build-authority.md)
- Base: `quay.io/fedora/fedora-kinoite:44` (no silent fallback)
- QCOW2 rootfs remains **btrfs** (`--bootc-default-fs btrfs`)

## Validation evidence

### Layer A (local)

- `just ci` — 94 tests PASS (002E-R2 boot-smoke hardening contracts)

### Layer B (real QCOW2 + UEFI boot)

- Pending 002E-R2 GHA run(s) after harness push
- No REVIEW ZIP yet (Layer B not proven)

## DoD status summary

V0.1 DoD success proof chain: not started (M05–M10). M04: **BLOCKED**.

## Backlog (future versions only)

No new features. V0.2+ remains out of scope.
