# CircleCI M04 disk-image blocker (Prompt 002D)

CircleCI is **rejected** as M04 QCOW2/osbuild build authority. Do not retry the heavy
`m04-cloud-build` job. Repeated capability/security-flag changes did not remove the
platform restriction.

## Latest relevant runs

| Run ID | Commit | Outcome | Notes |
|--------|--------|---------|-------|
| `05cfbf5a-e2b0-40af-9e2e-f2c4f011ee11` (#28) | `661a5d6` | FAILED | Latest: osbuild mount denied after `--userns=host` |
| `cc7814c5-6ee6-4ee7-8885-96ea620ea334` (#26) | `1f8b4c6` | FAILED | osbuild mount denied after SYS_ADMIN/seccomp/`/run/osbuild` |
| `1840743f-83c9-4b74-82e4-72f02135ad27` (#24) | `0de5c57` | FAILED | First osbuild `permission denied` after storage alignment |

Earlier CircleCI diagnostics (OVMF, CI env leak, rootless Podman, sudo `-E`) were
fixed and are **not** the remaining blocker.

## Failed step

- Workflow: `m04-manual`
- Job: `m04-cloud-build`
- Step: `just build-qcow2` / bootc-image-builder → osbuild
- Exact error:

```
RuntimeError: mount: /run/osbuild/containers/storage: permission denied.
       dmesg(1) may have more information after failed mount system call. (code: 32)
```

Also observed: `fchownat() ... failed: Operation not permitted` during
`org.osbuild.container-deploy`.

## Environment / executor

- CircleCI `machine` / `ubuntu-2604:current` / `resource_class: medium`
- `RAVEN_CLOUD_BUILDER=1`
- Linux x86_64 AWS kernel (`7.0.0-1004-aws`)
- KVM absent; TCG accepted
- Rootful Podman via `sudo env …` after later fixes
- Graphroot aligned to `/var/lib/containers/storage`

## Strategies already attempted (no further retries)

- Ubuntu OVMF 4M path discovery
- Isolate `RAVEN_CLOUD_BUILDER` from the `just ci` gate
- Podman `cgroupfs` + `BUILDAH_ISOLATION=chroot`
- Rootful `sudo env CONTAINERS_* podman`
- System graphroot `/var/lib/containers/storage` for BIB mount identity
- Privileged BIB: `SYS_ADMIN`, `seccomp=unconfined`, `label=disable`, `/dev`, `/run/osbuild`
- `--userns=host`

Further CircleCI M04 heavy attempts add no information.

## Evidence that earlier M04 gates passed on CircleCI

On the osbuild-failing runs (`1840743f`, `cc7814c5`, `05cfbf5a`):

- `just ci` — PASS
- `builder-preflight` — PASS (Kinoite 44 digest captured)
- `build-image` — PASS (`localhost/raven-os:0.1-dev`)
- `image-check` — PASS
- Failure is **specifically** QCOW2/osbuild nested mount, not OCI construction

Verified Fedora Kinoite 44 digest from preflight:

`sha256:079f493ebc3ddf75de92e1d53e908fa5b9269dc40634c0b9bbf9c0322840d4a4`

## Authority change

M04 disk-image authority moves off CircleCI (ADR-0003). CircleCI may remain for
lightweight diagnostics only. The heavy workflow is disabled in `.circleci/config.yml`.
