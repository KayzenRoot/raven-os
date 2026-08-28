# Raven OS V0.1 — Checkpoint

- **STATUS:** IN PROGRESS
- **VERSION:** V0.1
- **PHASE:** Image Foundation (M04) — Prompt 002E GitHub Actions public M04 builder
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
Attempt 2 reached `image-check` then failed with Podman `conmon` runtime error on the
standard runner. Retry budget for Prompt 002E is exhausted (2/2). A `crun` runtime fix
is committed for Sol follow-up. CircleCI heavy M04 stays disabled. Do not start M05.

## Next step

Sol follow-up: re-trigger M04 after reviewing the `crun` runtime fix
(`gh workflow run m04.yml --ref main -f confirm_m04=true`). Attempts 1–2 failed
(preflight/podman path, then `image-check` conmon). M04 stays **BLOCKED** until Layer B
evidence exists and Sol audits the REVIEW ZIP.

## Decisions

- See [ADR-0002](../../adr/0002-migrate-disk-image-builds-to-osbuild-image-builder.md)
- See [ADR-0004](../../adr/0004-use-public-github-standard-runner-as-m04-build-authority.md)
- Base: `quay.io/fedora/fedora-kinoite:44` (no silent fallback)
- QCOW2 rootfs remains **btrfs** (`--bootc-default-fs btrfs`)

## Validation evidence

### Layer A (local)

- `just ci` — includes 002E contracts (GitHub Actions workflow, Cirrus retired, CircleCI disabled)

### Layer B (real QCOW2 + UEFI boot)

- Not yet proven on GitHub Actions in this increment

## DoD status summary

V0.1 DoD success proof chain: not started (M05–M10). M04: **BLOCKED**.

## Backlog (future versions only)

No new features. V0.2+ remains out of scope.
