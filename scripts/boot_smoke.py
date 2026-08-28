#!/usr/bin/env python3
"""Bounded UEFI VM boot smoke for generated QCOW2 (M04 Layer B)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from scripts.boot_smoke_qemu import build_qemu_uefi_command
from scripts.boot_smoke_runner import (
    CLASSIFICATION_LAUNCH_ERROR,
    CLASSIFICATION_PASS,
    attempt_to_dict,
    run_boot_attempt,
)
from scripts.qcow2_preboot import write_qcow2_preboot_evidence
from scripts.raven_build_config import (
    UefiFirmware,
    build_paths,
    command_exists,
    is_cloud_builder,
    is_linux_x86_64,
    iter_ovmf_firmware_candidates,
    platform_summary,
    resolve_acceleration,
)
from scripts.uefi_preboot import UefiPrebootResult, write_uefi_preboot_evidence

MAX_BOOT_ATTEMPTS = 3


def resolve_timeout_seconds(explicit: int | None) -> int:
    if explicit is not None:
        if explicit <= 0:
            raise ValueError("timeout_seconds must be positive")
        return explicit
    return 300 if is_cloud_builder() else 120


def _firmware_for_pair(
    code: Path,
    vars_template: Path,
    evidence_dir: Path,
    attempt: int,
) -> UefiFirmware:
    import shutil

    runtime = evidence_dir / f"OVMF_VARS.runtime.attempt{attempt}.fd"
    shutil.copy2(vars_template, runtime)
    return UefiFirmware(
        code_path=code,
        vars_template_path=vars_template,
        vars_runtime_path=runtime,
        candidate_label=f"{code} + {vars_template}",
    )


def _firmware_attempts(uefi_result: UefiPrebootResult, evidence_dir: Path) -> list[UefiFirmware]:
    attempts = []
    seen: set[str] = set()
    if uefi_result.firmware is not None:
        attempts.append(uefi_result.firmware)
        seen.add(uefi_result.firmware.candidate_label)
    for code, vars_template in iter_ovmf_firmware_candidates():
        label = f"{code} + {vars_template}"
        if label in seen:
            continue
        if not code.is_file() or not vars_template.is_file():
            continue
        seen.add(label)
        attempts.append(_firmware_for_pair(code, vars_template, evidence_dir, len(attempts) + 1))
        if len(attempts) >= MAX_BOOT_ATTEMPTS:
            break
    return attempts


def boot_smoke(repo_root: Path | None = None, timeout_seconds: int | None = None) -> int:
    paths = build_paths(repo_root)
    try:
        effective_timeout = resolve_timeout_seconds(timeout_seconds)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if not is_linux_x86_64():
        print("error: boot-smoke requires Linux x86_64 Raven Builder", file=sys.stderr)
        return 2
    if not command_exists("qemu-system-x86_64"):
        print("error: qemu-system-x86_64 is required", file=sys.stderr)
        return 2

    qcow2_files = sorted(paths.qcow2_dir.glob("*.qcow2"), key=lambda p: p.stat().st_mtime)
    if not qcow2_files:
        print("error: no QCOW2 artifact found; run just build-qcow2 first", file=sys.stderr)
        return 1

    qcow2 = qcow2_files[-1]
    qcow2_stat_before = qcow2.stat()
    qcow2_mtime_before = qcow2_stat_before.st_mtime
    qcow2_size_before = qcow2_stat_before.st_size

    preboot = write_qcow2_preboot_evidence(qcow2, paths)
    if not preboot.ok:
        print(f"error: QCOW2 preboot failed: {preboot.error}", file=sys.stderr)
        return 1

    uefi_result = write_uefi_preboot_evidence(paths.evidence_dir)
    if not uefi_result.ok or uefi_result.firmware is None:
        print(f"error: UEFI preboot failed: {uefi_result.error}", file=sys.stderr)
        return 2

    paths.evidence_dir.mkdir(parents=True, exist_ok=True)
    serial_log = paths.evidence_dir / "boot-smoke-serial.log"
    stdout_log = paths.evidence_dir / "qemu-stdout.log"
    stderr_log = paths.evidence_dir / "qemu-stderr.log"
    accel = resolve_acceleration()

    attempt_records: list[dict[str, Any]] = []
    final_classification = CLASSIFICATION_LAUNCH_ERROR
    passed = False
    observed_guest: list[str] = []

    firmware_candidates = _firmware_attempts(uefi_result, paths.evidence_dir)
    for index, firmware in enumerate(firmware_candidates[:MAX_BOOT_ATTEMPTS], start=1):
        attempt_serial = paths.evidence_dir / f"boot-smoke-serial-attempt{index}.log"
        attempt_stdout = paths.evidence_dir / f"qemu-stdout-attempt{index}.log"
        attempt_stderr = paths.evidence_dir / f"qemu-stderr-attempt{index}.log"

        command = build_qemu_uefi_command(
            qcow2=qcow2,
            firmware=firmware,
            serial_log=attempt_serial,
            acceleration=accel,
        )
        result = run_boot_attempt(
            command,
            cwd=paths.repo_root,
            serial_log=attempt_serial,
            stdout_log=attempt_stdout,
            stderr_log=attempt_stderr,
            timeout_seconds=effective_timeout,
        )
        record = attempt_to_dict(
            attempt=index,
            command=command,
            firmware_label=firmware.candidate_label,
            acceleration=accel,
            result=result,
        )
        attempt_records.append(record)
        final_classification = result.classification

        if result.classification == CLASSIFICATION_PASS:
            passed = True
            observed_guest = result.guest_markers
            if attempt_serial.exists():
                serial_log.write_bytes(attempt_serial.read_bytes())
            if attempt_stdout.exists():
                stdout_log.write_bytes(attempt_stdout.read_bytes())
            if attempt_stderr.exists():
                stderr_log.write_bytes(attempt_stderr.read_bytes())
            break

        # Attempt 2+ only for launch-level errors (not guest timeout).
        if result.classification != CLASSIFICATION_LAUNCH_ERROR:
            break

    qcow2_stat_after = qcow2.stat()
    base_unmodified = (
        qcow2_stat_after.st_mtime == qcow2_mtime_before
        and qcow2_stat_after.st_size == qcow2_size_before
    )

    evidence = {
        "architecture": "x86_64",
        "uefi_firmware_code": str(uefi_result.firmware.code_path) if uefi_result.firmware else "",
        "uefi_firmware_vars_template": (
            str(uefi_result.firmware.vars_template_path) if uefi_result.firmware else ""
        ),
        "uefi_candidate": uefi_result.firmware.candidate_label if uefi_result.firmware else "",
        "acceleration": accel,
        "timeout_seconds": effective_timeout,
        "disk_mode": "snapshot",
        "base_qcow2_unmodified": base_unmodified,
        "attempts": attempt_records,
        "final_classification": final_classification,
        "observed_guest_markers": observed_guest,
        "platform": platform_summary(),
        "boot_mode": "uefi-ovmf",
        "serial_console_kargs": "console=tty0 console=ttyS0,115200n8",
    }
    (paths.evidence_dir / "boot-smoke-evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (paths.evidence_dir / "boot-smoke.log").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if not passed:
        last = attempt_records[-1] if attempt_records else {}
        if final_classification == CLASSIFICATION_LAUNCH_ERROR:
            summary = last.get("stderr_summary") or "QEMU exited during launch grace window"
            print(
                f"error: QEMU launch failure ({final_classification}): {summary}", file=sys.stderr
            )
        elif final_classification == "BOOT_OBSERVABILITY_TIMEOUT":
            print(
                f"error: boot smoke timed out without guest markers ({final_classification})",
                file=sys.stderr,
            )
        else:
            print(
                "error: boot smoke did not observe guest-level serial markers",
                file=sys.stderr,
            )
        return 1

    print(
        f"boot-smoke: PASS (guest markers={','.join(observed_guest)}; "
        f"acceleration={accel}; snapshot=yes)"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="QCOW2 UEFI boot smoke")
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=None,
        help="Boot timeout override (omit for environment default: 300 cloud / 120 local)",
    )
    args = parser.parse_args(argv)
    return boot_smoke(args.repo_root, args.timeout_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
