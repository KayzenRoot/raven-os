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
IMAGE_BUILDER_REFERENCE = "ghcr.io/osbuild/image-builder:latest"
ARCHIVED_BIB_REFERENCE = "quay.io/centos-bootc/bootc-image-builder:latest"
BUILD_ROOT_NAME = ".build"
IMAGES_SUBDIR = "images"
QCOW2_SUBDIR = "qcow2"
EVIDENCE_SUBDIR = "evidence"
PODMAN_STORAGE_STRATEGY = "repo-local-containers-storage-conf"
CLOUD_PODMAN_GRAPHROOT = "/var/lib/containers/storage"
CLOUD_PODMAN_RUNROOT = "/run/containers/storage"

OVMF_FIRMWARE_CANDIDATES: tuple[tuple[str, str], ...] = (
    ("/usr/share/edk2/ovmf/OVMF_CODE.secboot.fd", "/usr/share/edk2/ovmf/OVMF_VARS.secboot.fd"),
    ("/usr/share/OVMF/OVMF_CODE.secboot.fd", "/usr/share/OVMF/OVMF_VARS.secboot.fd"),
    ("/usr/share/OVMF/OVMF_CODE_4M.secboot.fd", "/usr/share/OVMF/OVMF_VARS_4M.secboot.fd"),
    ("/usr/share/OVMF/OVMF_CODE_4M.fd", "/usr/share/OVMF/OVMF_VARS_4M.fd"),
    ("/usr/share/edk2/ovmf/OVMF_CODE.fd", "/usr/share/edk2/ovmf/OVMF_VARS.fd"),
    ("/usr/share/qemu/OVMF_CODE.fd", "/usr/share/qemu/OVMF_VARS.fd"),
    ("/usr/share/edk2/OVMF_CODE.fd", "/usr/share/edk2/OVMF_VARS.fd"),
)

OVMF_SEARCH_DIRS: tuple[str, ...] = (
    "/usr/share/OVMF",
    "/usr/share/edk2/ovmf",
    "/usr/share/edk2-ovmf",
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
    if is_cloud_builder():
        graphroot = Path(CLOUD_PODMAN_GRAPHROOT)
        runroot = Path(CLOUD_PODMAN_RUNROOT)
        subprocess.run(
            ["sudo", "mkdir", "-p", str(graphroot), str(runroot)],
            check=False,
        )
    else:
        graphroot = paths.podman_graphroot
        runroot = paths.podman_runroot
        graphroot.mkdir(parents=True, exist_ok=True)
        runroot.mkdir(parents=True, exist_ok=True)
    paths.podman_storage_conf.write_text(
        "[storage]\n"
        'driver = "overlay"\n'
        f'graphroot = "{graphroot.as_posix()}"\n'
        f'runroot = "{runroot.as_posix()}"\n',
        encoding="utf-8",
    )
    return paths.podman_storage_conf


def ensure_cloud_containers_conf(paths: BuildPaths) -> Path:
    conf_path = paths.containers_dir / "containers.conf"
    conf_path.write_text(
        "[containers]\n"
        'log_driver = "k8s-file"\n'
        "[engine]\n"
        'cgroup_manager = "cgroupfs"\n'
        'events_logger = "file"\n'
        'runtime = "crun"\n',
        encoding="utf-8",
    )
    return conf_path


def load_cloud_containers_conf(paths: BuildPaths) -> dict[str, Any]:
    """Parse Raven-owned cloud containers.conf (stdlib tomllib)."""
    conf_path = ensure_cloud_containers_conf(paths)
    with conf_path.open("rb") as handle:
        return tomllib.load(handle)


def resolve_podman_context(paths: BuildPaths) -> PodmanContext:
    ensure_podman_storage(paths)
    env = os.environ.copy()
    env["CONTAINERS_STORAGE_CONF"] = str(paths.podman_storage_conf.resolve())
    strategy = PODMAN_STORAGE_STRATEGY
    if is_cloud_builder():
        containers_conf = ensure_cloud_containers_conf(paths)
        env["CONTAINERS_CONF"] = str(containers_conf.resolve())
        env["BUILDAH_ISOLATION"] = "chroot"
        strategy = f"{PODMAN_STORAGE_STRATEGY}+cloud-system-graphroot+rootful-sudo+cgroupfs"
        storage_mount_path = CLOUD_PODMAN_GRAPHROOT
    else:
        storage_mount_path = str(paths.podman_graphroot.resolve())
    return PodmanContext(
        command_prefix=("podman",),
        env=env,
        storage_mount_path=storage_mount_path,
        strategy=strategy,
    )


def podman_command(ctx: PodmanContext, *args: str) -> list[str]:
    if "rootful-sudo" in ctx.strategy:
        env_pairs: list[str] = []
        for key in ("CONTAINERS_STORAGE_CONF", "CONTAINERS_CONF", "BUILDAH_ISOLATION"):
            value = ctx.env.get(key)
            if value:
                env_pairs.append(f"{key}={value}")
        return ["sudo", "env", *env_pairs, "podman", *args]
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
            "All M04 podman build/inspect/run commands and osbuild/image-builder share the "
            "rootful graphroot via CONTAINERS_STORAGE_CONF and an identical bind mount."
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
            "image_builder_resolved_digest",
            bib_digest,
        )


def iter_ovmf_firmware_candidates() -> list[tuple[Path, Path]]:
    seen: set[tuple[str, str]] = set()
    pairs: list[tuple[Path, Path]] = []
    for code_str, vars_str in OVMF_FIRMWARE_CANDIDATES:
        key = (code_str, vars_str)
        if key in seen:
            continue
        seen.add(key)
        pairs.append((Path(code_str), Path(vars_str)))
    for directory_str in OVMF_SEARCH_DIRS:
        directory = Path(directory_str)
        if not directory.is_dir():
            continue
        for code in sorted(directory.glob("OVMF_CODE*.fd")):
            suffix = code.name.removeprefix("OVMF_CODE")
            vars_template = directory / f"OVMF_VARS{suffix}"
            key = (str(code), str(vars_template))
            if key in seen:
                continue
            seen.add(key)
            pairs.append((code, vars_template))
    return pairs


def detect_uefi_firmware(evidence_dir: Path) -> UefiFirmware | None:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    for code, vars_template in iter_ovmf_firmware_candidates():
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


def is_cloud_builder() -> bool:
    return os.environ.get("RAVEN_CLOUD_BUILDER", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }


def kvm_device_present() -> bool:
    return Path("/dev/kvm").exists()


def resolve_acceleration() -> str:
    """Return ``kvm`` when usable, otherwise ``tcg`` (accepted on cloud builders)."""
    if kvm_device_present():
        return "kvm"
    return "tcg"


def acceleration_blocker(*, cloud_builder: bool | None = None) -> str | None:
    cloud = is_cloud_builder() if cloud_builder is None else cloud_builder
    if kvm_device_present() or cloud:
        return None
    return "KVM unavailable (/dev/kvm missing) and cloud TCG fallback not enabled"
