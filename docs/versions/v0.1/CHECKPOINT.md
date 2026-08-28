# Raven OS V0.1 — Checkpoint

- **STATUS:** IN PROGRESS
- **VERSION:** V0.1
- **PHASE:** Image Foundation (M04) — Prompt 002D Cirrus/image-builder migration
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

INC-002 / Prompt 002D — CircleCI rejected as M04 disk-image authority; image-builder
tooling migrated; Cirrus `.cirrus.yml` added after `KayzenRoot/raven-os` became
**PUBLIC**. GitHub App **Cirrus CI** is installed for this repository only
(installation id `157274806`; installed after `c8d5189`, so that SHA has no
Cirrus check-runs). M04 remains **BLOCKED** until a real QCOW2 + UEFI boot
passes on cloud Cirrus and Sol audits the REVIEW ZIP. Points stay 20 / 20%.

## Completed (Sol-accepted)

| Item | Status |
|------|--------|
| INC-001 / M01–M03 | ACCEPTED (20 points) |

## In progress / blocked

| Item | Status |
|------|--------|
| INC-002 / M04 | **BLOCKED** — Cirrus App installed; Layer B (QCOW2 + boot) not yet proven |

## Prompt 002D infrastructure change (applied in source)

- ADR-0002: prefer `ghcr.io/osbuild/image-builder` over archived bootc-image-builder
- ADR-0003: Cirrus Community Cluster full VM is primary M04 authority (public repo)
- CircleCI heavy M04 workflow disabled (`when: false`)
- Evidence: [CIRCLECI-M04-BLOCKER.md](CIRCLECI-M04-BLOCKER.md)
- `.cirrus.yml`: manual `m04-cirrus-builder` + execution lock; REVIEW ZIP only
- Operator: [CIRRUS-OPERATOR.md](CIRRUS-OPERATOR.md)
- GitHub App Cirrus CI authorized for `KayzenRoot/raven-os` only (id `157274806`)

## Blockers

M04 Layer B (real QCOW2 + UEFI boot smoke) has not yet passed on Cirrus.
CircleCI heavy M04 stays disabled. Do not start M05.

## Decisions

- See [ADR-0002](../../adr/0002-migrate-disk-image-builds-to-osbuild-image-builder.md)
- See [ADR-0003](../../adr/0003-use-cirrus-ci-full-vm-as-primary-m04-build-authority.md)
- Base: `quay.io/fedora/fedora-kinoite:44` (no silent fallback)
- QCOW2 rootfs remains **btrfs** (`--bootc-default-fs btrfs`)

## Validation evidence

### Layer A (local)

- `just ci` — includes 002D contracts (CircleCI disabled, Cirrus manual, image-builder CLI)

### Layer B (real QCOW2 + UEFI boot)

- Not yet proven on Cirrus in this increment

## Next step

Trigger **one** manual `m04-cirrus-builder` (Cirrus App already installed).
Do not trigger CircleCI M04. Do not start M05. M04 stays **BLOCKED** until
Layer B evidence exists.

## DoD status summary

V0.1 DoD success proof chain: not started (M05–M10). M04: **BLOCKED**.

## Backlog (future versions only)

No new features. V0.2+ remains out of scope.
