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

## Agent skills

### Matt Pocock skill invocation

When the `mattpocock-skills` plugin is available, automatically use a model-invoked skill whose description matches the current task; these skills do not require the user to type a slash command. Use `/ask-matt` when skill routing is unclear. User-invoked workflows remain user-led. Do not force-fit a skill or let it override the user's request, this repository's governance/security rules, or deterministic evidence.

Prefer deterministic Git, text search, AST, hashes, tests, lint, typecheck, and build checks whenever they are sufficient. Use Jev only when available and useful for bounded context relevance, triage, classification, reranking, claim verification, comparison, or explicit-gate decisions. Jev output is advisory; never send it secrets or credentials.

### Issue tracker

Issues and specs for this repository live in GitHub Issues. Use the `gh` CLI and follow `docs/agents/issue-tracker.md`.

### Triage labels

Use `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, and `wontfix` for the five canonical triage roles. Follow `docs/agents/triage-labels.md`.

### Domain docs

This repository uses a single-context domain layout. Read relevant glossary and ADR material before domain changes; follow the actual paths recorded in `docs/agents/domain.md`.
