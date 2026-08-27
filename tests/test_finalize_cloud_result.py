"""Unit tests for CircleCI cloud result finalization."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.finalize_cloud_result import finalize_cloud_result


def test_finalize_cloud_result_passes_on_review_ready(tmp_path: Path) -> None:
    evidence_dir = tmp_path / ".build" / "evidence"
    evidence_dir.mkdir(parents=True)
    (evidence_dir / "run-m04-cloud.json").write_text(
        json.dumps({"result": "PASS_REVIEW_READY"}) + "\n",
        encoding="utf-8",
    )
    assert finalize_cloud_result(tmp_path) == 0


def test_finalize_cloud_result_fails_when_evidence_missing(tmp_path: Path) -> None:
    assert finalize_cloud_result(tmp_path) == 1
