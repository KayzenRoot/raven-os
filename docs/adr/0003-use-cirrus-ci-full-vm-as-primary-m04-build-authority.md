# ADR 0003 — Use Cirrus CI full VM as primary zero-cost M04 build authority

- **Status:** Accepted (authority intent) — **activation BLOCKED** until the GitHub
  repository is public and Cirrus OSS free eligibility is confirmed.
- **Date:** 2026-08-28
- **Increment:** INC-002 / Prompt 002D
- **Supersedes:** ADR-0001 **only** for M04 disk-image / QCOW2/osbuild authority.

## Context

ADR-0001 made CircleCI Free `machine` the primary M04 cloud Builder. CircleCI
repeatedly failed osbuild nested mounts (`mount: /run/osbuild/containers/storage:
permission denied`) despite rootful Podman and privilege flags. See
[CIRCLECI-M04-BLOCKER.md](../versions/v0.1/CIRCLECI-M04-BLOCKER.md).

Cirrus CI managed `docker_builder` is a full VM intended for privileged
container builds and is free for public open-source repositories. Cirrus is
**not** free for private repositories; using it on a private repo would create
a paid-infrastructure dependency.

As of Prompt 002D inspection, `KayzenRoot/raven-os` visibility is **PRIVATE**.

## Decision

1. **PRIMARY (when eligible):** Cirrus CI `docker_builder` full VM, manual
   heavy M04 task only (`trigger_type: manual` + execution lock).
2. **CircleCI:** lightweight optional CI / diagnostics only. Heavy M04 path
   disabled so it cannot be triggered accidentally.
3. **FALLBACK:** local/self-hosted Fedora Builder (`just ci-image`).
4. **Zero-paid-infrastructure:** no Cirrus paid plan, no CircleCI paid features,
   no automatic visibility change.
5. **Do not create `.cirrus.yml` or connect the Cirrus GitHub App while the
   repository is private.** That would be a paid dependency.

## Cirrus free-for-OSS constraint

Cirrus OSS credits apply to public repositories. Private repos are out of
scope for Raven's zero-cost rule.

## Manual heavy task / cost guard (when later activated)

- Manual trigger only (no push/PR auto-run).
- Execution lock against concurrent M04 jobs.
- Maximum two heavy Cirrus attempts per increment prompt without a new root cause.
- REVIEW ZIP artifact only (no QCOW2/OCI upload).

## Privileged build requirement

osbuild/image-builder needs rootful Podman, loop/mount, and a full VM — not a
restricted nested Kubernetes `container` executor.

## Reversibility

- Keep CircleCI CLI/config for lightweight checks.
- Re-enable local Fedora Builder at any time.
- After the repo is public, add `.cirrus.yml` in a follow-up increment and
  require a single human Cirrus GitHub App authorization for `KayzenRoot/raven-os`.

## Current stop

`BLOCKED - CIRRUS OSS FREE ELIGIBILITY REQUIRES PUBLIC REPOSITORY`

Do not change repository visibility automatically. Human/Sol must decide
whether to make `KayzenRoot/raven-os` public.
