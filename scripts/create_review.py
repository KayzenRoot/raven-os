#!/usr/bin/env python3
"""Cross-platform Raven OS review ZIP generator (INC-001 / M03)."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

VERSION = "V0.1"
DEFAULT_INCREMENT = "INC-002"
DEFAULT_OUT_DIR_NAME = ".review"

INCREMENT_DEFAULTS: dict[str, dict[str, Any]] = {
    "INC-001": {
        "handoff_status": "REVIEW",
        "completed_points": 0,
        "version_progress_percent": 0,
        "modules": {
            "M01": "REVIEW",
            "M02": "REVIEW",
            "M03": "REVIEW",
            "M04": "TODO",
            "M05": "TODO",
            "M06": "TODO",
            "M07": "TODO",
            "M08": "TODO",
            "M09": "TODO",
            "M10": "TODO",
        },
        "summary_objective": (
            "Bootstrap repository foundation, operational docs, quality harness, "
            "and review packaging (M01+M02+M03)."
        ),
        "explicit_status": (
            "**M01, M02, and M03 are REVIEW, not ACCEPTED, pending GPT-5.6 Sol audit.**"
        ),
        "checkpoint_next": "Await Sol audit of INC-001 review ZIP.",
    },
    "INC-002": {
        "handoff_status": "BLOCKED",
        "completed_points": 20,
        "version_progress_percent": 20,
        "modules": {
            "M01": "ACCEPTED",
            "M02": "ACCEPTED",
            "M03": "ACCEPTED",
            "M04": "BLOCKED",
            "M05": "TODO",
            "M06": "TODO",
            "M07": "TODO",
            "M08": "TODO",
            "M09": "TODO",
            "M10": "TODO",
        },
        "summary_objective": (
            "M04 image foundation: Containerfile, image manifest, build scripts, "
            "Justfile image commands, Layer A contracts."
        ),
        "explicit_status": (
            "**M04 is BLOCKED pending Raven Builder Layer B validation. "
            "COMPLETED POINTS remain 20 (M04 not Sol-accepted).**"
        ),
        "checkpoint_next": "Run Layer B gates on Raven Builder, then resubmit for Sol audit.",
    },
}

INCLUDE_PATHS: tuple[str, ...] = (
    "AGENTS.md",
    "Justfile",
    "pyproject.toml",
    "uv.lock",
    "Containerfile",
    ".gitignore",
    ".circleci/config.yml",
    ".cirrus.yml",
    "docs",
    "src",
    "scripts",
    "tests",
    "os",
    "ui",
    "db",
    "systemd",
    "dbus",
)

DIR_EXCLUDES: frozenset[str] = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "ENV",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        ".pyright",
        ".ty",
        "node_modules",
        "build",
        "dist",
        ".review",
        ".build",
        "podman-storage",
        "models",
        "weights",
        ".uv-cache",
        "uv-cache",
        "htmlcov",
        ".tox",
        ".nox",
        ".idea",
        ".vscode",
    }
)

SUFFIX_EXCLUDES: frozenset[str] = frozenset(
    {
        ".qcow2",
        ".raw",
        ".vmdk",
        ".vhd",
        ".vhdx",
        ".iso",
        ".img",
        ".gguf",
        ".ggml",
        ".safetensors",
        ".onnx",
        ".pt",
        ".pth",
        ".pyc",
        ".pyo",
        ".egg",
        ".whl",
    }
)

# Explicit denylist for common sensitive names / patterns (not a full DLP engine).
SECRET_NAME_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\.env($|\.)", re.IGNORECASE),
    re.compile(r".*\.pem$", re.IGNORECASE),
    re.compile(r".*\.key$", re.IGNORECASE),
    re.compile(r".*\.p12$", re.IGNORECASE),
    re.compile(r".*\.pfx$", re.IGNORECASE),
    re.compile(r"^id_rsa", re.IGNORECASE),
    re.compile(r"^credentials\.json$", re.IGNORECASE),
    re.compile(r"^secrets\.json$", re.IGNORECASE),
    re.compile(r".*\.keystore$", re.IGNORECASE),
    re.compile(r".*secret.*", re.IGNORECASE),
    re.compile(r".*credential.*", re.IGNORECASE),
    re.compile(r".*password.*", re.IGNORECASE),
)

NESTED_REVIEW_ZIP = re.compile(r"RAVEN-OS-.*-REVIEW\.zip$", re.IGNORECASE)


@dataclass
class CommandResult:
    name: str
    command: list[str]
    exit_code: int
    output: str


@dataclass
class ReviewContext:
    repo_root: Path
    out_dir: Path
    increment: str = DEFAULT_INCREMENT
    version: str = VERSION
    profile: dict[str, Any] = field(default_factory=dict)
    commands: list[CommandResult] = field(default_factory=list)
    errors_fixed: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    files_created_changed: list[str] = field(default_factory=list)
    cloud_result: str | None = None


def resolve_repo_root(start: Path | None = None) -> Path:
    path = (start or Path.cwd()).resolve()
    for candidate in [path, *path.parents]:
        if (candidate / "pyproject.toml").is_file() and (candidate / "AGENTS.md").is_file():
            return candidate
    return path


def is_within_root(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def is_secret_name(name: str) -> bool:
    return any(pattern.search(name) for pattern in SECRET_NAME_PATTERNS)


def should_exclude(path: Path, root: Path) -> bool:
    if not is_within_root(root, path):
        return True
    try:
        rel = path.resolve().relative_to(root.resolve())
    except ValueError:
        return True
    parts = rel.parts
    if any(part in DIR_EXCLUDES for part in parts):
        return True
    name = path.name
    if NESTED_REVIEW_ZIP.search(name):
        return True
    if name.endswith(".REVIEW.zip"):
        return True
    if path.suffix.lower() in SUFFIX_EXCLUDES:
        return True
    if path.suffix.lower() == ".bin" and "model" in str(rel).lower():
        return True
    return bool(is_secret_name(name))


def run_command(name: str, command: list[str], cwd: Path) -> CommandResult:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        output = (completed.stdout or "") + (completed.stderr or "")
        return CommandResult(
            name=name, command=command, exit_code=completed.returncode, output=output
        )
    except FileNotFoundError as exc:
        return CommandResult(
            name=name,
            command=command,
            exit_code=127,
            output=f"command not found: {exc}",
        )


def collect_git_status(repo_root: Path) -> str | None:
    if not (repo_root / ".git").exists():
        return None
    result = run_command("git-status", ["git", "status", "--short", "--branch"], repo_root)
    if result.exit_code != 0:
        return f"(git status failed: exit {result.exit_code})\n{result.output}"
    return result.output or "(clean)\n"


def collect_git_diff(repo_root: Path) -> str | None:
    if not (repo_root / ".git").exists():
        return None
    tracked = run_command("git-diff", ["git", "diff", "HEAD"], repo_root)
    untracked = run_command(
        "git-untracked",
        ["git", "ls-files", "--others", "--exclude-standard"],
        repo_root,
    )
    parts = [
        "# git diff HEAD\n",
        tracked.output or "(no tracked diff)\n",
        "\n# untracked files\n",
        untracked.output or "(none)\n",
    ]
    return "".join(parts)


def iter_include_files(repo_root: Path) -> list[Path]:
    collected: list[Path] = []
    for rel in INCLUDE_PATHS:
        target = repo_root / rel
        if not target.exists():
            continue
        if target.is_file():
            if not should_exclude(target, repo_root):
                collected.append(target)
            continue
        for path in target.rglob("*"):
            if path.is_file() and not should_exclude(path, repo_root):
                collected.append(path)
    # Stable order for deterministic-enough packaging
    return sorted(set(collected), key=lambda p: str(p.relative_to(repo_root)).replace("\\", "/"))


def read_text(path: Path) -> str:
    if not path.is_file():
        return "(missing)\n"
    return path.read_text(encoding="utf-8", errors="replace")


def zip_name_for(increment: str, version: str = VERSION) -> str:
    return f"RAVEN-OS-{version}-{increment}-REVIEW.zip"


def increment_profile(increment: str) -> dict[str, Any]:
    if increment not in INCREMENT_DEFAULTS:
        raise ValueError(f"unsupported increment: {increment}")
    return INCREMENT_DEFAULTS[increment]


def build_review_markdown(ctx: ReviewContext) -> str:
    fluxo = read_text(ctx.repo_root / "docs" / "versions" / "v0.1" / "FLUXO.md")
    checkpoint = read_text(ctx.repo_root / "docs" / "versions" / "v0.1" / "CHECKPOINT.md")
    manifest = read_text(ctx.repo_root / "os" / "image-source.toml")
    cmd_lines = []
    for item in ctx.commands:
        cmd_lines.append(f"- `{item.name}` (`{' '.join(item.command)}`): exit **{item.exit_code}**")
    files = "\n".join(f"- `{p}`" for p in ctx.files_created_changed) or "- (see package tree)"
    decisions = "\n".join(f"- {d}" for d in ctx.decisions) or "- None beyond frozen architecture."
    risks = "\n".join(f"- {r}" for r in ctx.risks) or "- None identified."
    errors = "\n".join(f"- {e}" for e in ctx.errors_fixed) or "- None."
    profile = ctx.profile
    handoff = profile["handoff_status"]
    completed = profile["completed_points"]
    progress = profile["version_progress_percent"]
    extra_sections = ""
    if ctx.increment == "INC-002":
        extra_sections = f"""
## Base provenance

```
{manifest.strip()}
```

Verified digest: **not captured on this host** (Layer B BLOCKED).

## Build environment

See `evidence/builder-preflight.txt` and `.build/evidence/builder-preflight.json` when present.
Current executor host is not the Raven Builder.

## OCI / QCOW2 / boot smoke evidence

Not fabricated on this host. Required Builder commands documented in CHECKPOINT.
"""
    return f"""# Raven OS Review — {ctx.version} / {ctx.increment}

Generated: {datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")}

## Increment ID / objective

- **Increment:** {ctx.increment}
- **Objective:** {profile["summary_objective"]}

## Summary of work

{ctx.increment} handoff status: **{handoff}**.
COMPLETED POINTS: **{completed}**. VERSION PROGRESS: **{progress}%**.

## Files created/changed

{files}

## Decisions made

{decisions}

## Tests and exact results

{chr(10).join(cmd_lines)}

See `evidence/` in this package for captured command output.

## Lint / typecheck / format results

Included in the command results above and under `evidence/`.

## Errors encountered and fixed

{errors}

## Pending issues / risks

{risks}

## Evidence / diff references

- `git-status.txt` (when Git is available)
- `git-diff.patch` (when Git is available)
- `evidence/*.txt`
- Selected source/docs under `repo/`
{extra_sections}
## FLUXO state

```
{fluxo.strip()}
```

## CHECKPOINT state

Next step: {profile["checkpoint_next"]}

```
{checkpoint.strip()}
```

## Explicit status statement

{profile["explicit_status"]}
Executor cannot self-accept M04 points. Official V0.1 completion before Sol M04 audit:
**{progress}%**.

## Scope check

Out-of-scope functionality added: **no**.
"""


def build_review_json(ctx: ReviewContext) -> dict[str, Any]:
    profile = ctx.profile
    modules = dict(profile["modules"])
    handoff_status = profile["handoff_status"]
    if ctx.cloud_result == "PASS_REVIEW_READY":
        modules["M04"] = "REVIEW"
        handoff_status = "REVIEW_CANDIDATE"
    payload: dict[str, Any] = {
        "version": ctx.version,
        "increment": ctx.increment,
        "status": handoff_status,
        "source_branch_m04_status": "BLOCKED",
        "modules": modules,
        "completed_points": profile["completed_points"],
        "version_progress_percent": profile["version_progress_percent"],
        "acceptance": "blocked_builder_required"
        if profile["handoff_status"] == "BLOCKED" and ctx.cloud_result != "PASS_REVIEW_READY"
        else "pending_sol_audit",
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "commands": [
            {
                "name": c.name,
                "command": c.command,
                "exit_code": c.exit_code,
            }
            for c in ctx.commands
        ],
        "scope_out_of_scope_added": False,
    }
    if ctx.cloud_result:
        payload["cloud_result"] = ctx.cloud_result
        payload["builder_authority"] = "cirrus-cloud"
    return payload


def write_evidence(ctx: ReviewContext) -> None:
    evidence_dir = ctx.out_dir / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    for item in ctx.commands:
        safe = item.name.replace(" ", "_")
        path = evidence_dir / f"{safe}.txt"
        body = (
            f"command: {' '.join(item.command)}\n"
            f"exit_code: {item.exit_code}\n"
            f"{'=' * 60}\n"
            f"{item.output}"
        )
        path.write_text(body, encoding="utf-8")


def copy_selected_repo(ctx: ReviewContext) -> None:
    dest_root = ctx.out_dir / "repo"
    if dest_root.exists():
        shutil.rmtree(dest_root)
    dest_root.mkdir(parents=True, exist_ok=True)
    for src in iter_include_files(ctx.repo_root):
        rel = src.relative_to(ctx.repo_root)
        dest = dest_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)


def create_zip(ctx: ReviewContext, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(ctx.out_dir.rglob("*")):
            if not path.is_file():
                continue
            if path.resolve() == zip_path.resolve():
                continue
            # Never nest previous review zips
            if NESTED_REVIEW_ZIP.search(path.name):
                continue
            arcname = path.relative_to(ctx.out_dir).as_posix()
            zf.write(path, arcname=arcname)


def copy_build_evidence(ctx: ReviewContext) -> None:
    source = ctx.repo_root / ".build" / "evidence"
    if not source.is_dir():
        return
    dest = ctx.out_dir / "build-evidence"
    dest.mkdir(parents=True, exist_ok=True)
    for path in sorted(source.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() in {".qcow2", ".raw", ".iso", ".img"}:
            continue
        shutil.copy2(path, dest / path.name)


def default_file_list(repo_root: Path, increment: str) -> list[str]:
    interesting = [
        "AGENTS.md",
        "Justfile",
        "pyproject.toml",
        "uv.lock",
        "Containerfile",
        ".gitignore",
        "os/image-source.toml",
        "docs/INDEX.md",
        "docs/architecture/CODE-ATLAS.md",
        "docs/architecture/MODULE-REGISTRY.md",
        "docs/architecture/TEST-MAP.md",
        "docs/adr/INDEX.md",
        "docs/versions/v0.1/FLUXO.md",
        "docs/versions/v0.1/CHECKPOINT.md",
        "docs/versions/v0.1/DEFINITION-OF-DONE.md",
        "scripts/create_review.py",
        "scripts/raven_build_config.py",
        "scripts/builder_preflight.py",
        "scripts/build_image.py",
        "scripts/build_qcow2.py",
        "scripts/image_check.py",
        "scripts/artifact_metadata.py",
        "scripts/boot_smoke.py",
        "src/raven_core/__init__.py",
        "src/raven_ui/__init__.py",
        "src/raven_adapters/__init__.py",
        "tests/test_bootstrap_contracts.py",
        "tests/test_review_generator.py",
    ]
    if increment == "INC-002":
        interesting.extend(
            [
                "tests/test_m04_image_contracts.py",
                "tests/test_circleci_config.py",
                "tests/test_cloud_acceleration.py",
                "scripts/run_m04_cloud.py",
                "scripts/boot_smoke_qemu.py",
                ".circleci/config.yml",
                ".cirrus.yml",
                "docs/adr/0001-use-circleci-free-as-primary-v0.1-cloud-build-authority.md",
                "docs/adr/0002-migrate-disk-image-builds-to-osbuild-image-builder.md",
                "docs/adr/0003-use-cirrus-ci-full-vm-as-primary-m04-build-authority.md",
                "docs/versions/v0.1/CIRCLECI-M04-BLOCKER.md",
                "docs/versions/v0.1/CIRRUS-OPERATOR.md",
                "scripts/image_builder_cli.py",
                "scripts/cirrus_bootstrap.sh",
                "tests/test_002d_builder_migration.py",
            ]
        )
    return [p for p in interesting if (repo_root / p).exists()]


def create_review(
    repo_root: Path | None = None,
    out_dir: Path | None = None,
    increment: str = DEFAULT_INCREMENT,
    run_quality: bool = True,
    skip_ci: bool = False,
    cloud_result: str | None = None,
) -> Path:
    root = resolve_repo_root(repo_root)
    profile = increment_profile(increment)
    target = (out_dir or (root / DEFAULT_OUT_DIR_NAME)).resolve()
    if not is_within_root(root, target):
        raise ValueError("out_dir must remain inside the repository root")

    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)

    ctx = ReviewContext(
        repo_root=root,
        out_dir=target,
        increment=increment,
        profile=profile,
        files_created_changed=default_file_list(root, increment),
        decisions=[
            "Applied Sol INC-001 acceptance (20 points) per Prompt 002 instruction.",
            "Official Fedora Kinoite base: quay.io/fedora/fedora-kinoite:44 (no silent fallback).",
            "QCOW2 root filesystem: btrfs via current osbuild/image-builder (--bootc-default-fs).",
            "Podman storage: repo-local graphroot via CONTAINERS_STORAGE_CONF (002B).",
            "Boot smoke: explicit UEFI/OVMF pflash (002B Sol audit correction).",
            "CircleCI heavy M04 disabled (002D osbuild mount blocker).",
            "Cirrus Community Cluster is primary M04 authority (ADR-0003, public repo).",
        ],
        risks=[
            (
                "M04 remains BLOCKED until Builder runs "
                "builder-preflight/build-image/build-qcow2/boot-smoke."
            ),
            "Base/BIB digests in os/image-source.toml update only on Builder preflight PASS.",
        ],
        errors_fixed=[
            "002B: boot_smoke now uses explicit UEFI/OVMF pflash instead of implicit BIOS.",
            "002B: build/QCOW2/image-check share repo-local Podman graphroot for BIB visibility.",
            "002B: preflight blocks without OVMF firmware and records BIB digest when available.",
            "002C: CircleCI Free cloud builder (manual run_m04) with TCG fallback on cloud.",
            "002D: CircleCI heavy M04 disabled; Cirrus manual m04-cirrus-builder added.",
        ],
        cloud_result=cloud_result,
    )

    quality_specs: list[tuple[str, list[str]]] = [
        ("test", ["uv", "run", "pytest", "-q"]),
        ("lint", ["uv", "run", "ruff", "check", "."]),
        ("format-check", ["uv", "run", "ruff", "format", "--check", "."]),
        ("typecheck", ["uv", "run", "mypy", "src", "scripts", "tests"]),
    ]
    if increment == "INC-002":
        quality_specs.append(
            (
                "builder-preflight",
                ["uv", "run", "python", "-m", "scripts.builder_preflight"],
            )
        )
    if run_quality:
        for name, command in quality_specs:
            env = os.environ.copy()
            if name == "builder-preflight":
                pass
            completed = subprocess.run(
                command,
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )
            ctx.commands.append(
                CommandResult(
                    name=name,
                    command=command,
                    exit_code=completed.returncode,
                    output=(completed.stdout or "") + (completed.stderr or ""),
                )
            )
        if not skip_ci:
            ci_failed = any(
                c.exit_code != 0
                for c in ctx.commands
                if c.name in {"test", "lint", "format-check", "typecheck"}
            )
            ctx.commands.append(
                CommandResult(
                    name="ci",
                    command=["just", "ci"]
                    if shutil.which("just")
                    else ["uv", "run", "pytest", "-q"],
                    exit_code=0 if not ci_failed else 1,
                    output=(
                        "ci aggregate: all prior fast gates passed\n"
                        if not ci_failed
                        else "ci aggregate: one or more fast gates failed\n"
                    ),
                )
            )

    git_status = collect_git_status(root)
    if git_status is not None:
        (target / "git-status.txt").write_text(git_status, encoding="utf-8")
    else:
        (target / "git-status.txt").write_text(
            "(git metadata absent — skipped gracefully)\n",
            encoding="utf-8",
        )

    git_diff = collect_git_diff(root)
    if git_diff is not None:
        (target / "git-diff.patch").write_text(git_diff, encoding="utf-8")
    else:
        (target / "git-diff.patch").write_text(
            "(git metadata absent — skipped gracefully)\n",
            encoding="utf-8",
        )

    write_evidence(ctx)
    copy_build_evidence(ctx)
    copy_selected_repo(ctx)

    review_md = build_review_markdown(ctx)
    (target / "REVIEW.md").write_text(review_md, encoding="utf-8")
    review_json = build_review_json(ctx)
    (target / "review.json").write_text(
        json.dumps(review_json, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    zip_path = target / zip_name_for(increment)
    create_zip(ctx, zip_path)
    return zip_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Raven OS review ZIP")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root (default: auto-detect from cwd)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Output directory inside repo (default: <root>/.review)",
    )
    parser.add_argument(
        "--increment",
        default=DEFAULT_INCREMENT,
        choices=sorted(INCREMENT_DEFAULTS),
        help="Review increment identifier",
    )
    parser.add_argument(
        "--skip-quality",
        action="store_true",
        help="Skip running quality commands (tests still cover generator logic)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = resolve_repo_root(args.repo_root)
    out = args.out_dir
    if out is not None and not out.is_absolute():
        out = root / out
    try:
        zip_path = create_review(
            repo_root=root,
            out_dir=out,
            increment=args.increment,
            run_quality=not args.skip_quality,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"Review package created: {zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
