#!/usr/bin/env python3
"""Build the local Raven OCI image from the root Containerfile (M04)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scripts.raven_build_config import (
    DEFAULT_BASE_IMAGE,
    DEFAULT_FEDORA_MAJOR,
    RAVEN_LOCAL_IMAGE,
    build_paths,
    command_exists,
    is_linux_x86_64,
    load_manifest,
    podman_command,
    resolve_podman_context,
    run_podman,
    write_podman_storage_evidence,
)


def build_image(repo_root: Path | None = None) -> int:
    paths = build_paths(repo_root)
    if not is_linux_x86_64():
        print("error: build-image requires Linux x86_64 Raven Builder", file=sys.stderr)
        return 2
    if not command_exists("podman"):
        print("error: podman is required", file=sys.stderr)
        return 2
    if not paths.containerfile.is_file():
        print(f"error: missing Containerfile at {paths.containerfile}", file=sys.stderr)
        return 1

    manifest = load_manifest(paths.repo_root)
    image_cfg = manifest["image"]
    base_reference = str(image_cfg.get("base_reference", DEFAULT_BASE_IMAGE))
    fedora_major = int(image_cfg.get("fedora_major", DEFAULT_FEDORA_MAJOR))
    local_tag = str(image_cfg.get("raven_local_image", RAVEN_LOCAL_IMAGE))

    paths.images_dir.mkdir(parents=True, exist_ok=True)
    paths.evidence_dir.mkdir(parents=True, exist_ok=True)
    ctx = resolve_podman_context(paths)
    write_podman_storage_evidence(paths, ctx)

    build_cmd = [
        "build",
        "-f",
        str(paths.containerfile),
        "-t",
        local_tag,
        "--build-arg",
        f"FEDORA_MAJOR={fedora_major}",
        "--build-arg",
        f"BASE_IMAGE={base_reference}",
        str(paths.repo_root),
    ]
    completed = run_podman(ctx, build_cmd, paths.repo_root)
    log_path = paths.evidence_dir / "build-image.log"
    log_path.write_text(
        f"storage_strategy: {ctx.strategy}\n"
        f"storage_conf: {paths.podman_storage_conf}\n"
        f"command: {' '.join(podman_command(ctx, *build_cmd))}\n"
        f"exit_code: {completed.returncode}\n"
        f"{'=' * 60}\n"
        f"{completed.stdout}\n{completed.stderr}",
        encoding="utf-8",
    )
    if completed.returncode != 0:
        print(completed.stderr or completed.stdout, file=sys.stderr)
        return int(completed.returncode)

    inspect = run_podman(
        ctx,
        ["images", "--format", "{{.ID}} {{.Digest}}", local_tag],
        paths.repo_root,
    )
    (paths.evidence_dir / "build-image-id.txt").write_text(
        (inspect.stdout or "").strip() + "\n",
        encoding="utf-8",
    )
    print(f"built {local_tag}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Raven OCI image")
    parser.add_argument("--repo-root", type=Path, default=None)
    args = parser.parse_args(argv)
    return build_image(args.repo_root)


if __name__ == "__main__":
    raise SystemExit(main())
