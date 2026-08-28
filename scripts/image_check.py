#!/usr/bin/env python3
"""Validate the locally built Raven OCI image properties (M04)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from scripts.raven_build_config import (
    RAVEN_LOCAL_IMAGE,
    build_paths,
    command_exists,
    is_linux_x86_64,
    load_manifest,
    resolve_podman_context,
    run_podman,
    write_podman_storage_evidence,
)

FORBIDDEN_KERNEL_MARKERS = (
    "kernel-lt",
    "kernel-ml",
    "akmod",
    "nvidia",
    "proton",
    "wine",
)


def image_check(repo_root: Path | None = None) -> int:
    paths = build_paths(repo_root)
    if not is_linux_x86_64():
        print("error: image-check requires Linux x86_64 Raven Builder", file=sys.stderr)
        return 2
    if not command_exists("podman"):
        print("error: podman is required", file=sys.stderr)
        return 2

    manifest = load_manifest(paths.repo_root)
    local_tag = str(manifest["image"].get("raven_local_image", RAVEN_LOCAL_IMAGE))
    ctx = resolve_podman_context(paths)
    write_podman_storage_evidence(paths, ctx)

    log_driver_out = run_podman(
        ctx,
        ["info", "--format", "{{ .Host.LogDriver }}"],
        paths.repo_root,
    )
    if log_driver_out.returncode != 0:
        print(log_driver_out.stderr or log_driver_out.stdout, file=sys.stderr)
        return int(log_driver_out.returncode)
    effective_log_driver = (log_driver_out.stdout or "").strip()
    if effective_log_driver != "k8s-file":
        print(
            f"error: podman effective log driver is {effective_log_driver!r}, expected 'k8s-file'",
            file=sys.stderr,
        )
        return 1

    exists = run_podman(ctx, ["image", "exists", local_tag], paths.repo_root)
    if exists.returncode != 0:
        print(
            f"error: local image not found in repo-local podman storage: {local_tag}",
            file=sys.stderr,
        )
        return 1

    inspect = run_podman(ctx, ["inspect", local_tag], paths.repo_root)
    if inspect.returncode != 0:
        print(inspect.stderr or inspect.stdout, file=sys.stderr)
        return int(inspect.returncode)

    data = json.loads(inspect.stdout)[0]
    labels = data.get("Config", {}).get("Labels", {}) or {}
    findings = {
        "image": local_tag,
        "labels": labels,
        "digest": data.get("Digest", ""),
        "architecture": data.get("Architecture", ""),
        "podman_storage_strategy": ctx.strategy,
        "podman_graphroot": str(paths.podman_graphroot),
        "podman_log_driver": effective_log_driver,
    }

    required_label_keys = ("io.raven.os.version", "io.raven.os.variant")
    missing = [key for key in required_label_keys if key not in labels]
    if missing:
        print(f"error: missing Raven labels: {missing}", file=sys.stderr)
        return 1

    run_args = ["run", "--rm", "--log-driver=k8s-file", local_tag, "cat", "/usr/lib/raven/version"]
    version_out = run_podman(ctx, run_args, paths.repo_root)
    if version_out.returncode != 0:
        print(version_out.stderr or version_out.stdout, file=sys.stderr)
        return int(version_out.returncode)
    findings["raven_version_file"] = (version_out.stdout or "").strip()

    containerfile_text = paths.containerfile.read_text(encoding="utf-8").lower()
    for marker in FORBIDDEN_KERNEL_MARKERS:
        if marker in containerfile_text:
            print(f"error: forbidden marker in Containerfile: {marker}", file=sys.stderr)
            return 1

    paths.evidence_dir.mkdir(parents=True, exist_ok=True)
    (paths.evidence_dir / "image-check.json").write_text(
        json.dumps(findings, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"image-check ok: {local_tag}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check Raven OCI image")
    parser.add_argument("--repo-root", type=Path, default=None)
    args = parser.parse_args(argv)
    return image_check(args.repo_root)


if __name__ == "__main__":
    raise SystemExit(main())
