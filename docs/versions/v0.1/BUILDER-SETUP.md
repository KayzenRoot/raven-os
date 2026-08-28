# Raven Builder setup — INC-002 / Prompt 002D

## Primary authority

**Cirrus CI** Community Cluster full VM (`compute_engine_instance` /
`cirrus-images` / `docker-kvm`, nested virtualization) is the M04 disk-image
authority ([ADR-0003](../../adr/0003-use-cirrus-ci-full-vm-as-primary-m04-build-authority.md))
now that `KayzenRoot/raven-os` is **PUBLIC**.

Manual task: `m04-cirrus-builder`. See [CIRRUS-OPERATOR.md](CIRRUS-OPERATOR.md).

## CircleCI

CircleCI is **not** the M04 QCOW2/osbuild authority
([CIRCLECI-M04-BLOCKER.md](CIRCLECI-M04-BLOCKER.md)). Heavy workflow is disabled.
CLI tooling may remain for lightweight diagnostics.

## Fallback: local Fedora Server 44 Builder

## Minimum VM profile

- OS: Fedora Server 44 x86_64
- Firmware: UEFI
- vCPU: 4+
- RAM: 8 GiB+
- Disk: 64 GiB+ free for `.build/` artifacts
- Nested virtualization/KVM enabled when host supports it

## Packages (Fedora 44)

```bash
sudo dnf install -y podman qemu-kvm edk2-ovmf edk2-aarch64 git just
# uv (official installer)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify OVMF firmware exists (one of these pairs must be present):

- `/usr/share/edk2/ovmf/OVMF_CODE.secboot.fd`
- `/usr/share/OVMF/OVMF_CODE.secboot.fd`

## Clone repo inside Builder

```bash
git clone <raven-os-repo-url> raven-os
cd raven-os
uv sync --extra dev
```

## Layer B gate sequence

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

On Cirrus the same sequence runs via `just run-m04-cloud` after
`scripts/cirrus_bootstrap.sh`.

`just build-qcow2` uses current `osbuild/image-builder` (`--bootc-ref`,
`--bootc-default-fs btrfs`). Confirm flags with container `--help` on the Builder
and record the resolved digest.

Expected outcomes on a capable Builder:

- `builder-preflight` → **PASS** and updates `os/image-source.toml` digests
- `build-image` / `image-check` / `build-qcow2` / `boot-smoke` → exit 0
- `ci-image` → all steps pass
- M04 may move to **REVIEW** (not ACCEPTED) for Sol audit

## Podman storage note

On a local Fedora Builder, M04 uses a repo-local Podman graphroot under
`.build/containers/storage`. Cloud/full-VM rootful builds use
`/var/lib/containers/storage` so image-builder can see the Raven OCI image.

## Windows / non-Builder hosts

Do not fabricate OCI/QCOW2/boot evidence. Layer A (`just ci`) may pass, but M04
remains **BLOCKED** until the sequence above succeeds on a capable Builder.
