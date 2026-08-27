#!/usr/bin/env python3
"""Bounded UEFI VM boot smoke for generated QCOW2 (M04 Layer B)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from scripts.boot_smoke_qemu import build_qemu_uefi_command
from scripts.raven_build_config import (
    build_paths,
    command_exists,
    detect_uefi_firmware,
    ensure_within_build_root,
    is_linux_x86_64,
    platform_summary,
    resolve_acceleration,
)


def evaluate_serial_log(serial_text: str) -> tuple[bool, list[str]]:
    markers = ("Fedora", "systemd", "Linux version", "Kinoite", "EFI")
    observed = [marker for marker in markers if marker in serial_text]
    return bool(observed), observed


def boot_smoke(repo_root: Path | None = None, timeout_seconds: int = 120) -> int:
    paths = build_paths(repo_root)
    if not is_linux_x86_64():
        print("error: boot-smoke requires Linux x86_64 Raven Builder", file=sys.stderr)
        return 2
    if not command_exists("qemu-system-x86_64"):
        print("error: qemu-system-x86_64 is required", file=sys.stderr)
        return 2

    firmware = detect_uefi_firmware(paths.evidence_dir)
    if firmware is None:
        print("error: no usable UEFI/OVMF firmware found on Builder", file=sys.stderr)
        return 2

    qcow2_files = sorted(paths.qcow2_dir.glob("*.qcow2"), key=lambda p: p.stat().st_mtime)
    if not qcow2_files:
        print("error: no QCOW2 artifact found; run just build-qcow2 first", file=sys.stderr)
        return 1

    qcow2 = ensure_within_build_root(paths, qcow2_files[-1])
    paths.evidence_dir.mkdir(parents=True, exist_ok=True)
    serial_log = paths.evidence_dir / "boot-smoke-serial.log"
    if serial_log.exists():
        serial_log.unlink()

    accel = resolve_acceleration()
    command = build_qemu_uefi_command(
        qcow2=qcow2,
        firmware=firmware,
        serial_log=serial_log,
        acceleration=accel,
    )

    timed_out = False
    exit_code = 0
    stdout = ""
    stderr = ""
    try:
        completed = subprocess.run(
            command,
            cwd=paths.repo_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
        exit_code = int(completed.returncode)
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = 124
        stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
        stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""

    serial_text = (
        serial_log.read_text(encoding="utf-8", errors="replace") if serial_log.exists() else ""
    )
    passed, observed_markers = evaluate_serial_log(serial_text)

    evidence = {
        "architecture": "x86_64",
        "uefi_firmware_code": str(firmware.code_path),
        "uefi_firmware_vars_template": str(firmware.vars_template_path),
        "uefi_firmware_vars_runtime": str(firmware.vars_runtime_path),
        "uefi_candidate": firmware.candidate_label,
        "qemu_command": command,
        "acceleration": accel,
        "timeout_seconds": timeout_seconds,
        "timed_out": timed_out,
        "qemu_exit_code": exit_code,
        "serial_log": str(serial_log),
        "observed_markers": observed_markers,
        "platform": platform_summary(),
        "boot_mode": "uefi-ovmf",
    }
    (paths.evidence_dir / "boot-smoke-evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (paths.evidence_dir / "boot-smoke.log").write_text(
        f"command: {' '.join(command)}\n"
        f"exit_code: {exit_code}\n"
        f"timeout_seconds: {timeout_seconds}\n"
        f"timed_out: {timed_out}\n"
        f"uefi_firmware: {firmware.candidate_label}\n"
        f"acceleration: {accel}\n"
        f"observed_markers: {', '.join(observed_markers) or 'none'}\n"
        f"{'=' * 60}\n"
        f"{stdout}\n{stderr}",
        encoding="utf-8",
    )

    if not passed:
        print(
            "error: boot smoke did not observe expected UEFI boot markers in serial log",
            file=sys.stderr,
        )
        return 1

    print(
        f"boot-smoke: PASS (bounded UEFI/OVMF serial boot markers observed; acceleration={accel})"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="QCOW2 UEFI boot smoke")
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    args = parser.parse_args(argv)
    return boot_smoke(args.repo_root, args.timeout_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
