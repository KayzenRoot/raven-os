"""Shared Raven OS image build configuration and path guards (M04)."""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_BASE_IMAGE = "quay.io/fedora/fedora-kinoite:44"
DEFAULT_FEDORA_MAJOR = 44
RAVEN_LOCAL_IMAGE = "localhost/raven-os:0.1-dev"
BIB_REFERENCE = "quay.io/centos-bootc/bootc-image-builder:latest"
BUILD_ROOT_NAME = ".build"
IMAGES_SUBDIR = "images"
QCOW2_SUBDIR = "qcow2"
EVIDENCE_SUBDIR = "evidence"
PODMAN_STORAGE_STRATEGY = "repo-local-containers-storage-conf"

OVMF_FIRMWARE_CANDIDATES: tuple[tuple[str, str], ...] = (
    ("/usr/share/edk2/ovmf/OVMF_CODE.secboot.fd", "/usr/share/edk2/ovmf/OVMF_VARS.secboot.fd"),
    ("/usr/share/OVMF/OVMF_CODE.secboot.fd", "/usr/share/OVMF/OVMF_VARS.secboot.fd"),
    ("/usr/share/edk2/ovmf/OVMF_CODE.fd", "/usr/share/edk2/ovmf/OVMF_VARS.fd"),
    ("/usr/share/qemu/OVMF_CODE.fd", "/usr/share/qemu/OVMF_VARS.fd"),
)


@dataclass(frozen=True)
class BuildPaths:
    repo_root: Path
    build_root: Path
    images_dir: Path
    qcow2_dir: Path
    evidence_dir: Path
    containerfile: Path
    manifest_path: Path
    containers_dir: Path
    podman_storage_conf: Path
    podman_graphroot: Path
    podman_runroot: Path


@dataclass(frozen=True)
class PodmanContext:
    command_prefix: tuple[str, ...]
    env: dict[str, str]
    storage_mount_path: str
    strategy: str


@dataclass(frozen=True)
class UefiFirmware:
    code_path: Path
    vars_template_path: Path
    vars_runtime_path: Path
    candidate_label: str


def resolve_repo_root(start: Path | None = None) -> Path:
    path = (start or Path.cwd()).resolve()
    for candidate in [path, *path.parents]:
        if (candidate / "pyproject.toml").is_file() and (candidate / "AGENTS.md").is_file():
            return candidate
    return path


def build_paths(repo_root: Path | None = None) -> BuildPaths:
    root = resolve_repo_root(repo_root)
    build_root = root / BUILD_ROOT_NAME
    containers_dir = build_root / "containers"
    graphroot = containers_dir / "storage"
    runroot = containers_dir / "run"
    return BuildPaths(
        repo_root=root,
        build_root=build_root,
        images_dir=build_root / IMAGES_SUBDIR,
        qcow2_dir=build_root / QCOW2_SUBDIR,
        evidence_dir=build_root / EVIDENCE_SUBDIR,
        containerfile=root / "Containerfile",
        manifest_path=root / "os" / "image-source.toml",
        containers_dir=containers_dir,
        podman_storage_conf=containers_dir / "storage.conf",
        podman_graphroot=graphroot,
        podman_runroot=runroot,
    )


def ensure_podman_storage(paths: BuildPaths) -> Path:
    paths.containers_dir.mkdir(parents=True, exist_ok=True)
    paths.podman_graphroot.mkdir(parents=True, exist_ok=True)
    paths.podman_runroot.mkdir(parents=True, exist_ok=True)
    paths.podman_storage_conf.write_text(
        "[storage]\n"
        'driver = "overlay"\n'
        f'graphroot = "{paths.podman_graphroot.as_posix()}"\n'
        f'runroot = "{paths.podman_runroot.as_posix()}"\n',
        encoding="utf-8",
    )
    return paths.podman_storage_conf


def resolve_podman_context(paths: BuildPaths) -> PodmanContext:
    ensure_podman_storage(paths)
    env = os.environ.copy()
    env["CONTAINERS_STORAGE_CONF"] = str(paths.podman_storage_conf.resolve())
    return PodmanContext(
        command_prefix=("podman",),
        env=env,
        storage_mount_path=str(paths.podman_graphroot.resolve()),
        strategy=PODMAN_STORAGE_STRATEGY,
    )


def podman_command(ctx: PodmanContext, *args: str) -> list[str]:
    return [*ctx.command_prefix, *args]


def write_podman_storage_evidence(paths: BuildPaths, ctx: PodmanContext) -> None:
    paths.evidence_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "strategy": ctx.strategy,
        "storage_conf": str(paths.podman_storage_conf),
        "graphroot": str(paths.podman_graphroot),
        "runroot": str(paths.podman_runroot),
        "bib_mount_target": "/var/lib/containers/storage",
        "bib_mount_source": ctx.storage_mount_path,
        "note": (
            "All M04 podman build/inspect/run commands and bootc-image-builder share the "
            "repo-local graphroot via CONTAINERS_STORAGE_CONF and an identical bind mount."
        ),
    }
    (paths.evidence_dir / "podman-storage.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_podman(
    ctx: PodmanContext,
    args: list[str],
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        podman_command(ctx, *args),
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        env=ctx.env,
    )


def load_manifest(repo_root: Path | None = None) -> dict[str, Any]:
    paths = build_paths(repo_root)
    if not paths.manifest_path.is_file():
        raise FileNotFoundError(f"missing manifest: {paths.manifest_path}")
    with paths.manifest_path.open("rb") as handle:
        return tomllib.load(handle)


def update_manifest_field(path: Path, key: str, value: str) -> None:
    text = path.read_text(encoding="utf-8")
    pattern = rf'^({re.escape(key)} = )".*?"'
    replacement = rf'\1"{value}"'
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise ValueError(f"manifest field not updated: {key}")
    path.write_text(updated, encoding="utf-8")


def update_manifest_verified_digests(
    paths: BuildPaths,
    *,
    base_digest: str,
    bib_digest: str = "",
) -> None:
    update_manifest_field(paths.manifest_path, "base_digest", base_digest)
    update_manifest_field(paths.manifest_path, "digest_verification_state", "verified")
    if bib_digest:
        update_manifest_field(
            paths.manifest_path,
            "bootc_image_builder_resolved_digest",
            bib_digest,
        )


def detect_uefi_firmware(evidence_dir: Path) -> UefiFirmware | None:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    for code_str, vars_str in OVMF_FIRMWARE_CANDIDATES:
        code = Path(code_str)
        vars_template = Path(vars_str)
        if code.is_file() and vars_template.is_file():
            runtime_vars = evidence_dir / "OVMF_VARS.runtime.fd"
            shutil.copy2(vars_template, runtime_vars)
            return UefiFirmware(
                code_path=code,
                vars_template_path=vars_template,
                vars_runtime_path=runtime_vars,
                candidate_label=f"{code} + {vars_template}",
            )
    return None


def ensure_within_build_root(paths: BuildPaths, candidate: Path) -> Path:
    resolved = candidate.resolve()
    build_root = paths.build_root.resolve()
    try:
        resolved.relative_to(build_root)
    except ValueError as exc:
        raise ValueError(f"path must remain inside {build_root}") from exc
    return resolved


def ensure_within_repo_root(paths: BuildPaths, candidate: Path) -> Path:
    resolved = candidate.resolve()
    repo_root = paths.repo_root.resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError(f"path must remain inside {repo_root}") from exc
    return resolved


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def run_command(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def platform_summary() -> dict[str, str]:
    return {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "platform": platform.platform(),
    }


def is_linux_x86_64() -> bool:
    summary = platform_summary()
    return summary["system"].lower() == "linux" and summary["machine"] in {
        "x86_64",
        "amd64",
    }
