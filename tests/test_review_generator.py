"""Tests for scripts/create_review.py review packaging contracts."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest
from scripts.create_review import (
    create_review,
    is_within_root,
    should_exclude,
    zip_name_for,
)


def _seed_minimal_repo(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "AGENTS.md").write_text("# agents\n", encoding="utf-8")
    (root / "Justfile").write_text("test:\n    echo ok\n", encoding="utf-8")
    (root / "pyproject.toml").write_text(
        '[project]\nname = "raven-os"\nversion = "0.1.0"\nrequires-python = ">=3.12"\n',
        encoding="utf-8",
    )
    (root / ".gitignore").write_text(".review/\n", encoding="utf-8")
    docs = root / "docs" / "versions" / "v0.1"
    docs.mkdir(parents=True)
    (docs / "FLUXO.md").write_text(
        "COMPLETED POINTS = **0**\nVERSION PROGRESS = **0%**\n", encoding="utf-8"
    )
    (docs / "CHECKPOINT.md").write_text("Next step: Await Sol audit\n", encoding="utf-8")
    (docs / "DEFINITION-OF-DONE.md").write_text("DoD\n", encoding="utf-8")
    (root / "docs" / "INDEX.md").write_text("index\n", encoding="utf-8")
    arch = root / "docs" / "architecture"
    arch.mkdir(parents=True)
    (arch / "CODE-ATLAS.md").write_text("atlas\n", encoding="utf-8")
    (arch / "MODULE-REGISTRY.md").write_text("registry\n", encoding="utf-8")
    (arch / "TEST-MAP.md").write_text("tests\n", encoding="utf-8")
    (root / "docs" / "adr").mkdir(parents=True)
    (root / "docs" / "adr" / "INDEX.md").write_text("adr\n", encoding="utf-8")
    for pkg in ("raven_core", "raven_ui", "raven_adapters"):
        pkg_dir = root / "src" / pkg
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text('__version__ = "0.1.0"\n', encoding="utf-8")
    scripts = root / "scripts"
    scripts.mkdir()
    # Importable copy of generator is used from real package; fixture only needs tree.
    (scripts / "create_review.py").write_text("# placeholder\n", encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests" / "test_bootstrap_contracts.py").write_text("# placeholder\n", encoding="utf-8")


def test_should_exclude_secrets_and_heavy_artifacts(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    cases = [
        root / ".env",
        root / ".env.local",
        root / "credentials.json",
        root / "secrets.json",
        root / "id_rsa",
        root / "server.pem",
        root / "disk.qcow2",
        root / "image.raw",
        root / "model.gguf",
        root / "weights.safetensors",
        root / "RAVEN-OS-V0.1-INC-001-REVIEW.zip",
        root / ".venv" / "lib" / "x.py",
        root / "__pycache__" / "x.pyc",
        root / ".git" / "config",
    ]
    (root / ".venv" / "lib").mkdir(parents=True)
    (root / "__pycache__").mkdir()
    (root / ".git").mkdir()
    for path in cases:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x", encoding="utf-8")
        assert should_exclude(path, root), f"expected exclude: {path}"


def test_does_not_traverse_outside_repository_root(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    outside = tmp_path / "outside.txt"
    root.mkdir()
    outside.write_text("secret", encoding="utf-8")
    assert not is_within_root(root, outside)
    assert should_exclude(outside, root)


def test_create_review_without_git(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _seed_minimal_repo(root)
    # Drop sensitive fixtures that must not appear in ZIP
    (root / ".env").write_text("API_KEY=should-not-appear\n", encoding="utf-8")
    (root / "id_rsa").write_text("PRIVATE KEY FIXTURE\n", encoding="utf-8")
    (root / "credentials.json").write_text("{}\n", encoding="utf-8")
    (root / "disk.qcow2").write_bytes(b"qcow")
    (root / "model.gguf").write_bytes(b"gguf")
    nested = root / ".review" / "old" / "RAVEN-OS-V0.1-INC-000-REVIEW.zip"
    nested.parent.mkdir(parents=True)
    nested.write_bytes(b"old")
    venv_file = root / ".venv" / "pyvenv.cfg"
    venv_file.parent.mkdir()
    venv_file.write_text("home = x\n", encoding="utf-8")
    cache = root / "__pycache__" / "x.pyc"
    cache.parent.mkdir()
    cache.write_bytes(b"pyc")

    out = root / ".review"
    zip_path = create_review(repo_root=root, out_dir=out, increment="INC-001", run_quality=False)
    assert zip_path.is_file()
    assert zip_path.name == zip_name_for("INC-001")
    assert (out / "REVIEW.md").is_file()
    assert (out / "review.json").is_file()
    assert (out / "git-status.txt").is_file()
    assert "git metadata absent" in (out / "git-status.txt").read_text(encoding="utf-8")

    payload = json.loads((out / "review.json").read_text(encoding="utf-8"))
    assert payload["version"] == "V0.1"
    assert payload["increment"] == "INC-001"
    assert payload["status"] == "REVIEW"
    assert payload["completed_points"] == 0

    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())
    assert "REVIEW.md" in names
    assert "review.json" in names
    joined = "\n".join(names).lower()
    for banned in (
        ".env",
        "id_rsa",
        "credentials.json",
        ".git/",
        ".venv/",
        "__pycache__",
        "disk.qcow2",
        "model.gguf",
        "inc-000-review.zip",
    ):
        assert banned.lower() not in joined, f"ZIP unexpectedly contains {banned}"


def test_out_dir_outside_root_rejected(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _seed_minimal_repo(root)
    outside = tmp_path / "outside-review"
    with pytest.raises(ValueError, match="inside the repository root"):
        create_review(repo_root=root, out_dir=outside, run_quality=False)
