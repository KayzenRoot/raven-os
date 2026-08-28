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
tooling migrated; Cirrus OSS activation **blocked** because `KayzenRoot/raven-os` is PRIVATE.

## Completed (Sol-accepted)

| Item | Status |
|------|--------|
| INC-001 / M01–M03 | ACCEPTED (20 points) |

## In progress / blocked

| Item | Status |
|------|--------|
| INC-002 / M04 | **BLOCKED** — Cirrus OSS free requires a public repository |

## Prompt 002D infrastructure change (applied in source)

- ADR-0002: prefer `ghcr.io/osbuild/image-builder` over archived bootc-image-builder
- ADR-0003: Cirrus `docker_builder` is intended primary M04 authority when repo is public
- CircleCI heavy M04 workflow disabled (`when: false`)
- Evidence: [CIRCLECI-M04-BLOCKER.md](CIRCLECI-M04-BLOCKER.md)
- `.cirrus.yml` **not** created (would be a paid path on a private repo)

## Blockers

**BLOCKED - CIRRUS OSS FREE ELIGIBILITY REQUIRES PUBLIC REPOSITORY**

Do not change visibility automatically. Human/Sol next step:

1. Decide whether `KayzenRoot/raven-os` may be made **public**
2. If public: add `.cirrus.yml` (manual + execution lock) and install Cirrus GitHub App
   only for this repo (no payment method)
3. Otherwise: use local Fedora Builder fallback (`just ci-image`)

Source branch remains **M04 BLOCKED**. Progress remains 20%.

## Decisions

- See [ADR-0002](../../adr/0002-migrate-disk-image-builds-to-osbuild-image-builder.md)
- See [ADR-0003](../../adr/0003-use-cirrus-ci-full-vm-as-primary-m04-build-authority.md)
- Base: `quay.io/fedora/fedora-kinoite:44` (no silent fallback)
- QCOW2 rootfs remains **btrfs** (`--bootc-default-fs btrfs`)

## Validation evidence

### Layer A (local)

- `just ci` — includes 002D contracts (CircleCI disabled, image-builder CLI, no `.cirrus.yml`)

### Layer B (real QCOW2 + UEFI boot)

- Not executed in this increment (Cirrus not eligible; CircleCI heavy disabled)

## Next step

Human/Sol: repository visibility decision. Do not trigger CircleCI M04.

## DoD status summary

V0.1 DoD success proof chain: not started (M05–M10). M04: **BLOCKED**.

## Backlog (future versions only)

No new features. V0.2+ remains out of scope.
