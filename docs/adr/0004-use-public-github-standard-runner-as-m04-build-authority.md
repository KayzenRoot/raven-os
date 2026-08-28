# ADR 0004 — Use public GitHub standard runner as zero-cost M04 build authority

- **Status:** Accepted
- **Date:** 2026-08-28
- **Increment:** INC-002 / Prompt 002E
- **Supersedes:** ADR-0003 **only** for M04 disk-image / QCOW2/osbuild authority.
  ADR-0001 and ADR-0003 remain historical; CircleCI heavy M04 stays disabled.

## Context

1. **Original GitHub Actions blocker:** When `KayzenRoot/raven-os` was private, standard
   GitHub-hosted runner minutes were exhausted. Heavy M04 on GitHub-hosted runners was
   prohibited for zero-paid-infrastructure compliance.
2. **Repository is now public:** `KayzenRoot/raven-os` visibility is **PUBLIC** (verified
   via `gh repo view --json visibility,isPrivate`). Public repositories receive
   zero-cost standard GitHub-hosted Linux runner minutes.
3. **CircleCI blocker (ADR-0001/0002):** osbuild nested mounts failed on CircleCI
   (`permission denied` on `/run/osbuild/containers/storage`). Heavy CircleCI M04 remains
   disabled.
4. **Cirrus blocker (ADR-0003):** Cirrus Community Cluster was evaluated but the operator
   network cannot reach `cirrus-ci.com` without VPN (explicitly out of scope). Cirrus
   posted empty check suites and is not operationally reachable.
5. **Need:** A cloud build authority reachable through GitHub itself (`gh` CLI), with no
   paid infrastructure, using current `ghcr.io/osbuild/image-builder`.

## Decision

### Primary M04 authority

- **GitHub Actions** on the **public** repository
- **Standard Linux runner only:** `ubuntu-24.04`, x64
- **Trigger:** `workflow_dispatch` only, with required boolean input `confirm_m04`
  (default `false`)
- **No automatic triggers** (no push, pull_request, schedule, workflow_run, repository_dispatch)
- **Concurrency:** `raven-m04-heavy`, `cancel-in-progress: false`
- **Timeout:** 90 minutes (initial)
- **Permissions:** `contents: read` only (validation-only workflow)
- **Artifacts:** lightweight `raven-review` ZIP only, `retention-days: 1`
- **Orchestration:** `.github/workflows/m04.yml` calls `scripts/github_actions_bootstrap.sh`
  and existing `just run-m04-cloud` (Justfile/scripts remain source of truth)

### Fallback

- Local/self-hosted Fedora Builder (`just ci-image`)

### Guard — repository becomes private

If visibility returns to **private**:

- The heavy M04 workflow must refuse execution (`github.event.repository.private == true`)
- No paid GitHub runner usage is authorized
- Operators must use local Builder fallback

### Cost policy

- No larger runners, no paid storage, no workflow cache
- No QCOW2 or OCI upload as GitHub artifacts
- REVIEW ZIP only with short retention

### Security

- Minimal token permissions (`contents: read`)
- No PAT or secrets stored in the repository
- Official GitHub-maintained actions pinned by commit SHA
- No untrusted PR execution for privileged build (manual dispatch only)

### Disk policy

Standard `ubuntu-24.04` runners have finite ephemeral SSD. M04 measures free space at job
start and may remove only large preinstalled SDK/tool caches unrelated to M04 before
blocking with `BLOCKED - STANDARD GITHUB RUNNER DISK CAPACITY`.

### Reversibility

Build orchestration remains thin. Removing `.github/workflows/m04.yml` reverts cloud
authority without a product-architecture change. Real build logic stays in versioned
scripts and the Justfile.

## Cirrus retirement

Cirrus `.cirrus.yml` is removed. The Cirrus GitHub App may remain installed but is not an
operational M04 dependency. No future Raven task may require `cirrus-ci.com` unless
separately approved.
