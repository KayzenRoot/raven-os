#!/usr/bin/env python3
"""Observable QEMU process control for M04 boot smoke."""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.boot_smoke_markers import evaluate_serial_log

CLASSIFICATION_PASS = "BOOT_GUEST_MARKER_OBSERVED"
CLASSIFICATION_LAUNCH_ERROR = "QEMU_LAUNCH_ERROR"
CLASSIFICATION_TIMEOUT = "BOOT_OBSERVABILITY_TIMEOUT"
CLASSIFICATION_NO_MARKERS = "BOOT_NO_GUEST_MARKERS"

DEFAULT_LAUNCH_GRACE_SECONDS = 8.0
DEFAULT_POLL_INTERVAL_SECONDS = 1.0


@dataclass
class BootAttemptResult:
    classification: str
    exit_code: int | None
    process_lifetime_seconds: float
    timed_out: bool
    guest_markers: list[str] = field(default_factory=list)
    firmware_markers: list[str] = field(default_factory=list)
    serial_bytes: int = 0
    qemu_stdout_path: str = ""
    qemu_stderr_path: str = ""
    serial_log_path: str = ""
    stderr_summary: str = ""


def _read_tail(path: Path, max_bytes: int = 8192) -> str:
    if not path.is_file():
        return ""
    data = path.read_bytes()
    if len(data) > max_bytes:
        data = data[-max_bytes:]
    return data.decode("utf-8", errors="replace")


def _process_exit_code(process: subprocess.Popen[str]) -> int:
    code = process.poll()
    return int(code if code is not None else 0)


def _terminate_process(process: subprocess.Popen[str], *, grace_seconds: float = 5.0) -> int:
    if process.poll() is not None:
        return _process_exit_code(process)
    process.terminate()
    deadline = time.monotonic() + grace_seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            return _process_exit_code(process)
        time.sleep(0.2)
    process.kill()
    process.wait(timeout=5)
    return _process_exit_code(process)


def run_boot_attempt(
    command: list[str],
    *,
    cwd: Path,
    serial_log: Path,
    stdout_log: Path,
    stderr_log: Path,
    timeout_seconds: int,
    launch_grace_seconds: float = DEFAULT_LAUNCH_GRACE_SECONDS,
    poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
) -> BootAttemptResult:
    serial_log.parent.mkdir(parents=True, exist_ok=True)
    if serial_log.exists():
        serial_log.unlink()
    stdout_log.parent.mkdir(parents=True, exist_ok=True)
    stderr_log.parent.mkdir(parents=True, exist_ok=True)

    start = time.monotonic()
    with (
        stdout_log.open("w", encoding="utf-8") as stdout_handle,
        stderr_log.open("w", encoding="utf-8") as stderr_handle,
    ):
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=stdout_handle,
            stderr=stderr_handle,
            text=True,
        )

        # Launch grace: detect immediate QEMU exit (disk/firmware errors).
        grace_deadline = start + launch_grace_seconds
        while time.monotonic() < grace_deadline:
            if process.poll() is not None:
                lifetime = time.monotonic() - start
                stderr_summary = _read_tail(stderr_log)
                if stderr_summary.strip():
                    print(stderr_summary, end="", flush=True)
                return BootAttemptResult(
                    classification=CLASSIFICATION_LAUNCH_ERROR,
                    exit_code=_process_exit_code(process),
                    process_lifetime_seconds=round(lifetime, 3),
                    timed_out=False,
                    serial_bytes=serial_log.stat().st_size if serial_log.exists() else 0,
                    qemu_stdout_path=str(stdout_log),
                    qemu_stderr_path=str(stderr_log),
                    serial_log_path=str(serial_log),
                    stderr_summary=stderr_summary.strip(),
                )
            time.sleep(0.25)

        deadline = start + timeout_seconds
        while time.monotonic() < deadline:
            serial_text = (
                serial_log.read_text(encoding="utf-8", errors="replace")
                if serial_log.exists()
                else ""
            )
            passed, guest, firmware = evaluate_serial_log(serial_text)
            if passed:
                exit_code = _terminate_process(process)
                return BootAttemptResult(
                    classification=CLASSIFICATION_PASS,
                    exit_code=exit_code,
                    process_lifetime_seconds=round(time.monotonic() - start, 3),
                    timed_out=False,
                    guest_markers=guest,
                    firmware_markers=firmware,
                    serial_bytes=len(serial_text.encode("utf-8", errors="replace")),
                    qemu_stdout_path=str(stdout_log),
                    qemu_stderr_path=str(stderr_log),
                    serial_log_path=str(serial_log),
                )
            if process.poll() is not None:
                lifetime = time.monotonic() - start
                stderr_summary = _read_tail(stderr_log)
                serial_text = (
                    serial_log.read_text(encoding="utf-8", errors="replace")
                    if serial_log.exists()
                    else ""
                )
                _, guest, firmware = evaluate_serial_log(serial_text)
                if guest:
                    return BootAttemptResult(
                        classification=CLASSIFICATION_PASS,
                        exit_code=_process_exit_code(process),
                        process_lifetime_seconds=round(lifetime, 3),
                        timed_out=False,
                        guest_markers=guest,
                        firmware_markers=firmware,
                        serial_bytes=len(serial_text.encode("utf-8", errors="replace")),
                        qemu_stdout_path=str(stdout_log),
                        qemu_stderr_path=str(stderr_log),
                        serial_log_path=str(serial_log),
                    )
                return BootAttemptResult(
                    classification=CLASSIFICATION_LAUNCH_ERROR
                    if lifetime < launch_grace_seconds
                    else CLASSIFICATION_NO_MARKERS,
                    exit_code=_process_exit_code(process),
                    process_lifetime_seconds=round(lifetime, 3),
                    timed_out=False,
                    firmware_markers=firmware,
                    serial_bytes=len(serial_text.encode("utf-8", errors="replace")),
                    qemu_stdout_path=str(stdout_log),
                    qemu_stderr_path=str(stderr_log),
                    serial_log_path=str(serial_log),
                    stderr_summary=stderr_summary.strip(),
                )
            time.sleep(poll_interval_seconds)

        # Timeout with QEMU still running.
        stderr_summary = _read_tail(stderr_log)
        serial_text = (
            serial_log.read_text(encoding="utf-8", errors="replace") if serial_log.exists() else ""
        )
        exit_code = _terminate_process(process)
        _, guest, firmware = evaluate_serial_log(serial_text)
        return BootAttemptResult(
            classification=CLASSIFICATION_TIMEOUT,
            exit_code=exit_code,
            process_lifetime_seconds=round(time.monotonic() - start, 3),
            timed_out=True,
            guest_markers=guest,
            firmware_markers=firmware,
            serial_bytes=len(serial_text.encode("utf-8", errors="replace")),
            qemu_stdout_path=str(stdout_log),
            qemu_stderr_path=str(stderr_log),
            serial_log_path=str(serial_log),
            stderr_summary=stderr_summary.strip(),
        )


def attempt_to_dict(
    *,
    attempt: int,
    command: list[str],
    firmware_label: str,
    acceleration: str,
    result: BootAttemptResult,
) -> dict[str, Any]:
    return {
        "attempt": attempt,
        "classification": result.classification,
        "qemu_command": command,
        "firmware_pair": firmware_label,
        "acceleration": acceleration,
        "disk_mode": "snapshot",
        "process_lifetime_seconds": result.process_lifetime_seconds,
        "qemu_exit_code": result.exit_code,
        "timed_out": result.timed_out,
        "guest_markers": result.guest_markers,
        "firmware_markers": result.firmware_markers,
        "serial_bytes": result.serial_bytes,
        "qemu_stdout": result.qemu_stdout_path,
        "qemu_stderr": result.qemu_stderr_path,
        "serial_log": result.serial_log_path,
        "stderr_summary": result.stderr_summary,
    }
