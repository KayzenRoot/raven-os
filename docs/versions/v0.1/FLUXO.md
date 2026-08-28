# Raven OS V0.1 — FLUXO

Frozen module weights for Raven OS V0.1 (VM Cognitive Seed).
**Total points: 100.** Do not change weights without a Sol-approved architecture/scope decision.

## Module weights

| ID | V0.1 module | Points | Status |
|----|-------------|-------:|--------|
| M01 | Repository structure + operational documentation | 8 | ACCEPTED |
| M02 | Development quality harness + stable commands | 7 | ACCEPTED |
| M03 | Review ZIP/evidence packaging | 5 | ACCEPTED |
| M04 | Raven bootc base image + QCOW2 build path | 12 | BLOCKED |
| M05 | ravend core service + D-Bus contract | 12 | TODO |
| M06 | CognitiveBackend + configurable provider/Hermes adapter | 12 | TODO |
| M07 | SQLite persistence + minimal memory/profile/session state | 10 | TODO |
| M08 | Safe user-context system tools + correlation/audit | 8 | TODO |
| M09 | Minimal PySide6/QML Raven UI | 10 | TODO |
| M10 | Integrated VM acceptance flow + reboot persistence proof | 16 | TODO |
| **TOTAL** | | **100** | |

### Weight checks

- M01 + M02 + M03 = **20** (accepted by Sol via INC-001 audit)
- M04 = **12** (repository work present; Layer B **BLOCKED** — GitHub Actions workflow added; QCOW2+boot not yet proven on cloud)
- COMPLETED POINTS = **20** (Sol-accepted only; M04 not counted)
- VERSION PROGRESS = **20%**

Governance: executor may mark M04 as **REVIEW** only after real Builder validation passes.
Only Sol may mark modules **ACCEPTED**. M04 remains **BLOCKED**.

## Sol state transition (INC-001)

Applied per Prompt 002 instruction from Sol (not executor self-acceptance):

- M01 = ACCEPTED
- M02 = ACCEPTED
- M03 = ACCEPTED
- INC-001 = ACCEPTED
- COMPLETED POINTS = 20
- VERSION PROGRESS = 20%

## Increment queue

| Increment | Scope | Points | Status |
|-----------|-------|-------:|--------|
| INC-001 | M01 + M02 + M03 — repository bootstrap | 20 | ACCEPTED (Sol) |
| INC-002 | M04 — bootc base image + QCOW2 build path | 12 | BLOCKED — 002E-R2 boot-smoke harness hardened; Layer B pending GHA |
| INC-003 | Placeholder — future Sol-scoped increment | — | PLANNED |
| INC-004 | Placeholder — future Sol-scoped increment | — | PLANNED |
| INC-005 | Placeholder — future Sol-scoped increment | — | PLANNED |
