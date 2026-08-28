"""Cloud acceleration and UEFI boot smoke unit contracts."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from scripts.boot_smoke_qemu import build_qemu_uefi_command
from scripts.raven_build_config import (
    UefiFirmware,
    acceleration_blocker,
    resolve_acceleration,
)


def _firmware(tmp_path: Path) -> UefiFirmware:
    code = tmp_path / "OVMF_CODE.fd"
    vars_template = tmp_path / "OVMF_VARS.fd"
    runtime = tmp_path / "OVMF_VARS.runtime.fd"
    code.write_bytes(b"code")
    vars_template.write_bytes(b"vars")
    runtime.write_bytes(b"vars")
    return UefiFirmware(
        code_path=code,
        vars_template_path=vars_template,
        vars_runtime_path=runtime,
        candidate_label="test",
    )


def test_resolve_acceleration_tcg_without_kvm() -> None:
    with patch("scripts.raven_build_config.kvm_device_present", return_value=False):
        assert resolve_acceleration() == "tcg"


def test_resolve_acceleration_tcg_on_cloud_even_with_kvm() -> None:
    with (
        patch("scripts.raven_build_config.is_cloud_builder", return_value=True),
        patch("scripts.raven_build_config.kvm_device_present", return_value=True),
    ):
        assert resolve_acceleration() == "tcg"


def test_resolve_acceleration_kvm_when_device_present() -> None:
    with (
        patch("scripts.raven_build_config.is_cloud_builder", return_value=False),
        patch("scripts.raven_build_config.kvm_device_present", return_value=True),
    ):
        assert resolve_acceleration() == "kvm"


def test_acceleration_blocker_absent_on_cloud_without_kvm() -> None:
    with patch("scripts.raven_build_config.kvm_device_present", return_value=False):
        assert acceleration_blocker(cloud_builder=True) is None


def test_acceleration_blocker_present_locally_without_kvm_or_cloud_flag() -> None:
    with patch("scripts.raven_build_config.kvm_device_present", return_value=False):
        blocker = acceleration_blocker(cloud_builder=False)
        assert blocker is not None
        assert "KVM unavailable" in blocker


def test_qemu_command_uses_uefi_pflash_for_tcg(tmp_path: Path) -> None:
    qcow2 = tmp_path / "disk.qcow2"
    qcow2.write_bytes(b"qcow2")
    serial = tmp_path / "serial.log"
    cmd = build_qemu_uefi_command(
        qcow2=qcow2,
        firmware=_firmware(tmp_path),
        serial_log=serial,
        acceleration="tcg",
    )
    joined = " ".join(cmd)
    assert "q35,accel=tcg" in joined
    assert "if=pflash" in joined
    assert "-cpu max" in joined
    assert "-snapshot" in cmd


def test_boot_smoke_cloud_timeout_via_resolve() -> None:
    from scripts.boot_smoke import resolve_timeout_seconds

    with patch("scripts.boot_smoke.is_cloud_builder", return_value=True):
        assert resolve_timeout_seconds(None) == 300


def test_qemu_command_uses_kvm_and_host_cpu_when_requested(tmp_path: Path) -> None:
    qcow2 = tmp_path / "disk.qcow2"
    qcow2.write_bytes(b"qcow2")
    serial = tmp_path / "serial.log"
    cmd = build_qemu_uefi_command(
        qcow2=qcow2,
        firmware=_firmware(tmp_path),
        serial_log=serial,
        acceleration="kvm",
    )
    joined = " ".join(cmd)
    assert "q35,accel=kvm" in joined
    assert "-cpu host" in joined
