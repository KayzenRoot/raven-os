#!/usr/bin/env python3
"""Guest vs firmware boot marker evaluation for M04 boot smoke."""

from __future__ import annotations

FIRMWARE_MARKERS: tuple[str, ...] = ("EFI",)

GUEST_MARKERS: tuple[str, ...] = (
    "Linux version",
    "systemd",
    "Welcome to Fedora",
    "Fedora Linux",
    "Kinoite",
)


def evaluate_serial_log(serial_text: str) -> tuple[bool, list[str], list[str]]:
    """Return (passed, guest_markers, firmware_markers).

    M04 PASS requires at least one guest-level marker. Firmware-only output fails.
    """
    guest = [marker for marker in GUEST_MARKERS if marker in serial_text]
    firmware = [marker for marker in FIRMWARE_MARKERS if marker in serial_text]
    return bool(guest), guest, firmware
