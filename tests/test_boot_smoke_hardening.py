"""Prompt 002E-R2 boot-smoke hardening contracts."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from scripts.boot_smoke import main, resolve_timeout_seconds
from scripts.boot_smoke_markers import evaluate_serial_log
from scripts.boot_smoke_qemu import build_qemu_uefi_command
from scripts.boot_smoke_runner import (
    CLASSIFICATION_LAUNCH_ERROR,
    CLASSIFICATION_PASS,
    CLASSIFICATION_TIMEOUT,
    run_boot_attempt,
)
from scripts.create_diagnostics import DIAGNOSTICS_NAME, create_diagnostics
from scripts.qcow2_preboot import validate_qcow2_preboot, write_qcow2_preboot_evidence
from scripts.raven_build_config import UefiFirmware

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "m04.yml"


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


def test_cloud_default_timeout_is_300_when_omitted() -> None:
    with patch("scripts.boot_smoke.is_cloud_builder", return_value=True):
        assert resolve_timeout_seconds(None) == 300


def test_local_default_timeout_is_120_when_omitted() -> None:
    with patch("scripts.boot_smoke.is_cloud_builder", return_value=False):
        assert resolve_timeout_seconds(None) == 120


def test_explicit_timeout_override() -> None:
    assert resolve_timeout_seconds(45) == 45


def test_non_positive_timeout_rejected() -> None:
    with pytest.raises(ValueError):
        resolve_timeout_seconds(0)
    with pytest.raises(ValueError):
        resolve_timeout_seconds(-1)


def test_cli_omitted_timeout_passes_none() -> None:
    with patch("scripts.boot_smoke.boot_smoke", return_value=0) as mocked:
        assert main([]) == 0
        mocked.assert_called_once_with(None, None)


def test_cli_explicit_timeout_override() -> None:
    with patch("scripts.boot_smoke.boot_smoke", return_value=0) as mocked:
        assert main(["--timeout-seconds", "45"]) == 0
        mocked.assert_called_once_with(None, 45)


def test_qemu_command_uses_snapshot_and_virtio_boot_disk(tmp_path: Path) -> None:
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
    assert "-snapshot" in cmd
    assert "if=none,id=raven-disk" in joined
    assert "virtio-blk-pci,drive=raven-disk,bootindex=1" in joined
    assert "-no-reboot" not in cmd


def test_efi_only_serial_log_fails() -> None:
    passed, guest, firmware = evaluate_serial_log("UEFI firmware EFI stub\n")
    assert not passed
    assert not guest
    assert firmware == ["EFI"]


def test_linux_systemd_fedora_marker_passes() -> None:
    log = "Linux version 6.12.0\nsystemd[1]: Welcome to Fedora Linux\n"
    passed, guest, _ = evaluate_serial_log(log)
    assert passed
    assert "Linux version" in guest
    assert "systemd" in guest


def test_empty_serial_fails() -> None:
    passed, guest, firmware = evaluate_serial_log("")
    assert not passed
    assert not guest
    assert not firmware


def test_mixed_realistic_serial_passes() -> None:
    log = "EFI stub\nLinux version 6.12\nFedora Kinoite\nsystemd[1]:\n"
    passed, guest, firmware = evaluate_serial_log(log)
    assert passed
    assert guest
    assert firmware == ["EFI"]


def test_early_qemu_exit_classified_as_launch_error(tmp_path: Path) -> None:
    serial = tmp_path / "serial.log"
    stdout = tmp_path / "stdout.log"
    stderr = tmp_path / "stderr.log"

    class ImmediateProcess:
        def __init__(self, *args, **kwargs):
            self._returncode = 1

        def poll(self):
            return self._returncode

        def terminate(self):
            return None

        def kill(self):
            return None

        def wait(self, timeout=None):
            return self._returncode

    with patch("scripts.boot_smoke_runner.subprocess.Popen", ImmediateProcess):
        result = run_boot_attempt(
            ["qemu-system-x86_64", "-version"],
            cwd=tmp_path,
            serial_log=serial,
            stdout_log=stdout,
            stderr_log=stderr,
            timeout_seconds=30,
            launch_grace_seconds=0.1,
        )
    assert result.classification == CLASSIFICATION_LAUNCH_ERROR


def test_running_process_with_guest_marker_passes(tmp_path: Path) -> None:
    serial = tmp_path / "serial.log"
    stdout = tmp_path / "stdout.log"
    stderr = tmp_path / "stderr.log"
    serial.write_text("Linux version 6.12\nsystemd[1]: started\n", encoding="utf-8")

    class AliveProcess:
        def __init__(self, *args, **kwargs):
            self._returncode = None

        def poll(self):
            return self._returncode

        def terminate(self):
            self._returncode = 0

        def kill(self):
            self._returncode = 0

        def wait(self, timeout=None):
            return self._returncode

    with (
        patch("scripts.boot_smoke_runner.subprocess.Popen", AliveProcess),
        patch.object(Path, "unlink", lambda self, missing_ok=False: None),
    ):
        result = run_boot_attempt(
            ["qemu-system-x86_64"],
            cwd=tmp_path,
            serial_log=serial,
            stdout_log=stdout,
            stderr_log=stderr,
            timeout_seconds=5,
            launch_grace_seconds=0.0,
            poll_interval_seconds=0.05,
        )
    assert result.classification == CLASSIFICATION_PASS
    assert "Linux version" in result.guest_markers


def test_timeout_without_marker_is_observability_timeout(tmp_path: Path) -> None:
    serial = tmp_path / "serial.log"
    stdout = tmp_path / "stdout.log"
    stderr = tmp_path / "stderr.log"

    class AliveProcess:
        def __init__(self, *args, **kwargs):
            self._returncode = None

        def poll(self):
            return self._returncode

        def terminate(self):
            self._returncode = 0

        def kill(self):
            self._returncode = 0

        def wait(self, timeout=None):
            return self._returncode

    with patch("scripts.boot_smoke_runner.subprocess.Popen", AliveProcess):
        result = run_boot_attempt(
            ["qemu-system-x86_64"],
            cwd=tmp_path,
            serial_log=serial,
            stdout_log=stdout,
            stderr_log=stderr,
            timeout_seconds=1,
            launch_grace_seconds=0.0,
            poll_interval_seconds=0.05,
        )
    assert result.classification == CLASSIFICATION_TIMEOUT


def test_qcow2_preboot_rejects_missing_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (root / "AGENTS.md").write_text("# x\n", encoding="utf-8")
    build = root / ".build" / "qcow2"
    build.mkdir(parents=True)
    missing = build / "missing.qcow2"
    from scripts.raven_build_config import build_paths

    paths = build_paths(root)
    result = validate_qcow2_preboot(missing, paths)
    assert not result.ok


def test_qcow2_preboot_with_mocked_qemu_img(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (root / "AGENTS.md").write_text("# x\n", encoding="utf-8")
    qcow2_dir = root / ".build" / "qcow2"
    evidence = root / ".build" / "evidence"
    qcow2_dir.mkdir(parents=True)
    evidence.mkdir(parents=True)
    qcow2 = qcow2_dir / "disk.qcow2"
    qcow2.write_bytes(b"fake")

    from scripts.raven_build_config import build_paths

    paths = build_paths(root)
    (evidence / "artifact-metadata.json").write_text(
        json.dumps({"artifacts": [{"path": ".build/qcow2/disk.qcow2", "sha256": "abc"}]}),
        encoding="utf-8",
    )

    def fake_run(args, cwd):
        if "info" in args:
            return MagicMock(
                returncode=0,
                stdout=json.dumps({"format": "qcow2", "virtual-size": 1000, "actual-size": 100}),
                stderr="",
            )
        return MagicMock(returncode=0, stdout="No errors", stderr="")

    monkeypatch.setattr("scripts.qcow2_preboot.command_exists", lambda _: True)
    monkeypatch.setattr("scripts.qcow2_preboot._run_qemu_img", fake_run)
    result = write_qcow2_preboot_evidence(qcow2, paths)
    assert result.ok
    payload = json.loads((evidence / "qcow2-preboot.json").read_text(encoding="utf-8"))
    assert payload["sha256"] == "abc"


def test_diagnostics_zip_excludes_qcow2(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (root / "AGENTS.md").write_text("# x\n", encoding="utf-8")
    (root / "docs" / "versions" / "v0.1").mkdir(parents=True)
    (root / "docs" / "versions" / "v0.1" / "FLUXO.md").write_text("# fluxo\n", encoding="utf-8")
    (root / "docs" / "versions" / "v0.1" / "CHECKPOINT.md").write_text("# cp\n", encoding="utf-8")
    evidence = root / ".build" / "evidence"
    evidence.mkdir(parents=True)
    (evidence / "run-m04-cloud.json").write_text("{}", encoding="utf-8")
    (root / ".build" / "qcow2").mkdir(parents=True)
    (root / ".build" / "qcow2" / "secret.qcow2").write_bytes(b"qcow2")

    zip_path = create_diagnostics(root)
    assert zip_path.name == DIAGNOSTICS_NAME
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
    assert not any(name.endswith(".qcow2") for name in names)


def test_workflow_uploads_diagnostics_on_failure() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "raven-m04-diagnostics" in text
    assert "RAVEN-OS-V0.1-INC-002-DIAGNOSTICS.zip" in text
    assert "if: failure()" in text


def test_image_builder_config_exists_with_serial_console() -> None:
    config = ROOT / "os" / "image-builder-config.toml"
    assert config.is_file()
    text = config.read_text(encoding="utf-8")
    assert "console=tty0 console=ttyS0,115200n8" in text


def test_build_qcow2_mounts_image_builder_config() -> None:
    text = (ROOT / "scripts" / "build_qcow2.py").read_text(encoding="utf-8")
    assert "image-builder-config.toml" in text
    assert "/config.toml:ro" in text
