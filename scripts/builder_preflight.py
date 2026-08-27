#!/usr/bin/env python3
"""Non-destructive Raven Builder preflight diagnostics (M04 Layer B gate)."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from scripts.raven_build_config import (
    BIB_REFERENCE,
    DEFAULT_BASE_IMAGE,
    build_paths,
    command_exists,
    detect_uefi_firmware,
    is_linux_x86_64,
    load_manifest,
    platform_summary,
    resolve_podman_context,
    run_podman,
    update_manifest_verified_digests,
    write_podman_storage_evidence,
)

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_BLOCKED = 2


def disk_free_gb(path: Path) -> float | None:
    try:
        usage = shutil.disk_usage(path)
    except OSError:
        return None
    return round(usage.free / (1024**3), 2)


def kvm_available() -> bool:
    return Path("/dev/kvm").exists()


def inspect_base_image(base_reference: str, paths: Any, ctx: Any) -> dict[str, Any]:
    pull = run_podman(ctx, ["pull", base_reference], paths.repo_root)
    if pull.returncode != 0:
        return {
            "status": "blocked",
            "reason": "base image pull failed",
            "base_reference": base_reference,
            "digest": "",
            "output": (pull.stdout or "") + (pull.stderr or ""),
        }
    inspect = run_podman(
        ctx,
        ["inspect", "--format", "{{.Digest}}", base_reference],
        paths.repo_root,
    )
    digest = (inspect.stdout or "").strip()
    if inspect.returncode != 0 or not digest:
        return {
            "status": "blocked",
            "reason": "base image inspect failed",
            "base_reference": base_reference,
            "digest": "",
            "output": (inspect.stdout or "") + (inspect.stderr or ""),
        }
    return {
        "status": "ok",
        "base_reference": base_reference,
        "digest": digest,
    }


def inspect_bib_image(bib_reference: str, paths: Any, ctx: Any) -> dict[str, Any]:
    pull = run_podman(ctx, ["pull", bib_reference], paths.repo_root)
    if pull.returncode != 0:
        return {
            "status": "blocked",
            "reason": "bootc-image-builder pull failed",
            "reference": bib_reference,
            "digest": "",
            "output": (pull.stdout or "") + (pull.stderr or ""),
        }
    inspect = run_podman(
        ctx,
        ["inspect", "--format", "{{.Digest}}", bib_reference],
        paths.repo_root,
    )
    digest = (inspect.stdout or "").strip()
    if inspect.returncode != 0 or not digest:
        return {
            "status": "blocked",
            "reason": "bootc-image-builder inspect failed",
            "reference": bib_reference,
            "digest": "",
            "output": (inspect.stdout or "") + (inspect.stderr or ""),
        }
    return {
        "status": "ok",
        "reference": bib_reference,
        "digest": digest,
    }


def evaluate_preflight(repo_root: Path | None = None) -> dict[str, Any]:
    paths = build_paths(repo_root)
    manifest = load_manifest(paths.repo_root)
    image = manifest["image"]
    tooling = manifest["tooling"]
    base_reference = str(image.get("base_reference", DEFAULT_BASE_IMAGE))
    bib_reference = str(tooling.get("bootc_image_builder_reference", BIB_REFERENCE))

    uefi = detect_uefi_firmware(paths.evidence_dir)
    podman_ctx = resolve_podman_context(paths) if is_linux_x86_64() else None
    if podman_ctx is not None:
        write_podman_storage_evidence(paths, podman_ctx)

    checks: dict[str, Any] = {
        "platform": platform_summary(),
        "tools": {
            "podman": command_exists("podman"),
            "just": command_exists("just"),
            "uv": command_exists("uv"),
            "qemu-system-x86_64": command_exists("qemu-system-x86_64"),
        },
        "disk_free_gb": disk_free_gb(paths.repo_root),
        "kvm": {"available": kvm_available()} if is_linux_x86_64() else {"available": False},
        "linux_x86_64": is_linux_x86_64(),
        "uefi_firmware": {
            "available": uefi is not None,
            "candidate": uefi.candidate_label if uefi else "",
            "code_path": str(uefi.code_path) if uefi else "",
        },
        "podman_storage": {
            "strategy": podman_ctx.strategy if podman_ctx else "",
            "graphroot": str(paths.podman_graphroot),
            "storage_conf": str(paths.podman_storage_conf),
        },
        "base_image": inspect_base_image(base_reference, paths, podman_ctx)
        if is_linux_x86_64() and podman_ctx is not None
        else {
            "status": "blocked",
            "reason": "Layer B base verification requires Linux x86_64 with Podman",
            "base_reference": base_reference,
            "digest": "",
        },
        "bootc_image_builder": inspect_bib_image(bib_reference, paths, podman_ctx)
        if is_linux_x86_64() and podman_ctx is not None
        else {
            "status": "blocked",
            "reason": "Layer B tooling verification requires Linux x86_64 with Podman",
            "reference": bib_reference,
            "digest": "",
        },
    }

    blockers: list[str] = []
    if not checks["linux_x86_64"]:
        blockers.append("host is not Linux x86_64 (Raven Builder required)")
    if not checks["tools"]["podman"]:
        blockers.append("podman unavailable")
    if not checks["tools"]["uv"]:
        blockers.append("uv unavailable")
    if not checks["uefi_firmware"]["available"]:
        blockers.append("UEFI/OVMF firmware unavailable")
    if checks["disk_free_gb"] is not None and checks["disk_free_gb"] < 40:
        blockers.append("insufficient free disk (<40 GiB recommended for image builds)")
    if not checks["kvm"]["available"]:
        blockers.append("KVM unavailable (/dev/kvm missing)")
    if checks["base_image"]["status"] != "ok":
        blockers.append(
            f"base image verification blocked: {checks['base_image'].get('reason', 'unknown')}"
        )
    if checks["bootc_image_builder"]["status"] != "ok":
        blockers.append(
            "bootc-image-builder verification blocked: "
            f"{checks['bootc_image_builder'].get('reason', 'unknown')}"
        )

    if blockers:
        overall = "BLOCKED"
        exit_code = EXIT_BLOCKED
    else:
        overall = "PASS"
        exit_code = EXIT_PASS
        update_manifest_verified_digests(
            paths,
            base_digest=str(checks["base_image"]["digest"]),
            bib_digest=str(checks["bootc_image_builder"]["digest"]),
        )

    return {
        "overall": overall,
        "exit_code": exit_code,
        "blockers": blockers,
        "checks": checks,
        "manifest_base_reference": base_reference,
    }


def write_evidence(report: dict[str, Any], paths: Any) -> None:
    paths.evidence_dir.mkdir(parents=True, exist_ok=True)
    json_path = paths.evidence_dir / "builder-preflight.json"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    text_path = paths.evidence_dir / "builder-preflight.txt"
    lines = [
        f"overall: {report['overall']}",
        f"platform: {report['checks']['platform']}",
        f"blockers: {', '.join(report['blockers']) or 'none'}",
        f"base_reference: {report['manifest_base_reference']}",
        f"uefi_firmware: {report['checks']['uefi_firmware']}",
        f"podman_storage: {report['checks']['podman_storage']}",
    ]
    base = report["checks"]["base_image"]
    if base.get("digest"):
        lines.append(f"verified_base_digest: {base['digest']}")
    bib = report["checks"]["bootc_image_builder"]
    if bib.get("digest"):
        lines.append(f"verified_bib_digest: {bib['digest']}")
    text_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Raven Builder preflight")
    parser.add_argument("--repo-root", type=Path, default=None)
    args = parser.parse_args(argv)

    paths = build_paths(args.repo_root)
    report = evaluate_preflight(paths.repo_root)
    write_evidence(report, paths)

    print(f"Raven Builder preflight: {report['overall']}")
    for blocker in report["blockers"]:
        print(f"BLOCKER: {blocker}")
    if report["checks"]["base_image"].get("digest"):
        print(f"base digest: {report['checks']['base_image']['digest']}")
    if report["checks"]["bootc_image_builder"].get("digest"):
        print(f"bib digest: {report['checks']['bootc_image_builder']['digest']}")
    return int(report["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
