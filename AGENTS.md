# Raven OS — Agent Instructions

## Roles

- **Sol** (GPT-5.6 Sol): architect and reviewer. Only Sol marks work **ACCEPTED**.
- **Executor** (Cursor/Codex): implement, test, fix. Never self-accept weighted points.

## Before any work

1. Inspect the existing repository tree; adapt to present state — do not overwrite blindly.
2. Read `docs/versions/v0.1/FLUXO.md`, `CHECKPOINT.md`, `DEFINITION-OF-DONE.md`, and relevant ADRs.
3. Do not expand scope beyond the active increment.
4. Frozen V0.1 architecture cannot change without an ADR and objective reason.

## Operating rules

- Evidence before completion: claims require command/test output.
- No secrets in the repository or review artifacts.
- Use the `just` command facade (`just test|lint|format-check|typecheck|ci|review`).
- Update FLUXO and CHECKPOINT after every increment.
- Prefer minimal relevant context and diff-first review packages.
- Executor may mark modules **REVIEW**; only Sol marks **ACCEPTED**.
- COMPLETED POINTS and VERSION PROGRESS stay at 0 until Sol acceptance.

## Out of scope reminder

Do not implement future V0.1 modules (M04–M10) or V0.2+ capabilities unless the active increment explicitly requires them.
