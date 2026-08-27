"""M04 image definition and build-path contracts (INC-002 Layer A)."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest
from scripts.raven_build_config import (
    OVMF_FIRMWARE_CANDIDATES,
    PODMAN_STORAGE_STRATEGY,
    build_paths,
    detect_uefi_firmware,
    ensure_within_build_root,
    resolve_podman_context,
)

ROOT = Path(__file__).resolve().parents[1]
FLUXO = ROOT / "docs" / "versions" / "v0.1" / "FLUXO.md"
CONTAINERFILE = ROOT / "Containerfile"
MANIFEST = ROOT / "os" / "image-source.toml"
SCRIPTS = ROOT / "scripts"

FORBIDDEN_KERNEL_MARKERS = ("kernel-lt", "kernel-ml", "akmod", "nvidia", "linux-firmware-nvidia")
FORBIDDEN_LATEST_PIN = re.compile(r"base_reference\s*=\s*\"[^\"]*:latest\"")


def test_containerfile_exists_and_uses_fedora_kinoite_44() -> None:
    text = CONTAINERFILE.read_text(encoding="utf-8")
    assert "fedora-kinoite:44" in text
    assert "ARG BASE_IMAGE=" in text
    assert "ARG FEDORA_MAJOR=44" in text


def test_containerfile_does_not_introduce_custom_kernel() -> None:
    text = CONTAINERFILE.read_text(encoding="utf-8").lower()
    for marker in FORBIDDEN_KERNEL_MARKERS:
        assert marker not in text, f"forbidden kernel marker: {marker}"


def test_manifest_parses_with_required_fields() -> None:
    data = tomllib.loads(MANIFEST.read_text(encoding="utf-8"))
    image = data["image"]
    tooling = data["tooling"]
    required_image = (
        "fedora_major",
        "base_reference",
        "base_digest",
        "digest_verification_state",
        "target_architecture",
        "desktop_session_family",
        "qcow2_root_filesystem",
        "raven_local_image",
    )
    for key in required_image:
        assert key in image, f"missing image.{key}"
    assert image["fedora_major"] == 44
    assert image["target_architecture"] == "x86_64"
    assert "bootc_image_builder_reference" in tooling
    assert "bootc_image_builder_policy" in tooling


def test_manifest_does_not_use_latest_as_release_pin() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    assert not FORBIDDEN_LATEST_PIN.search(text)
    assert "fedora-kinoite:44" in text


def test_build_output_paths_stay_inside_build_root() -> None:
    paths = build_paths(ROOT)
    inside = paths.qcow2_dir / "raven-os-v0.1.qcow2"
    ensure_within_build_root(paths, inside)
    outside = ROOT / "escape.qcow2"
    try:
        ensure_within_build_root(paths, outside)
        raise AssertionError("expected path outside .build to be rejected")
    except ValueError:
        pass


def test_fluxo_m01_m03_accepted_and_points_20() -> None:
    text = FLUXO.read_text(encoding="utf-8")
    assert re.search(r"\|\s*M01\s*\|[^|]+\|\s*8\s*\|\s*ACCEPTED\s*\|", text)
    assert re.search(r"\|\s*M02\s*\|[^|]+\|\s*7\s*\|\s*ACCEPTED\s*\|", text)
    assert re.search(r"\|\s*M03\s*\|[^|]+\|\s*5\s*\|\s*ACCEPTED\s*\|", text)
    assert re.search(r"COMPLETED POINTS\s*=\s*\*\*20\*\*", text)
    assert re.search(r"VERSION PROGRESS\s*=\s*\*\*20%\*\*", text)


def test_m04_is_not_accepted_by_executor() -> None:
    text = FLUXO.read_text(encoding="utf-8")
    assert "M04" in text
    assert re.search(r"\|\s*M04\s*\|[^|]+\|\s*12\s*\|\s*BLOCKED\s*\|", text)
    assert not re.search(r"\|\s*M04\s*\|[^|]+\|\s*12\s*\|\s*ACCEPTED\s*\|", text)


def test_required_m04_scripts_exist() -> None:
    required = [
        "builder_preflight.py",
        "build_image.py",
        "build_qcow2.py",
        "image_check.py",
        "artifact_metadata.py",
        "boot_smoke.py",
        "raven_build_config.py",
    ]
    missing = [name for name in required if not (SCRIPTS / name).is_file()]
    assert not missing, f"missing scripts: {missing}"


def test_boot_smoke_requires_explicit_uefi_ovmf() -> None:
    smoke = (SCRIPTS / "boot_smoke.py").read_text(encoding="utf-8")
    qemu = (SCRIPTS / "boot_smoke_qemu.py").read_text(encoding="utf-8")
    assert "detect_uefi_firmware" in smoke
    assert "build_qemu_uefi_command" in smoke
    assert "if=pflash" in qemu
    assert "UefiFirmware" in qemu
    assert "-machine" in qemu
    assert "q35" in qemu
    assert "uefi-ovmf" in smoke


def test_builder_preflight_checks_uefi_firmware() -> None:
    text = (SCRIPTS / "builder_preflight.py").read_text(encoding="utf-8")
    assert "detect_uefi_firmware" in text
    assert "UEFI/OVMF firmware unavailable" in text


def test_build_scripts_share_repo_local_podman_storage() -> None:
    for name in ("build_image.py", "build_qcow2.py", "image_check.py"):
        text = (SCRIPTS / name).read_text(encoding="utf-8")
        assert "resolve_podman_context" in text
        assert "write_podman_storage_evidence" in text or name == "image_check.py"
    config = (SCRIPTS / "raven_build_config.py").read_text(encoding="utf-8")
    assert PODMAN_STORAGE_STRATEGY in config
    assert "CONTAINERS_STORAGE_CONF" in config


def test_cloud_podman_context_uses_cgroupfs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAVEN_CLOUD_BUILDER", "1")
    paths = build_paths(ROOT)
    ctx = resolve_podman_context(paths)
    assert "CONTAINERS_CONF" in ctx.env
    assert "BUILDAH_ISOLATION" in ctx.env
    assert ctx.env["BUILDAH_ISOLATION"] == "chroot"
    assert "cloud-cgroupfs" in ctx.strategy
    conf_text = Path(ctx.env["CONTAINERS_CONF"]).read_text(encoding="utf-8")
    assert 'cgroup_manager = "cgroupfs"' in conf_text


def test_build_qcow2_mounts_repo_graphroot_for_bootc_image_builder() -> None:
    text = (SCRIPTS / "build_qcow2.py").read_text(encoding="utf-8")
    assert "storage_mount_path" in text
    assert "/var/lib/containers/storage" in text


def test_resolve_podman_context_uses_build_local_graphroot(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (root / "AGENTS.md").write_text("# x\n", encoding="utf-8")
    paths = build_paths(root)
    ctx = resolve_podman_context(paths)
    assert ctx.strategy == PODMAN_STORAGE_STRATEGY
    assert str(paths.podman_graphroot) in ctx.storage_mount_path
    assert paths.podman_storage_conf.is_file()


def test_ovmf_candidate_list_is_non_empty() -> None:
    assert OVMF_FIRMWARE_CANDIDATES


def test_detect_uefi_firmware_returns_none_when_firmware_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("scripts.raven_build_config.OVMF_FIRMWARE_CANDIDATES", ())
    monkeypatch.setattr("scripts.raven_build_config.OVMF_SEARCH_DIRS", ())
    assert detect_uefi_firmware(tmp_path / "evidence") is None


def test_detect_uefi_firmware_discovers_dynamic_ovmf_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    share = tmp_path / "share" / "OVMF"
    share.mkdir(parents=True)
    (share / "OVMF_CODE_4M.secboot.fd").write_bytes(b"code")
    (share / "OVMF_VARS_4M.secboot.fd").write_bytes(b"vars")
    monkeypatch.setattr("scripts.raven_build_config.OVMF_FIRMWARE_CANDIDATES", ())
    monkeypatch.setattr("scripts.raven_build_config.OVMF_SEARCH_DIRS", (str(share),))
    firmware = detect_uefi_firmware(tmp_path / "evidence")
    assert firmware is not None
    assert firmware.code_path.name == "OVMF_CODE_4M.secboot.fd"


def test_ovmf_candidates_include_ubuntu_4m_paths() -> None:
    joined = " ".join(f"{code} {vars_}" for code, vars_ in OVMF_FIRMWARE_CANDIDATES)
    assert "OVMF_CODE_4M.secboot.fd" in joined
    assert "OVMF_VARS_4M.secboot.fd" in joined
