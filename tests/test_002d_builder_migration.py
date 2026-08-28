"""Prompt 002D contracts: image-builder migration and Cirrus OSS M04 config."""

from __future__ import annotations

import re
from pathlib import Path

from scripts.image_builder_cli import image_builder_build_qcow2_args
from scripts.raven_build_config import ARCHIVED_BIB_REFERENCE, IMAGE_BUILDER_REFERENCE
from scripts.trigger_m04_pipeline import trigger_m04_pipeline

ROOT = Path(__file__).resolve().parents[1]
FLUXO = ROOT / "docs" / "versions" / "v0.1" / "FLUXO.md"
CHECKPOINT = ROOT / "docs" / "versions" / "v0.1" / "CHECKPOINT.md"
CIRRUS = ROOT / ".cirrus.yml"
CIRCLECI = ROOT / ".circleci" / "config.yml"


def test_preferred_image_builder_is_not_archived_bib() -> None:
    assert IMAGE_BUILDER_REFERENCE.startswith("ghcr.io/osbuild/image-builder")
    assert "bootc-image-builder" not in IMAGE_BUILDER_REFERENCE
    assert "centos-bootc/bootc-image-builder" in ARCHIVED_BIB_REFERENCE


def test_image_builder_qcow2_cli_uses_bootc_ref_not_archived_type_flag() -> None:
    args = image_builder_build_qcow2_args(
        bootc_ref="localhost/raven-os:0.1-dev",
        rootfs="btrfs",
    )
    assert args[0] == "build"
    assert "--bootc-ref" in args
    assert "localhost/raven-os:0.1-dev" in args
    assert "--bootc-default-fs" in args
    assert "btrfs" in args
    assert "--arch" in args
    assert "x86_64" in args
    assert "qcow2" in args
    assert "--type" not in args


def test_circleci_trigger_helper_refuses_heavy_m04() -> None:
    try:
        trigger_m04_pipeline()
        raise AssertionError("expected RuntimeError")
    except RuntimeError as exc:
        assert "disabled" in str(exc).lower()
        assert "cirrus" in str(exc).lower()


def test_cirrus_yml_exists_as_manual_heavy_m04() -> None:
    assert CIRRUS.is_file()
    text = CIRRUS.read_text(encoding="utf-8")
    assert "trigger_type: manual" in text
    assert "execution_lock:" in text
    assert "raven-os-m04-heavy" in text
    assert "timeout_in: 120m" in text
    assert "RAVEN_CLOUD_BUILDER" in text
    assert "just run-m04-cloud" in text
    assert "KayzenRoot/raven-os" in text
    assert "compute_engine_instance:" in text
    assert "image_project: cirrus-images" in text
    assert "nested_virtualization: true" in text
    assert "bootc-image-builder" not in text
    assert ".qcow2" not in text
    assert "RAVEN-OS-V0.1-INC-002-REVIEW.zip" in text
    assert re.search(r"^task:", text, re.MULTILINE)
    assert "trigger_type: automatic" not in text


def test_cirrus_does_not_use_k8s_container_executor() -> None:
    text = CIRRUS.read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.split("#", 1)[0].rstrip()
        if re.match(r"^\s*container:\s*$", stripped):
            raise AssertionError("M04 must not use a Kubernetes container executor")


def test_cirrus_bootstrap_installs_builder_tools() -> None:
    script = ROOT / "scripts" / "cirrus_bootstrap.sh"
    assert script.is_file()
    text = script.read_text(encoding="utf-8")
    for token in ("podman", "qemu-system-x86", "ovmf", "uv", "just"):
        assert token in text
    assert "ghcr.io" not in text  # product registry is not configured here


def test_circleci_heavy_m04_remains_disabled() -> None:
    text = CIRCLECI.read_text(encoding="utf-8")
    assert "when: false" in text
    assert "Heavy M04 path disabled" in text


def test_adr_0002_and_0003_exist() -> None:
    adr2 = ROOT / "docs" / "adr" / "0002-migrate-disk-image-builds-to-osbuild-image-builder.md"
    adr3 = ROOT / "docs" / "adr" / "0003-use-cirrus-ci-full-vm-as-primary-m04-build-authority.md"
    assert adr2.is_file()
    assert adr3.is_file()
    assert "osbuild/image-builder" in adr2.read_text(encoding="utf-8")
    assert "PUBLIC" in adr3.read_text(encoding="utf-8")
    assert ".cirrus.yml" in adr3.read_text(encoding="utf-8")


def test_circleci_blocker_evidence_exists() -> None:
    evidence = ROOT / "docs" / "versions" / "v0.1" / "CIRCLECI-M04-BLOCKER.md"
    text = evidence.read_text(encoding="utf-8")
    assert "permission denied" in text
    assert "05cfbf5a" in text
    assert "just ci" in text.lower() or "`just ci`" in text


def test_cirrus_operator_doc_exists() -> None:
    doc = ROOT / "docs" / "versions" / "v0.1" / "CIRRUS-OPERATOR.md"
    assert doc.is_file()
    text = doc.read_text(encoding="utf-8")
    assert "trigger_type: manual" in text
    assert "KayzenRoot/raven-os" in text
    assert "payment" in text.lower()


def test_canonical_progress_remains_20_percent() -> None:
    fluxo = FLUXO.read_text(encoding="utf-8")
    checkpoint = CHECKPOINT.read_text(encoding="utf-8")
    assert "VERSION PROGRESS = **20%**" in fluxo or "VERSION PROGRESS:** 20%" in checkpoint
    assert "COMPLETED POINTS:** 20" in checkpoint or "COMPLETED POINTS = **20**" in fluxo
    assert "| M04 |" in fluxo
    assert "BLOCKED" in fluxo
    m04 = re.search(r"\|\s*M04\s*\|[^|]+\|\s*12\s*\|([^|]+)\|", fluxo)
    assert m04 is not None
    assert "ACCEPTED" not in m04.group(1)
