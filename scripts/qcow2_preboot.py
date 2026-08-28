#!/usr/bin/env python3
"""Static QCOW2 validation before QEMU boot smoke (M04 Layer B)."""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.raven_build_config import (
    BuildPaths,
    build_paths,
    command_exists,
    ensure_within_build_root,
)


@dataclass(frozen=True)
class Qcow2PrebootResult:
    ok: bool
    error: str | None
    evidence: dict[str, Any]


def _file_owner_group(path: Path) -> tuple[int, int, str, str]:
    st = path.stat()
    uid = st.st_uid
    gid = st.st_gid
    user = str(uid)
    group = str(gid)
    try:
        import pwd

        user = pwd.getpwuid(uid).pw_name  # type: ignore[attr-defined]
    except (ImportError, KeyError):
        pass
    try:
        import grp

        group = grp.getgrgid(gid).gr_name  # type: ignore[attr-defined]
    except (ImportError, KeyError):
        pass
    return uid, gid, user, group


def _qcow2_sha256_from_metadata(paths: BuildPaths, qcow2: Path) -> str | None:
    metadata_path = paths.evidence_dir / "artifact-metadata.json"
    if not metadata_path.is_file():
        return None
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    rel = qcow2.resolve().relative_to(paths.repo_root.resolve()).as_posix()
    for artifact in payload.get("artifacts", []):
        artifact_path = str(artifact.get("path", "")).replace("\\", "/")
        if artifact_path == rel:
            return str(artifact.get("sha256", "")) or None
    return None


def _run_qemu_img(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["qemu-img", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def validate_qcow2_preboot(
    qcow2: Path,
    paths: BuildPaths | None = None,
) -> Qcow2PrebootResult:
    paths = paths or build_paths()
    evidence: dict[str, Any] = {"path": str(qcow2)}

    if not qcow2.is_file():
        return Qcow2PrebootResult(False, f"QCOW2 not found: {qcow2}", evidence)

    try:
        resolved = ensure_within_build_root(paths, qcow2)
    except ValueError as exc:
        return Qcow2PrebootResult(False, str(exc), evidence)

    if not os.access(resolved, os.R_OK):
        return Qcow2PrebootResult(False, f"QCOW2 not readable: {resolved}", evidence)

    size_bytes = resolved.stat().st_size
    evidence["size_bytes"] = size_bytes
    if size_bytes <= 0:
        return Qcow2PrebootResult(False, "QCOW2 size is zero", evidence)

    uid, gid, user, group = _file_owner_group(resolved)
    mode = stat.S_IMODE(resolved.stat().st_mode)
    writable = os.access(resolved, os.W_OK)
    evidence.update(
        {
            "owner_uid": uid,
            "owner_user": user,
            "group_gid": gid,
            "group": group,
            "mode_octal": oct(mode),
            "readable": True,
            "writable_by_current_user": writable,
        }
    )

    sha256 = _qcow2_sha256_from_metadata(paths, resolved)
    if sha256:
        evidence["sha256"] = sha256

    if not command_exists("qemu-img"):
        return Qcow2PrebootResult(False, "qemu-img is required for QCOW2 preboot", evidence)

    info = _run_qemu_img(["info", "--output=json", str(resolved)], paths.repo_root)
    if info.returncode != 0:
        return Qcow2PrebootResult(
            False,
            f"qemu-img info failed: {(info.stderr or info.stdout).strip()}",
            evidence,
        )

    info_payload = json.loads(info.stdout)
    evidence["qemu_img_info"] = info_payload
    if info_payload.get("format") != "qcow2":
        return Qcow2PrebootResult(
            False,
            f"expected qcow2 format, got {info_payload.get('format')!r}",
            evidence,
        )

    check = _run_qemu_img(["check", str(resolved)], paths.repo_root)
    evidence["qemu_img_check_exit_code"] = check.returncode
    evidence["qemu_img_check_output"] = (check.stdout or "") + (check.stderr or "")
    # qemu-img check: 0 = no errors; 1 = leaks/corruption (blocking per PDF)
    if check.returncode != 0:
        return Qcow2PrebootResult(
            False,
            f"qemu-img check failed (exit {check.returncode})",
            evidence,
        )

    return Qcow2PrebootResult(True, None, evidence)


def write_qcow2_preboot_evidence(
    qcow2: Path,
    paths: BuildPaths | None = None,
) -> Qcow2PrebootResult:
    paths = paths or build_paths()
    paths.evidence_dir.mkdir(parents=True, exist_ok=True)
    result = validate_qcow2_preboot(qcow2, paths)
    out = paths.evidence_dir / "qcow2-preboot.json"
    payload = {"ok": result.ok, "error": result.error, **result.evidence}
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="QCOW2 pre-boot validation")
    parser.add_argument("qcow2", type=Path, nargs="?", default=None)
    parser.add_argument("--repo-root", type=Path, default=None)
    args = parser.parse_args(argv)
    paths = build_paths(args.repo_root)
    if args.qcow2 is None:
        candidates = sorted(paths.qcow2_dir.glob("*.qcow2"), key=lambda p: p.stat().st_mtime)
        if not candidates:
            print("error: no QCOW2 found", file=sys.stderr)
            return 1
        qcow2 = candidates[-1]
    else:
        qcow2 = args.qcow2
    result = write_qcow2_preboot_evidence(qcow2, paths)
    if not result.ok:
        print(f"error: {result.error}", file=sys.stderr)
        return 1
    print(f"qcow2-preboot: PASS ({qcow2})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
