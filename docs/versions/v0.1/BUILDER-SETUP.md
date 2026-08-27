# Raven Builder setup — INC-002 / Prompts 002B + 002C

## Primary authority (Prompt 002C)

**CircleCI Free** Linux `machine` executor is the primary M04 build authority (see
[ADR-0001](../../adr/0001-use-circleci-free-as-primary-v0.1-cloud-build-authority.md)).

Manual pipeline only:

1. Connect CircleCI project to `https://github.com/KayzenRoot/raven-os` branch `main`
2. Set Up Project (no paid features, no DLC)
3. Trigger pipeline with parameter **`run_m04=true`**
4. Download REVIEW ZIP artifact from the job (QCOW2 is not uploaded)

CircleCI config uses `ubuntu-2604:current`, `resource_class: medium`, and sets
`RAVEN_CLOUD_BUILDER=1` for TCG fallback when KVM is absent.

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

Expected outcomes on a capable Builder:

- `builder-preflight` → **PASS** and updates `os/image-source.toml` digests
- `build-image` / `image-check` / `build-qcow2` / `boot-smoke` → exit 0
- `ci-image` → all steps pass
- M04 may move to **REVIEW** (not ACCEPTED) for Sol audit

## Podman storage note (002B correction)

M04 uses a repo-local Podman graphroot under `.build/containers/storage` via
`CONTAINERS_STORAGE_CONF`. The same graphroot is bind-mounted into
bootc-image-builder at `/var/lib/containers/storage` so the Raven OCI image built
by `just build-image` is visible to `just build-qcow2`.

## Windows / non-Builder hosts

Do not fabricate OCI/QCOW2/boot evidence. Layer A (`just ci`) may pass, but M04
remains **BLOCKED** until the sequence above succeeds on the Builder.
