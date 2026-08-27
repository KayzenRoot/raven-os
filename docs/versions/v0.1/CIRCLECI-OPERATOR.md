# CircleCI Operator Guide (V0.1 / M04)

Developer-only operations for the Raven CircleCI cloud Builder. CircleCI CLI is **not** a Raven runtime dependency.

## Install CLI (Windows)

Use the official WinGet package only:

```powershell
winget search CircleCI
winget install --id CircleCI.CLI --accept-package-agreements --accept-source-agreements
circleci --version
```

Do not install third-party wrappers or legacy unofficial packages.

## Authenticate (no tokens in Git)

```powershell
circleci auth login
circleci auth me
```

Credentials are stored in the OS credential manager via CircleCI OAuth. Never paste a personal API token into `.env`, docs, or review artifacts.

Optional telemetry preference (developer tool only):

```powershell
circleci setting set telemetry off
```

## Link this repository

From the repository root:

```powershell
circleci project link
circleci run list --json
```

If `.circleci/info.yml` is created, inspect it for project metadata only (no secrets). Keep it version-controlled when it contains non-secret project identifiers.

## Mandatory config validation

Before any M04 cloud trigger:

```powershell
just circleci-validate
just ci
```

`just circleci-validate` runs `circleci config validate` against `.circleci/config.yml`.

## Inspect recent runs

```powershell
circleci run list --json
circleci run get <run-id>
circleci job get <job-id>
```

Use runtime `--help` on each command; CircleCI CLI v1 flags may change between releases.

## Manual M04 trigger (`run_m04=true`)

The heavy workflow is **disabled by default**. Trigger exactly one run with the Boolean pipeline parameter:

```powershell
circleci run trigger --help
```

Use the syntax supported by your installed CLI to target branch `main` and set `run_m04=true`. Do not change the default parameter in config.

Monitor without the browser:

```powershell
circleci run get <run-id>
```

Poll no faster than every 20–30 seconds. Do not start parallel M04 runs.

## Zero-cost rules

- CircleCI Free only; no paid credits or DLC
- `resource_class: medium` only (no `large` without Sol approval)
- Maximum three new M04 cloud attempts per correction cycle unless Sol approves more
- REVIEW ZIP artifact only (no QCOW2/OCI remote upload)

## Optional: CircleCI MCP for Cursor

After CLI auth and project link:

```powershell
circleci mcp cursor enable
```

MCP is optional. If Cursor requires a restart, continue with CLI commands until MCP is available.

## Successful M04 cloud run

A green job does **not** accept M04. Download the artifact locally (outside Git staging):

```powershell
circleci artifact --help
```

Expected file: `.review/RAVEN-OS-V0.1-INC-002-REVIEW.zip` (gitignored). Verify SHA-256 before Sol audit.
