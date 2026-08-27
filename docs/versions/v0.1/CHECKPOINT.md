# Raven OS V0.1 — Checkpoint

- **STATUS:** IN PROGRESS
- **VERSION:** V0.1
- **PHASE:** Image Foundation (M04) — Prompt 002C-R2 CircleCI CLI autonomous ops
- **OBJECTIVE:** Deliver a small VM Cognitive Seed (local-first cognitive Linux OS seed), not the full long-term product.
- **VERSION PROGRESS:** 20% (20/100 Sol-accepted points; M04 pending real cloud/local Layer B)
- **COMPLETED POINTS:** 20

## Sol state transition (INC-001)

Per Prompt 002 instruction from Sol (not executor self-acceptance):

- M01, M02, M03 = **ACCEPTED**
- INC-001 = **ACCEPTED**
- COMPLETED POINTS = **20**
- VERSION PROGRESS = **20%**

## Current scope

INC-002 / Prompt 002C-R2 — CLI authenticated; failed run `a5b7d183` diagnosed (OVMF path gap on Ubuntu); fix in flight.

## CircleCI CLI ops (002C-R2)

- CircleCI CLI **v1.0.48840**; auth **PASS** (`KayzenRoot`); project linked (`gh/KayzenRoot/raven-os`)
- Failed run evidence: `a5b7d183-3a1b-41cd-89cc-b2c84352b44b` / job `0f66ca30-632c-41fa-b5a8-f80f5f3e32d6`
- Root cause: `builder-preflight` BLOCKED — **UEFI/OVMF firmware unavailable** (Ubuntu `OVMF_CODE_4M*.fd` paths missing from detector)
- Fix: expand OVMF candidate paths + `/usr/share/OVMF` discovery in `raven_build_config.py`

## Completed (Sol-accepted)

| Item | Status |
|------|--------|
| INC-001 / M01–M03 | ACCEPTED (20 points) |

## In progress / blocked

| Item | Status |
|------|--------|
| INC-002 / M04 | **BLOCKED** — OVMF detection fix pushed; cloud retry pending |

## Prompt 002C infrastructure change (applied in source)

- ADR-0001: CircleCI Free = **PRIMARY** build authority; local Fedora Builder = **FALLBACK**
- `.circleci/config.yml` with manual pipeline parameter `run_m04` (default `false`)
- `scripts/run_m04_cloud.py` orchestrates existing Justfile/scripts
- TCG + UEFI/OVMF supported on cloud when KVM absent (`RAVEN_CLOUD_BUILDER=1`)
- `scripts/finalize_cloud_result.py` finalizes CircleCI job status (no shell heredocs in YAML)

## Blockers

**Next human/operator step:**

1. Complete CircleCI CLI OAuth: `circleci auth login` (browser authorize; no token in Git)
2. Link project: `circleci project link` from repository root
3. Inspect failed run: `circleci run list --json` → `circleci run get <id>` / `circleci job get <id>`
4. After fix + `just circleci-validate` + `just ci`, trigger one M04 run with `run_m04=true`

Source branch remains **M04 BLOCKED** until Sol audits a successful cloud run.

## Decisions

- See [ADR-0001](../../adr/0001-use-circleci-free-as-primary-v0.1-cloud-build-authority.md)
- Preserve 002B Podman storage + UEFI/OVMF corrections
- Base: `quay.io/fedora/fedora-kinoite:44` (no silent fallback)

## Validation evidence

### Layer A (local)

- `just ci` — includes CircleCI/cloud contract tests
- Pushed to `origin/main` after Prompt 002C

### Layer B (CircleCI cloud — required for M04 REVIEW)

- Not executed yet
- Expected: `.build/evidence/run-m04-cloud.json`, REVIEW ZIP artifact only

## Next step

Configure CircleCI project and trigger first manual M04 cloud pipeline (`run_m04=true`).

## DoD status summary

V0.1 DoD success proof chain: not started (M05–M10). M04: **BLOCKED** pending first cloud Builder run.

## Backlog (future versions only)

No new features. V0.2+ remains out of scope.
