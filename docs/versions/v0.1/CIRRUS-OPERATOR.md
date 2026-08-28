# Cirrus CI Operator Guide (V0.1)

Developer-only operations. Cirrus is **not** a Raven runtime dependency.

**Prompt 002D:** Cirrus Community Cluster (`compute_engine_instance` +
`cirrus-images` / `docker-kvm`) is the **primary** M04 disk-image builder
when `KayzenRoot/raven-os` is public. Heavy M04 is **commit-message gated**
(`[m04]` on `main`) — not a dashboard click, and not every push.

See [ADR-0003](../../adr/0003-use-cirrus-ci-full-vm-as-primary-m04-build-authority.md)
and [CIRCLECI-M04-BLOCKER.md](CIRCLECI-M04-BLOCKER.md).

## Zero-cost rules

- Public OSS repository only (already required for Cirrus free eligibility)
- No payment method, no Cirrus paid plan, no private-repo compute
- No paid GCP project (`image_project` must remain `cirrus-images`)
- Commit-message gate only (`CIRRUS_CHANGE_MESSAGE` contains `[m04]` on `main`)
  — never on ordinary pushes/PRs. Cirrus does **not** set `CIRRUS_COMMIT_MESSAGE`.
- Execution lock `raven-os-m04-heavy` — at most one heavy M04 at a time
- REVIEW ZIP artifact only (no QCOW2/OCI remote store)
- Do not paste API tokens into Git, `.env`, or review artifacts
- Do not require opening `cirrus-ci.com`. GitHub Checks on the SHA are enough.

## Install the Cirrus GitHub App (once)

1. Sign in to [Cirrus CI](https://cirrus-ci.com/) with GitHub.
2. Install/authorize the **Cirrus CI** GitHub App **only** for `KayzenRoot/raven-os`.
3. Remain on zero-cost OSS usage. Do not add a payment method.
4. Do not manually edit repository files inside the Cirrus UI.

App install URL (GitHub):

https://github.com/apps/cirrus-ci/installations/new/permissions?target_id=KayzenRoot

After authorization, the repository appears at:

https://cirrus-ci.com/github/KayzenRoot/raven-os

GitHub App Cirrus CI is already installed for this repository only
(installation id `157274806`).

## Trigger one heavy M04 (commit-message gate)

The task name is `m04-cirrus-builder`. It does **not** run on ordinary pushes.

Cirrus `only_if` (single-line in `.cirrus.yml`) creates the task only when
**all** of:

- `$CIRRUS_REPO_FULL_NAME == 'KayzenRoot/raven-os'`
- `$CIRRUS_BRANCH == 'main'`
- `$CIRRUS_CHANGE_MESSAGE =~ '.*\[m04\].*'`
  (`CIRRUS_CHANGE_MESSAGE` = commit message on push; first line is
  `CIRRUS_CHANGE_TITLE`. There is no `CIRRUS_COMMIT_MESSAGE`.)

If GitHub shows a `cirrus-ci` check suite with **0 check-runs** on an `[m04]`
SHA, verify `only_if` is one line (no YAML `>-` folding).

To start **one** cloud M04: commit on `main` with `[m04]` in the message and
push to `origin/main`. Example:

```text
ci: run M04 on Cirrus via [m04] commit gate
```

Watch GitHub Checks on that SHA (`gh api repos/KayzenRoot/raven-os/commits/SHA/check-runs`).
Do not open the Cirrus dashboard. Do not start a second heavy M04 while one is
running (execution lock `raven-os-m04-heavy`).

Ordinary pushes without `[m04]` may still create an **empty** Cirrus check suite
(0 check-runs). That is the gate working, not a started M04.

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

## GitHub App status

Cirrus CI GitHub App is installed for `KayzenRoot/raven-os` only
(installation id `157274806`). Do not add payment. Do not broaden the install.

## If Cirrus is not authorized

Stop with `HUMAN_CIRRUS_AUTH_REQUIRED`. Do not create a repository secret solely
to avoid one click. The `[m04]` commit gate replaces dashboard triggering.

## Fallback

Local Fedora Builder: `just ci-image`. CircleCI heavy M04 stays disabled.
