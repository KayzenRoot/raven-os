#!/usr/bin/env python3
"""Create M04 failure diagnostic ZIP (no QCOW2/OCI/secrets)."""

from __future__ import annotations

import argparse
import json
import subprocess
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from scripts.raven_build_config import build_paths, resolve_repo_root

DIAGNOSTICS_NAME = "RAVEN-OS-V0.1-INC-002-DIAGNOSTICS.zip"
FORBIDDEN_SUFFIXES = frozenset({".qcow2", ".raw", ".vmdk", ".vhd", ".vhdx", ".iso", ".img"})


def _git_output(args: list[str], cwd: Path) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return (completed.stdout or completed.stderr or "").strip()


def _collect_evidence_files(evidence_dir: Path) -> list[Path]:
    if not evidence_dir.is_dir():
        return []
    patterns = (
        "run-m04-cloud.json",
        "cloud-gate-*.txt",
        "builder-preflight*",
        "image-check*",
        "artifact-metadata.json",
        "qcow2-preboot.json",
        "uefi-preboot.json",
        "qemu-stdout.log",
        "qemu-stderr.log",
        "boot-smoke-serial.log",
        "boot-smoke-evidence.json",
        "boot-smoke.log",
        "build-qcow2.log",
        "image-builder-digest.txt",
        "image-builder-help.txt",
        "podman-storage.json",
    )
    collected: list[Path] = []
    for pattern in patterns:
        collected.extend(sorted(evidence_dir.glob(pattern)))
    return [path for path in collected if path.is_file()]


def _safe_add(zipf: zipfile.ZipFile, source: Path, arcname: str) -> None:
    if source.suffix.lower() in FORBIDDEN_SUFFIXES:
        return
    if source.is_file():
        zipf.write(source, arcname)


def create_diagnostics(repo_root: Path | None = None) -> Path:
    paths = build_paths(repo_root)
    out_dir = paths.repo_root / ".review"
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / DIAGNOSTICS_NAME

    manifest = {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_sha": _git_output(["rev-parse", "HEAD"], paths.repo_root),
        "git_status": _git_output(["status", "--short", "--branch"], paths.repo_root),
    }

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr("diagnostics-manifest.json", json.dumps(manifest, indent=2) + "\n")

        for rel in (
            "docs/versions/v0.1/FLUXO.md",
            "docs/versions/v0.1/CHECKPOINT.md",
            "scripts/boot_smoke.py",
            "scripts/boot_smoke_qemu.py",
            "scripts/boot_smoke_runner.py",
            "scripts/qcow2_preboot.py",
            "scripts/uefi_preboot.py",
            "os/image-builder-config.toml",
        ):
            source = paths.repo_root / rel
            if source.is_file():
                zipf.write(source, rel)

        for evidence in _collect_evidence_files(paths.evidence_dir):
            arc = f"evidence/{evidence.name}"
            _safe_add(zipf, evidence, arc)

    return zip_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create M04 diagnostics ZIP")
    parser.add_argument("--repo-root", type=Path, default=None)
    args = parser.parse_args(argv)
    root = resolve_repo_root(args.repo_root)
    zip_path = create_diagnostics(root)
    print(f"diagnostics: {zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
