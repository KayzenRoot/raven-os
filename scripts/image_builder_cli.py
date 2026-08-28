#!/usr/bin/env python3
"""Current osbuild/image-builder CLI argument builder (M04, ADR-0002)."""

from __future__ import annotations


def image_builder_build_qcow2_args(
    *,
    bootc_ref: str,
    rootfs: str,
    arch: str = "x86_64",
    output_dir: str = "/output",
) -> list[str]:
    """Return the current image-builder bootc qcow2 CLI (not archived BIB).

    Flags follow published osbuild/image-builder usage. Builder hosts must still
    capture ``image-builder --help`` / ``build --help`` in evidence before treating
    a new flag as mandatory.
    """
    return [
        "build",
        "--arch",
        arch,
        "--bootc-ref",
        bootc_ref,
        "--bootc-default-fs",
        rootfs,
        "--output-dir",
        output_dir,
        "qcow2",
    ]


def image_builder_help_args() -> list[str]:
    return ["--help"]


def image_builder_build_help_args() -> list[str]:
    return ["build", "--help"]
