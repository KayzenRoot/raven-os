# Raven OS V0.1 — Checkpoint

- **STATUS:** IN PROGRESS
- **VERSION:** V0.1
- **PHASE:** Image Foundation (M04) — Prompt 002E-R1 k8s-file fix applied; boot-smoke TCG follow-up
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

INC-002 / Prompt 002E — Cirrus operational path retired (network cannot reach
`cirrus-ci.com` without VPN). M04 build authority moved to **GitHub Actions**
standard public `ubuntu-24.04` runner (`workflow_dispatch` + `confirm_m04=true`).
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
| INC-002 / M04 | **BLOCKED** — GitHub Actions workflow added; Layer B (QCOW2 + boot) not yet proven |

## Prompt 002E infrastructure change (applied in source)

- ADR-0004: public GitHub standard runner as primary M04 authority
- ADR-0003: superseded for M04 (Cirrus evaluated and retired)
- `.cirrus.yml` removed; Cirrus is not an operational M04 dependency
- `.github/workflows/m04.yml`: manual M04 validation (`confirm_m04`, public repo gate)
- `scripts/github_actions_bootstrap.sh`: runner bootstrap + disk policy
- CircleCI heavy M04 workflow remains disabled (`when: false`)
- Operator: [GITHUB-ACTIONS-OPERATOR.md](GITHUB-ACTIONS-OPERATOR.md)

## Blockers

M04 Layer B (real QCOW2 + UEFI boot smoke) has not yet passed on GitHub Actions.
GitHub M04 attempt history on `main`:

| Run | SHA | Result | Failed step |
|-----|-----|--------|-------------|
| `33191087333` | `ce093ec`/`f462879` | FAIL (~2m) | `builder-preflight` / podman path |
| `33191467126` | `f462879` | FAIL (~11m) | `image-check` — conmon journald log driver |
| `33192739565` | `0e3d57e` (crun only) | FAIL (~11m) | `image-check` — same conmon/journald error |
| `33193783890` | `1f603e8` (002E-R1) | FAIL (~18m) | `boot-smoke` — UEFI serial markers not observed |

Run `33193783890` (`1f603e8`, 002E-R1 `k8s-file`) cleared `image-check`; failed
`boot-smoke` in 0.12s (KVM selected despite unusable nested virt on GHA). Follow-up:
force TCG acceleration on cloud builder + 300s boot-smoke timeout.
CircleCI heavy M04 stays disabled. Do not start M05.

## Next step

Executor: trigger M04 Run 2 after boot-smoke TCG push (`gh workflow run m04.yml
--ref main -f confirm_m04=true`). M04 stays **BLOCKED** until Layer B passes and
Sol audits the REVIEW ZIP.

## Decisions

- See [ADR-0002](../../adr/0002-migrate-disk-image-builds-to-osbuild-image-builder.md)
- See [ADR-0004](../../adr/0004-use-public-github-standard-runner-as-m04-build-authority.md)
- Base: `quay.io/fedora/fedora-kinoite:44` (no silent fallback)
- QCOW2 rootfs remains **btrfs** (`--bootc-default-fs btrfs`)

## Validation evidence

### Layer A (local)

- `just ci` — includes 002E contracts (GitHub Actions workflow, Cirrus retired, CircleCI disabled)

### Layer B (real QCOW2 + UEFI boot)

- GHA run `33193783890` (`1f603e8`): `image-check` passed; `boot-smoke` failed
  (UEFI serial markers not observed). Layer B not yet proven.
- Attempt 4 `boot-smoke` evidence (from GHA log + `scripts/boot_smoke.py`):
  - Serial log path: `.build/evidence/boot-smoke-serial.log`
  - Expected markers (any one): `Fedora`, `systemd`, `Linux version`, `Kinoite`, `EFI`
  - Observed markers: **none** (exit 1 after 120s bounded QEMU run)
  - QEMU/OVMF: `q35` + OVMF pflash code/vars + virtio QCOW2 + `-serial file:` +
    `-display none` + `-no-reboot`; acceleration `tcg` on GHA (no `/dev/kvm`)
  - No run artifacts uploaded (failed before REVIEW ZIP)

## DoD status summary

V0.1 DoD success proof chain: not started (M05–M10). M04: **BLOCKED**.

## Backlog (future versions only)

No new features. V0.2+ remains out of scope.
