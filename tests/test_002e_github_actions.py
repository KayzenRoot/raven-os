"""Prompt 002E contracts: GitHub Actions public M04 workflow."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "m04.yml"
FLUXO = ROOT / "docs" / "versions" / "v0.1" / "FLUXO.md"
CHECKPOINT = ROOT / "docs" / "versions" / "v0.1" / "CHECKPOINT.md"
CIRCLECI = ROOT / ".circleci" / "config.yml"
CIRRUS = ROOT / ".cirrus.yml"
BOOTSTRAP = ROOT / "scripts" / "github_actions_bootstrap.sh"
OPERATOR = ROOT / "docs" / "versions" / "v0.1" / "GITHUB-ACTIONS-OPERATOR.md"
ADR4 = ROOT / "docs" / "adr" / "0004-use-public-github-standard-runner-as-m04-build-authority.md"


def _workflow_text() -> str:
    assert WORKFLOW.is_file(), "missing .github/workflows/m04.yml"
    return WORKFLOW.read_text(encoding="utf-8")


def test_github_actions_workflow_is_workflow_dispatch_only() -> None:
    text = _workflow_text()
    assert "workflow_dispatch:" in text
    forbidden_triggers = (
        "push:",
        "pull_request:",
        "schedule:",
        "workflow_run:",
        "repository_dispatch:",
    )
    for forbidden in forbidden_triggers:
        assert forbidden not in text, f"forbidden trigger present: {forbidden}"


def test_github_actions_confirm_m04_defaults_false() -> None:
    text = _workflow_text()
    assert re.search(r"confirm_m04:\s*\n\s*description:", text)
    assert re.search(r"confirm_m04:\s*\n(?:\s+.+\n)*?\s+default:\s*false", text)


def test_github_actions_runner_is_ubuntu_24_04_standard() -> None:
    text = _workflow_text()
    assert "runs-on: ubuntu-24.04" in text
    for forbidden in (
        "ubuntu-slim",
        "ubuntu-latest",
        "macos",
        "windows",
        "larger",
        "self-hosted",
        "gpu",
    ):
        assert forbidden not in text.lower(), f"forbidden runner label: {forbidden}"


def test_github_actions_concurrency_lock() -> None:
    text = _workflow_text()
    assert "concurrency:" in text
    assert "group: raven-m04-heavy" in text
    assert "cancel-in-progress: false" in text


def test_github_actions_minimal_permissions() -> None:
    text = _workflow_text()
    assert "permissions:" in text
    assert "contents: read" in text
    lowered = text.lower()
    for forbidden in (
        "packages: write",
        "contents: write",
        "pull-requests: write",
        "id-token: write",
    ):
        assert forbidden not in lowered, f"forbidden permission: {forbidden}"


def test_github_actions_no_cache_action() -> None:
    text = _workflow_text().lower()
    assert "actions/cache" not in text


def test_github_actions_uploads_review_zip_only_short_retention() -> None:
    text = _workflow_text()
    assert "upload-artifact" in text
    assert "name: raven-review" in text
    assert "RAVEN-OS-V0.1-INC-002-REVIEW.zip" in text
    assert "retention-days: 1" in text
    assert ".qcow2" not in text


def test_github_actions_job_gates_public_repo_and_confirm() -> None:
    text = _workflow_text()
    assert "inputs.confirm_m04 == true" in text
    assert "github.event.repository.private == false" in text
    assert "PUBLIC REPOSITORY REQUIRED" in text


def test_github_actions_bootstrap_script_exists() -> None:
    assert BOOTSTRAP.is_file()
    text = BOOTSTRAP.read_text(encoding="utf-8")
    for token in ("podman", "qemu-system-x86", "ovmf", "uv", "just", "jq", "df -h"):
        assert token in text
    assert "BLOCKED - STANDARD GITHUB RUNNER DISK CAPACITY" in text
    assert "passwordless sudo" in text
    assert "conmon" in text
    assert "crun" in text


def test_cirrus_operational_path_retired() -> None:
    assert not CIRRUS.is_file()


def test_circleci_heavy_m04_remains_disabled() -> None:
    text = CIRCLECI.read_text(encoding="utf-8")
    assert "when: false" in text
    assert "Heavy M04 path disabled" in text


def test_adr_0004_exists_and_supersedes_cirrus_authority() -> None:
    assert ADR4.is_file()
    body = ADR4.read_text(encoding="utf-8")
    assert "ubuntu-24.04" in body
    assert "workflow_dispatch" in body
    assert "PUBLIC" in body
    assert "Supersedes" in body
    assert "ADR-0003" in body


def test_github_actions_operator_doc_exists() -> None:
    assert OPERATOR.is_file()
    text = OPERATOR.read_text(encoding="utf-8")
    assert "workflow_dispatch" in text
    assert "confirm_m04=true" in text
    assert "ubuntu-24.04" in text
    assert "PUBLIC" in text
    assert "gh workflow run" in text


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
