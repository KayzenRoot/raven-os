# GitHub Actions Operator Guide (V0.1 M04)

Developer-only operations. GitHub Actions is **not** a Raven runtime dependency.

**Prompt 002E:** Standard public `ubuntu-24.04` GitHub-hosted runner is the **primary**
M04 disk-image builder when `KayzenRoot/raven-os` is **PUBLIC**. Heavy M04 is
**manual-only** (`workflow_dispatch` + `confirm_m04=true`).

See [ADR-0004](../../adr/0004-use-public-github-standard-runner-as-m04-build-authority.md),
[CIRCLECI-M04-BLOCKER.md](CIRCLECI-M04-BLOCKER.md), and superseded
[ADR-0003](../../adr/0003-use-cirrus-ci-full-vm-as-primary-m04-build-authority.md).

## Zero-cost rules

- **Public repository required** — standard runners are zero-cost only while the repo is public
- **Standard runner only** — `ubuntu-24.04` x64; no larger, GPU, macOS, or Windows runners
- **Manual dispatch only** — no push/PR/schedule automatic heavy builds
- **Concurrency lock** — `raven-m04-heavy` (one expensive run at a time)
- **REVIEW ZIP artifact only** — `raven-review`, 1-day retention; no QCOW2/OCI upload
- **No workflow cache** — no paid storage dependency
- **No secrets in repo** — use `gh auth login` locally; never commit PATs

## If repository becomes private

The workflow job is gated on `github.event.repository.private == false`. Heavy M04 on
GitHub-hosted runners must not run. Use local Fedora Builder (`just ci-image`) instead.
Do not enable paid runners.

## Prerequisites

```bash
gh --version
gh auth status
gh repo view KayzenRoot/raven-os --json visibility,isPrivate,defaultBranchRef
```

Visibility must be `PUBLIC` / `isPrivate: false`.

## Trigger one heavy M04 run

Inspect help first:

```bash
gh workflow run --help
```

Ensure no other M04 run is queued or in progress:

```bash
gh run list --workflow m04.yml --branch main --limit 5
```

Trigger exactly one run:

```bash
gh workflow run m04.yml --repo KayzenRoot/raven-os --ref main -f confirm_m04=true
```

## Monitor

```bash
gh run list --workflow m04.yml --branch main --limit 3
gh run watch <run-id> --compact --exit-status --interval 30
```

On failure:

```bash
gh run view <run-id> --log-failed
```

On failure:

```bash
gh run download <run-id> -n raven-m04-diagnostics -D .review-downloads
```

## Download REVIEW ZIP (success only)

```bash
mkdir -p .review-downloads
gh run download <run-id> -n raven-review -D .review-downloads
```

Validate `RAVEN-OS-V0.1-INC-002-REVIEW.zip` is non-zero, contains no QCOW2, and record SHA-256.

## Retry budget

- Prompt 002E: maximum **2** heavy attempts — **exhausted** (runs `33191087333`, `33191467126`)
- Prompt 002E-R1: **2** heavy attempts — **exhausted** (runs `33193783890`, `33195816360`)
- Prompt 002E-R2: **2 NEW** heavy attempts authorized (boot-smoke/QEMU/UEFI harness fix)
- One run at a time; fix evidence-backed issues before retry
- Run `just ci` locally before retry
- Never move to paid/larger runners

## Local fallback

When GitHub Actions is unavailable or the repo is private:

```bash
just ci-image
just review
```

## Cirrus / CircleCI

- **Cirrus M04:** retired (Prompt 002E); do not require `cirrus-ci.com`
- **CircleCI heavy M04:** disabled (`when: false`); do not retry osbuild on CircleCI
