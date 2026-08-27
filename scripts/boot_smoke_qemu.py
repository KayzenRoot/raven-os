#!/usr/bin/env python3
"""Build bounded UEFI QEMU command lines for M04 boot smoke."""

from __future__ import annotations

from pathlib import Path

from scripts.raven_build_config import UefiFirmware, resolve_acceleration


def build_qemu_uefi_command(
    *,
    qcow2: Path,
    firmware: UefiFirmware,
    serial_log: Path,
    acceleration: str | None = None,
    memory_mib: int = 4096,
    smp: int = 2,
) -> list[str]:
    accel = acceleration or resolve_acceleration()
    return [
        "qemu-system-x86_64",
        "-machine",
        f"q35,accel={accel}",
        "-cpu",
        "host" if accel == "kvm" else "max",
        "-m",
        str(memory_mib),
        "-smp",
        str(smp),
        "-drive",
        f"if=pflash,format=raw,readonly=on,file={firmware.code_path}",
        "-drive",
        f"if=pflash,format=raw,file={firmware.vars_runtime_path}",
        "-drive",
        f"file={qcow2},format=qcow2,if=virtio",
        "-serial",
        f"file:{serial_log}",
        "-display",
        "none",
        "-no-reboot",
    ]
