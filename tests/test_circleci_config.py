"""CircleCI config and cloud builder contracts (Prompt 002C)."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CIRCLECI_CONFIG = ROOT / ".circleci" / "config.yml"
ADR = ROOT / "docs" / "adr" / "0001-use-circleci-free-as-primary-v0.1-cloud-build-authority.md"
RUN_M04 = ROOT / "scripts" / "run_m04_cloud.py"


def test_justfile_exposes_circleci_validate() -> None:
    text = (ROOT / "Justfile").read_text(encoding="utf-8")
    assert "circleci-validate:" in text
    assert "circleci config validate" in text


def test_circleci_operator_doc_exists() -> None:
    doc = ROOT / "docs" / "versions" / "v0.1" / "CIRCLECI-OPERATOR.md"
    assert doc.is_file()
    body = doc.read_text(encoding="utf-8")
    assert "circleci auth login" in body
    assert CIRCLECI_CONFIG.is_file()


def test_circleci_run_m04_defaults_false() -> None:
    text = CIRCLECI_CONFIG.read_text(encoding="utf-8")
    assert re.search(r"run_m04:\s*\n\s*type:\s*boolean\s*\n\s*default:\s*false", text)


def test_circleci_heavy_m04_is_disabled() -> None:
    text = CIRCLECI_CONFIG.read_text(encoding="utf-8")
    assert "when: false" in text
    assert "m04-cloud-build" in text
    assert "Heavy M04 path disabled" in text


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
    assert ".qcow2" not in text


def test_adr_0001_is_superseded_for_disk_image() -> None:
    assert ADR.is_file()
    body = ADR.read_text(encoding="utf-8")
    assert "Superseded" in body
    assert "FALLBACK" in body or "fallback" in body.lower()


def test_run_m04_cloud_orchestrator_exists() -> None:
    text = RUN_M04.read_text(encoding="utf-8")
    assert "PASS_REVIEW_READY" in text
    assert "just ci-image" not in text  # uses explicit gate plan, not hidden duplicate logic only
    assert "builder-preflight" in text
    assert "boot-smoke" in text


def test_run_m04_cloud_ci_gate_omits_cloud_builder_env() -> None:
    from scripts.run_m04_cloud import gate_environment

    base = {"RAVEN_CLOUD_BUILDER": "1", "PATH": "/usr/bin"}
    ci_env = gate_environment("ci", base)
    assert "RAVEN_CLOUD_BUILDER" not in ci_env
    preflight_env = gate_environment("builder-preflight", base)
    assert preflight_env["RAVEN_CLOUD_BUILDER"] == "1"


def test_circleci_finalizes_via_repository_script() -> None:
    text = CIRCLECI_CONFIG.read_text(encoding="utf-8")
    assert "when: false" in text
    assert "<<" not in text


def test_circleci_rejects_shell_heredoc_syntax() -> None:
    text = CIRCLECI_CONFIG.read_text(encoding="utf-8")
    forbidden_tokens = ("<<'PY'", '<<"PY"', "<<PY", "<<EOF", "<<'EOF'", '<<"EOF"')
    for token in forbidden_tokens:
        assert token not in text, f"shell heredoc token must not appear in CircleCI config: {token}"

    for line_number, line in enumerate(text.splitlines(), start=1):
        if "<<" not in line:
            continue
        raise AssertionError(
            f"unexpected '<<' in disabled CircleCI config on line {line_number}: {line.strip()}"
        )
