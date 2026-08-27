"""Bootstrap / FLUXO / package import contracts for INC-001."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import raven_adapters
import raven_core
import raven_ui

ROOT = Path(__file__).resolve().parents[1]
FLUXO = ROOT / "docs" / "versions" / "v0.1" / "FLUXO.md"

REQUIRED_FILES = [
    "AGENTS.md",
    "Justfile",
    "pyproject.toml",
    "uv.lock",
    "Containerfile",
    ".gitignore",
    "os/image-source.toml",
    "docs/INDEX.md",
    "docs/architecture/CODE-ATLAS.md",
    "docs/architecture/MODULE-REGISTRY.md",
    "docs/architecture/TEST-MAP.md",
    "docs/adr/INDEX.md",
    "docs/versions/v0.1/FLUXO.md",
    "docs/versions/v0.1/CHECKPOINT.md",
    "docs/versions/v0.1/DEFINITION-OF-DONE.md",
    "scripts/create_review.py",
    "src/raven_core/__init__.py",
    "src/raven_ui/__init__.py",
    "src/raven_adapters/__init__.py",
]

FORBIDDEN_DEPENDENCY_NAMES = {
    "hermes",
    "hermes-agent",
    "pyside6",
    "PySide6",
    "dbus-next",
    "dbus-python",
    "openai",
    "anthropic",
    "langchain",
    "chromadb",
    "fastapi",
    "flask",
    "django",
    "torch",
    "tensorflow",
}


def test_required_operational_files_exist() -> None:
    missing = [rel for rel in REQUIRED_FILES if not (ROOT / rel).is_file()]
    assert not missing, f"missing required files: {missing}"


def test_fluxo_total_weights_equal_100() -> None:
    text = FLUXO.read_text(encoding="utf-8")
    points = {
        mid: int(pts)
        for mid, pts in re.findall(
            r"\|\s*(M\d{2})\s*\|[^|]+\|\s*(\d+)\s*\|",
            text,
        )
    }
    assert len(points) == 10, f"expected M01-M10, got {sorted(points)}"
    assert sum(points.values()) == 100


def test_fluxo_m01_m02_m03_equal_20() -> None:
    text = FLUXO.read_text(encoding="utf-8")
    points = {
        mid: int(pts)
        for mid, pts in re.findall(
            r"\|\s*(M\d{2})\s*\|[^|]+\|\s*(\d+)\s*\|",
            text,
        )
    }
    assert points["M01"] + points["M02"] + points["M03"] == 20


def test_fluxo_completed_points_after_sol_acceptance() -> None:
    text = FLUXO.read_text(encoding="utf-8")
    assert re.search(r"COMPLETED POINTS\s*=\s*\*\*20\*\*", text)
    assert re.search(r"VERSION PROGRESS\s*=\s*\*\*20%\*\*", text)


def test_package_imports_succeed() -> None:
    assert raven_core.__version__
    assert raven_ui.__version__
    assert raven_adapters.__version__


def test_no_runtime_heavy_later_dependencies() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project_deps = list(pyproject.get("project", {}).get("dependencies", []))
    optional = pyproject.get("project", {}).get("optional-dependencies", {})
    for group_deps in optional.values():
        project_deps.extend(group_deps)

    lowered = " ".join(project_deps).lower()
    for name in FORBIDDEN_DEPENDENCY_NAMES:
        assert name.lower() not in lowered, f"forbidden dependency present: {name}"

    lock = ROOT / "uv.lock"
    if lock.is_file():
        lock_text = lock.read_text(encoding="utf-8").lower()
        for name in ("pyside6", "hermes", "fastapi", "torch", "chromadb", "langchain"):
            assert f'name = "{name}"' not in lock_text, f"forbidden locked package: {name}"
