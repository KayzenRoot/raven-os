# Cirrus CI Operator Guide (V0.1)

Developer-only operations. Cirrus is **not** a Raven runtime dependency.

**Prompt 002D:** Cirrus Community Cluster (`compute_engine_instance` +
`cirrus-images` / `docker-kvm`) is the **primary** M04 disk-image builder
when `KayzenRoot/raven-os` is public. Heavy M04 is **manual only**.

See [ADR-0003](../../adr/0003-use-cirrus-ci-full-vm-as-primary-m04-build-authority.md)
and [CIRCLECI-M04-BLOCKER.md](CIRCLECI-M04-BLOCKER.md).

## Zero-cost rules

- Public OSS repository only (already required for Cirrus free eligibility)
- No payment method, no Cirrus paid plan, no private-repo compute
- No paid GCP project (`image_project` must remain `cirrus-images`)
- Manual trigger only (`trigger_type: manual`) — never on every push/PR
- Execution lock `raven-os-m04-heavy` — at most one heavy M04 at a time
- REVIEW ZIP artifact only (no QCOW2/OCI remote store)
- Do not paste API tokens into Git, `.env`, or review artifacts

## Install the Cirrus GitHub App (once)

1. Sign in to [Cirrus CI](https://cirrus-ci.com/) with GitHub.
2. Install/authorize the **Cirrus CI** GitHub App **only** for `KayzenRoot/raven-os`.
3. Remain on zero-cost OSS usage. Do not add a payment method.
4. Do not manually edit repository files inside the Cirrus UI.

App install URL (GitHub):

https://github.com/apps/cirrus-ci/installations/new/permissions?target_id=KayzenRoot

After authorization, the repository appears at:

https://cirrus-ci.com/github/KayzenRoot/raven-os

## Trigger one manual M04

The task name is `m04-cirrus-builder`. It does **not** run on push.

From the Cirrus repository page:

1. Open the latest `main` build / task list.
2. Trigger **m04-cirrus-builder** (play / manual trigger).
3. Do not start a second heavy M04 while one is running.

Expected host sequence (thin YAML over existing scripts):

```text
bash scripts/cirrus_bootstrap.sh
just run-m04-cloud
```

`just run-m04-cloud` already runs:

`ci` → `builder-preflight` → `build-image` → `image-check` → `build-qcow2`
(osbuild/image-builder, not archived bootc-image-builder) → `artifact-metadata`
→ `boot-smoke` → REVIEW ZIP.

Environment: `RAVEN_CLOUD_BUILDER=1`. Timeout: 120 minutes.

## Artifacts

Cirrus uploads only:

`.review/RAVEN-OS-V0.1-INC-002-REVIEW.zip`

Download it locally into `.review/` (gitignored). Verify SHA-256 before Sol audit.
A green Cirrus job does **not** accept M04.

## If Cirrus is not authorized

Stop with `HUMAN_CIRRUS_AUTH_REQUIRED`. Do not create a repository secret solely
to avoid one manual click.

## Fallback

Local Fedora Builder: `just ci-image`. CircleCI heavy M04 stays disabled.
