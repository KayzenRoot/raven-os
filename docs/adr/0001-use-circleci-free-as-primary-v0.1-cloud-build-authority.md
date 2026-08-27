# ADR 0001 — Use CircleCI Free as primary V0.1 cloud build authority

- **Status:** Accepted
- **Date:** 2026-08-27
- **Increment:** INC-002 / Prompt 002C

## Context

V0.1 originally froze a local Fedora Server 44 Raven Builder VM as the build authority for
M04 (bootc OCI image + QCOW2 + bounded UEFI boot smoke). The operator host cannot sustain
that local VM, creating a valid implementation blocker under the Architecture Change Policy.

Layer B gates (Podman, bootc-image-builder, QCOW2, UEFI boot smoke) remain required for M04
REVIEW. Only the **build authority location** changes for the current phase.

## Decision

1. **PRIMARY BUILD AUTHORITY:** CircleCI Free Linux `machine` executor (x86_64).
2. **FALLBACK:** Local/self-hosted Fedora Linux Builder when available.
3. **Pipeline trigger:** Manual pipeline parameter `run_m04=true` (default `false`).
4. **Executor:** `ubuntu-2604:current`, `resource_class: medium`.
5. **Acceleration:** Prefer KVM when present; **QEMU TCG is accepted** on cloud when nested
   virtualization is unavailable.
6. **UEFI:** OVMF/pflash remains mandatory; BIOS/SeaBIOS smoke is not acceptable proof.
7. **Artifacts:** Only the lightweight REVIEW ZIP may be stored remotely; QCOW2/OCI archives,
   Podman storage, caches, and secrets are excluded.
8. **Zero-paid-infrastructure:** No DLC, paid runners, macOS/Windows/GPU, or credit purchase
   mechanisms.

This ADR supersedes **only** the requirement that the Builder authority must be a local VM.
It does **not** change the Raven OS product target (Fedora/Kinoite bootc x86_64 UEFI).

## Consequences

- `.circleci/config.yml` becomes the manual M04 cloud entrypoint.
- `scripts/run_m04_cloud.py` orchestrates existing Justfile/scripts (thin CI layer).
- `RAVEN_CLOUD_BUILDER=1` enables TCG fallback without treating missing KVM alone as blocker.
- Source branch FLUXO/CHECKPOINT remain M04 **BLOCKED** until Sol audits a successful cloud run;
  ephemeral workspace may prepare **candidate** REVIEW handoff only.

## Risks

- CircleCI Free queue/time limits may delay or fail long image builds.
- TCG boot smoke is slower and less representative than KVM nested virt.
- Ubuntu Builder userspace differs from Fedora runtime target (acceptable for build-only phase).

## Rollback / reversibility

- Remove or disable `.circleci/config.yml` workflow.
- Re-enable local Fedora Builder as primary in docs/ADR follow-up.
- No Raven runtime/product architecture change is required to revert build authority.

## Future path to self-hosted/local builder

When local Fedora Server 44 resources are available, run the same `just ci-image` gates on the
local Builder and treat CircleCI as optional fallback. Sol may accept either evidence path if
objectively equivalent.
