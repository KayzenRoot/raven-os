# ADR 0003 — Use Cirrus CI full VM as primary zero-cost M04 build authority

- **Status:** Accepted
- **Date:** 2026-08-28
- **Increment:** INC-002 / Prompt 002D
- **Supersedes:** ADR-0001 **only** for M04 disk-image / QCOW2/osbuild authority.

## Context

ADR-0001 made CircleCI Free `machine` the primary M04 cloud Builder. CircleCI
repeatedly failed osbuild nested mounts (`mount: /run/osbuild/containers/storage:
permission denied`) despite rootful Podman and privilege flags. See
[CIRCLECI-M04-BLOCKER.md](../versions/v0.1/CIRCLECI-M04-BLOCKER.md).

Cirrus CI Community Cluster `compute_engine_instance` (`image_project:
cirrus-images`, `family/docker-kvm`, nested virtualization) is a full VM
intended for privileged container builds and is free for **public** open-source
repositories. Cirrus is **not** free for private repositories.

`KayzenRoot/raven-os` visibility is **PUBLIC** (verified 2026-08-28 via
`gh repo view --json visibility,isPrivate`).

## Decision

1. **PRIMARY:** Cirrus CI Community Cluster full VM, manual heavy M04 task only
   (`trigger_type: manual` + execution lock `raven-os-m04-heavy`).
2. **Executor:** `compute_engine_instance` with `image_project: cirrus-images`
   (OSS community images, **not** a paid GCP project). Nested virtualization is
   enabled so `/dev/kvm` can exist for osbuild/QEMU. Do not use a Kubernetes
   `container` executor for M04.
3. **CircleCI:** lightweight optional CI / diagnostics only. Heavy M04 path
   disabled so it cannot be triggered accidentally.
4. **FALLBACK:** local/self-hosted Fedora Builder (`just ci-image`).
5. **Zero-paid-infrastructure:** no Cirrus paid plan, no CircleCI paid features,
   no GHCR as a Raven product registry.

## Cirrus free-for-OSS constraint

Cirrus OSS credits apply to public repositories. If visibility ever becomes
private again, stop using Cirrus and do not add paid compute.

## Manual heavy task / cost guard

- Manual trigger only (no push/PR auto-run).
- Execution lock against concurrent M04 jobs.
- Timeout ~2 hours.
- REVIEW ZIP artifact only (no QCOW2/OCI upload).
- Thin YAML: install tools, set `RAVEN_CLOUD_BUILDER=1`, run existing
  `just run-m04-cloud` (image-builder QCOW2 path, not archived bootc-image-builder).

## Privileged build requirement

osbuild/image-builder needs rootful Podman, loop/mount, and a full VM — not a
restricted nested Kubernetes `container` executor.

## Reversibility

- Keep CircleCI CLI/config for lightweight checks (heavy workflow stays off).
- Re-enable local Fedora Builder at any time.
- Removing `.cirrus.yml` reverts cloud authority without a product-architecture change.
