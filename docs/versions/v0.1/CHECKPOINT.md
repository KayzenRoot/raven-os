# Raven OS V0.1 — Checkpoint

- **STATUS:** IN PROGRESS
- **VERSION:** V0.1
- **PHASE:** Image Foundation (M04) — Prompt 002B correction
- **OBJECTIVE:** Deliver a small VM Cognitive Seed (local-first cognitive Linux OS seed), not the full long-term product.
- **VERSION PROGRESS:** 20% (20/100 Sol-accepted points; M04 pending Builder Layer B)
- **COMPLETED POINTS:** 20

## Sol state transition (INC-001)

Per Prompt 002 instruction from Sol (not executor self-acceptance):

- M01, M02, M03 = **ACCEPTED**
- INC-001 = **ACCEPTED**
- COMPLETED POINTS = **20**
- VERSION PROGRESS = **20%**

## Current scope

INC-002 / Prompt 002B — Layer A corrections applied; Layer B **BLOCKED** on this Windows executor host.

## Completed (Sol-accepted)

| Item | Status |
|------|--------|
| INC-001 / M01–M03 | ACCEPTED (20 points) |

## In progress / blocked

| Item | Status |
|------|--------|
| INC-002 / M04 | **BLOCKED** — Raven Builder Layer B not executed on this host |

## Prompt 002B Layer A corrections (applied)

- Boot smoke now requires explicit **UEFI/OVMF pflash** firmware (no implicit BIOS proof)
- Preflight blocks when OVMF firmware is unavailable
- Podman build/QCOW2/image-check share repo-local graphroot via `CONTAINERS_STORAGE_CONF`
- bootc-image-builder bind-mounts the same graphroot (no rootless/rootful mismatch)
- Builder setup instructions: [BUILDER-SETUP.md](BUILDER-SETUP.md)

## Blockers

**Executor host is Windows — not the Raven Builder:**

- Not Linux x86_64
- Podman unavailable
- KVM unavailable
- UEFI/OVMF not verifiable here
- Base/BIB digests remain `pending` until Builder preflight PASS

**Operator action:** provision/use Fedora Server 44 Builder VM per `docs/versions/v0.1/BUILDER-SETUP.md`, then run:

```bash
just builder-preflight
just build-image
just image-check
just build-qcow2
just artifact-metadata
just boot-smoke
just ci-image
just review
```

Do not fabricate QCOW2, digest, or boot evidence on non-Builder hosts.

## Decisions

- Base: `quay.io/fedora/fedora-kinoite:44` (official; no silent fallback)
- QCOW2 rootfs: `btrfs`
- Podman storage strategy: `repo-local-containers-storage-conf` (`.build/containers/storage`)
- Boot smoke: `q35` + OVMF pflash + serial log markers
- Manifest digests updated only when Builder preflight PASS

## Validation evidence

### Layer A (this host)

- `just ci` — fast gates including new M04 contract tests
- Review ZIP: `.review/RAVEN-OS-V0.1-INC-002-REVIEW.zip`

### Layer B (Builder — required for M04 REVIEW)

- Not executed here
- Expected evidence paths: `.build/evidence/`, `.build/qcow2/` (gitignored)

## Next step

Execute Layer B on Raven Builder VM; regenerate INC-002 review ZIP with real OCI/QCOW2/UEFI boot evidence.

## DoD status summary

V0.1 DoD success proof chain: not started (M05–M10). M04: **BLOCKED** pending Builder.

## Backlog (future versions only)

No new features. V0.2+ remains out of scope.
