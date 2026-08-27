"""CircleCI config and cloud builder contracts (Prompt 002C)."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CIRCLECI_CONFIG = ROOT / ".circleci" / "config.yml"
ADR = ROOT / "docs" / "adr" / "0001-use-circleci-free-as-primary-v0.1-cloud-build-authority.md"
RUN_M04 = ROOT / "scripts" / "run_m04_cloud.py"


def test_circleci_config_exists() -> None:
    assert CIRCLECI_CONFIG.is_file()


def test_circleci_run_m04_defaults_false() -> None:
    text = CIRCLECI_CONFIG.read_text(encoding="utf-8")
    assert re.search(r"run_m04:\s*\n\s*type:\s*boolean\s*\n\s*default:\s*false", text)


def test_circleci_heavy_workflow_is_manual_only() -> None:
    text = CIRCLECI_CONFIG.read_text(encoding="utf-8")
    assert "when: << pipeline.parameters.run_m04 >>" in text
    assert "m04-cloud-build" in text


def test_circleci_uses_machine_executor_medium_ubuntu() -> None:
    text = CIRCLECI_CONFIG.read_text(encoding="utf-8")
    assert "version: 2.1" in text
    assert "machine:" in text
    assert "ubuntu-2604:current" in text
    assert "resource_class: medium" in text


def test_circleci_has_no_dlc_or_remote_caches() -> None:
    text = CIRCLECI_CONFIG.read_text(encoding="utf-8").lower()
    assert "docker_layer_caching" not in text
    assert "setup_remote_docker" not in text
    assert "save_cache" not in text
    assert "persist_to_workspace" not in text


def test_circleci_stores_only_review_zip_artifact() -> None:
    text = CIRCLECI_CONFIG.read_text(encoding="utf-8")
    assert "store_artifacts:" in text
    assert "RAVEN-OS-V0.1-INC-002-REVIEW.zip" in text
    assert ".qcow2" not in text


def test_adr_exists_for_circleci_primary_builder() -> None:
    assert ADR.is_file()
    body = ADR.read_text(encoding="utf-8")
    assert "CircleCI Free" in body
    assert "FALLBACK" in body or "fallback" in body.lower()


def test_run_m04_cloud_orchestrator_exists() -> None:
    text = RUN_M04.read_text(encoding="utf-8")
    assert "PASS_REVIEW_READY" in text
    assert "just ci-image" not in text  # uses explicit gate plan, not hidden duplicate logic only
    assert "builder-preflight" in text
    assert "boot-smoke" in text
