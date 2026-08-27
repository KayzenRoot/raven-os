#!/usr/bin/env python3
"""Trigger the manual M04 CircleCI pipeline with a real boolean run_m04 parameter."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from scripts.raven_build_config import resolve_repo_root


def load_project_metadata(repo_root: Path) -> dict[str, str]:
    info_path = repo_root / ".circleci" / "info.yml"
    if not info_path.is_file():
        raise FileNotFoundError(
            "missing .circleci/info.yml; run `circleci project link` from the repository root"
        )
    text = info_path.read_text(encoding="utf-8")
    project_id = ""
    project_slug = ""
    in_project = False
    for line in text.splitlines():
        if line.startswith("project:"):
            in_project = True
            continue
        if in_project and line and not line.startswith((" ", "\t")):
            break
        if not in_project:
            continue
        id_match = re.match(r"\s+id:\s*(\S+)", line)
        if id_match:
            project_id = id_match.group(1)
        slug_match = re.match(r"\s+slug:\s*(\S+)", line)
        if slug_match:
            project_slug = slug_match.group(1)
    if not project_slug:
        raise RuntimeError("could not parse project slug from .circleci/info.yml")
    return {"project_slug": project_slug, "project_id": project_id}


def list_pipeline_definitions(project_slug: str) -> list[dict[str, Any]]:
    completed = subprocess.run(
        ["circleci", "pipeline", "list", "--project", project_slug, "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout or "pipeline list failed").strip())
    payload = json.loads(completed.stdout or "[]")
    if not isinstance(payload, list):
        raise RuntimeError("unexpected pipeline list response")
    return payload


def trigger_m04_pipeline(
    *,
    repo_root: Path | None = None,
    branch: str = "main",
) -> dict[str, Any]:
    root = resolve_repo_root(repo_root)
    meta = load_project_metadata(root)
    definitions = list_pipeline_definitions(meta["project_slug"])
    if not definitions:
        raise RuntimeError(f"no pipeline definitions found for {meta['project_slug']}")

    definition_id = str(definitions[0]["id"])
    payload = {
        "definition_id": definition_id,
        "config": {"branch": branch},
        "checkout": {"branch": branch},
        "parameters": {"run_m04": True},
    }
    body_path = root / ".build" / "evidence" / "trigger-m04-payload.json"
    body_path.parent.mkdir(parents=True, exist_ok=True)
    body_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    completed = subprocess.run(
        [
            "circleci",
            "api",
            f"api/v2/project/{meta['project_slug']}/pipeline/run",
            "-d",
            f"@{body_path.as_posix()}",
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=root,
    )
    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout or "pipeline trigger failed").strip()
        raise RuntimeError(message)
    response_obj: dict[str, Any] = json.loads(completed.stdout or "{}")
    response_obj["project_slug"] = meta["project_slug"]
    response_obj["definition_id"] = definition_id
    return response_obj


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Trigger CircleCI M04 pipeline (run_m04=true)")
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--branch", default="main")
    args = parser.parse_args(argv)
    try:
        response = trigger_m04_pipeline(repo_root=args.repo_root, branch=args.branch)
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    run_id = response.get("id", "")
    number = response.get("number")
    state = response.get("state")
    print(f"trigger-m04: run_id={run_id} number={number} state={state}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
