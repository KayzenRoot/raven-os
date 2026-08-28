# ADR 0002 — Migrate Raven disk-image builds to current osbuild/image-builder

- **Status:** Accepted
- **Date:** 2026-08-28
- **Increment:** INC-002 / Prompt 002D

## Context

M04 previously invoked the archived `bootc-image-builder` container
(`quay.io/centos-bootc/bootc-image-builder`) with the old CLI (`--type qcow2`,
positional bootc ref). Upstream merged `osbuild/bootc-image-builder` into
`osbuild/image-builder` and archived the old repository.

Continuing to design around the archived CLI/container is undesirable: flags,
container names, and support channels will diverge from current osbuild docs.

This ADR changes **build tooling only**. Raven product base remains Fedora
Kinoite 44 bootc x86_64 UEFI with btrfs rootfs.

## Decision

1. Preferred disk-image tool: current `osbuild/image-builder` project.
2. Preferred container reference: `ghcr.io/osbuild/image-builder:latest`
   (digest verified on the Builder before pin; not treated as a release pin).
3. Preferred bootc CLI shape (from published usage; re-verify with runtime
   `--help` on the Builder before treating a flag as mandatory):

   `build --arch x86_64 --bootc-ref <raven-oci> --bootc-default-fs btrfs --output-dir /output qcow2`

4. Preserve `btrfs` via `--bootc-default-fs` when the Raven/Kinoite container
   does not declare a default filesystem (Fedora bootc images often require this).
5. Do not silently switch filesystem or product base to bypass a tooling error.
6. Capture image-builder `--help`, `build --help`, and resolved digest in
   Builder evidence.

## Compatibility impact

- `os/image-source.toml` tooling keys move from `bootc_image_builder_*` to
  `image_builder_*`.
- `scripts/build_qcow2.py` no longer emits archived `--type qcow2` invocation.
- Local Fedora Builder fallback uses the same new CLI.

## Migration strategy

1. Update manifest and Python contracts.
2. Discover flags from published docs, then confirm on Builder via `--help`.
3. If `ghcr.io/osbuild/image-builder` cannot be pulled, record an upstream
   tooling blocker (documented rollback: `ghcr.io/osbuild/image-builder-cli`
   container as published in merge notes — only with a follow-up ADR).
4. Do not keep the archived BIB path as the preferred production tool.

## Rollback

- Revert this ADR and restore archived BIB reference/CLI only if current
  image-builder cannot build the Raven bootc source and Sol accepts a temporary
  rollback.
- Product Containerfile/base image remains unchanged either way.

## Consequences

- Preflight inspects `image_builder_reference` instead of archived BIB.
- Review ZIP includes current image-builder ref + digest when Layer B runs.
