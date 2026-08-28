#!/usr/bin/env python3
"""Convert the local Raven OCI image to QCOW2 via osbuild/image-builder (M04)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scripts.image_builder_cli import image_builder_build_qcow2_args
from scripts.raven_build_config import (
    IMAGE_BUILDER_REFERENCE,
    RAVEN_LOCAL_IMAGE,
    build_paths,
    command_exists,
    ensure_within_build_root,
    is_linux_x86_64,
    load_manifest,
    podman_command,
    resolve_podman_context,
    run_podman,
    write_podman_storage_evidence,
)


def image_builder_container_run_args(
    *,
    output_mount: Path,
    storage_mount_path: str,
    image_builder_ref: str,
    rootfs: str,
    local_tag: str,
) -> list[str]:
    return [
        "run",
        "--rm",
        "--privileged",
        "--security-opt",
        "label=type:unconfined_t",
        "-v",
        f"{output_mount}:/output",
        "-v",
        f"{storage_mount_path}:/var/lib/containers/storage",
        image_builder_ref,
        *image_builder_build_qcow2_args(
            bootc_ref=local_tag,
            rootfs=rootfs,
        ),
    ]


def build_qcow2(repo_root: Path | None = None, output_name: str = "raven-os-v0.1.qcow2") -> int:
    paths = build_paths(repo_root)
    if not is_linux_x86_64():
        print("error: build-qcow2 requires Linux x86_64 Raven Builder", file=sys.stderr)
        return 2
    if not command_exists("podman"):
        print("error: podman is required", file=sys.stderr)
        return 2

    manifest = load_manifest(paths.repo_root)
    image_cfg = manifest["image"]
    tooling = manifest["tooling"]
    local_tag = str(image_cfg.get("raven_local_image", RAVEN_LOCAL_IMAGE))
    rootfs = str(image_cfg.get("qcow2_root_filesystem", "btrfs"))
    image_builder_ref = str(tooling.get("image_builder_reference", IMAGE_BUILDER_REFERENCE))

    paths.qcow2_dir.mkdir(parents=True, exist_ok=True)
    paths.evidence_dir.mkdir(parents=True, exist_ok=True)
    output_path = ensure_within_build_root(paths, paths.qcow2_dir / output_name)
    ctx = resolve_podman_context(paths)
    write_podman_storage_evidence(paths, ctx)

    exists = run_podman(ctx, ["image", "exists", local_tag], paths.repo_root)
    if exists.returncode != 0:
        print(
            f"error: Raven image not found in repo-local podman storage: {local_tag}",
            file=sys.stderr,
        )
        return 1

    output_mount = paths.qcow2_dir.resolve()
    run_args = image_builder_container_run_args(
        output_mount=output_mount,
        storage_mount_path=ctx.storage_mount_path,
        image_builder_ref=image_builder_ref,
        rootfs=rootfs,
        local_tag=local_tag,
    )
    completed = run_podman(ctx, run_args, paths.repo_root)
    log_path = paths.evidence_dir / "build-qcow2.log"
    log_path.write_text(
        f"storage_strategy: {ctx.strategy}\n"
        f"storage_mount_source: {ctx.storage_mount_path}\n"
        f"image_builder_reference: {image_builder_ref}\n"
        f"command: {' '.join(podman_command(ctx, *run_args))}\n"
        f"exit_code: {completed.returncode}\n"
        f"expected_output: {output_path}\n"
        f"{'=' * 60}\n"
        f"{completed.stdout}\n{completed.stderr}",
        encoding="utf-8",
    )
    if completed.returncode != 0:
        print(completed.stderr or completed.stdout, file=sys.stderr)
        return int(completed.returncode)

    inspect_tool = run_podman(
        ctx,
        ["inspect", "--format", "{{.Digest}}", image_builder_ref],
        paths.repo_root,
    )
    if inspect_tool.returncode == 0 and (inspect_tool.stdout or "").strip():
        (paths.evidence_dir / "image-builder-digest.txt").write_text(
            (inspect_tool.stdout or "").strip() + "\n",
            encoding="utf-8",
        )

    produced = sorted(paths.qcow2_dir.glob("*.qcow2"), key=lambda p: p.stat().st_mtime)
    if not produced and not output_path.exists():
        print("error: QCOW2 artifact not found after build", file=sys.stderr)
        return 1

    artifact = produced[-1] if produced else output_path
    print(f"qcow2: {artifact}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Raven QCOW2")
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--output-name", default="raven-os-v0.1.qcow2")
    args = parser.parse_args(argv)
    return build_qcow2(args.repo_root, args.output_name)


if __name__ == "__main__":
    raise SystemExit(main())
