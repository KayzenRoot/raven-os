"""Prompt 002D contracts retained after 002E: image-builder migration."""

from __future__ import annotations

from pathlib import Path

from scripts.image_builder_cli import image_builder_build_qcow2_args
from scripts.raven_build_config import ARCHIVED_BIB_REFERENCE, IMAGE_BUILDER_REFERENCE
from scripts.trigger_m04_pipeline import trigger_m04_pipeline

ROOT = Path(__file__).resolve().parents[1]
CIRCLECI = ROOT / ".circleci" / "config.yml"
CIRRUS = ROOT / ".cirrus.yml"


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
        assert "github actions" in str(exc).lower()


def test_circleci_heavy_m04_remains_disabled() -> None:
    text = CIRCLECI.read_text(encoding="utf-8")
    assert "when: false" in text
    assert "Heavy M04 path disabled" in text


def test_adr_0002_and_0004_exist() -> None:
    adr2 = ROOT / "docs" / "adr" / "0002-migrate-disk-image-builds-to-osbuild-image-builder.md"
    adr4 = (
        ROOT / "docs" / "adr" / "0004-use-public-github-standard-runner-as-m04-build-authority.md"
    )
    assert adr2.is_file()
    assert adr4.is_file()
    assert "osbuild/image-builder" in adr2.read_text(encoding="utf-8")
    assert "workflow_dispatch" in adr4.read_text(encoding="utf-8")


def test_circleci_blocker_evidence_exists() -> None:
    evidence = ROOT / "docs" / "versions" / "v0.1" / "CIRCLECI-M04-BLOCKER.md"
    text = evidence.read_text(encoding="utf-8")
    assert "permission denied" in text
    assert "05cfbf5a" in text
    assert "just ci" in text.lower() or "`just ci`" in text


def test_cirrus_yml_removed_after_002e() -> None:
    assert not CIRRUS.is_file()
