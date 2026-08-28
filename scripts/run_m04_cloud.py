#!/usr/bin/env python3
"""Orchestrate M04 cloud Builder gates (CircleCI thin layer over Justfile/scripts)."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.raven_build_config import build_paths, is_cloud_builder, resolve_repo_root

RESULT_PASS = "PASS_REVIEW_READY"
RESULT_BLOCKED = "BLOCKED"
RESULT_FAILED = "FAILED"


@dataclass
class GateResult:
    name: str
    command: list[str]
    exit_code: int
    duration_seconds: float
    output: str


def run_gate(name: str, command: list[str], cwd: Path, env: dict[str, str]) -> GateResult:
    start = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    duration = round(time.monotonic() - start, 2)
    output = (completed.stdout or "") + (completed.stderr or "")
    return GateResult(
        name=name,
        command=command,
        exit_code=int(completed.returncode),
        duration_seconds=duration,
        output=output,
    )


def gate_plan() -> list[tuple[str, list[str]]]:
    return [
        ("ci", ["just", "ci"]),
        ("builder-preflight", ["just", "builder-preflight"]),
        ("build-image", ["just", "build-image"]),
        ("image-check", ["just", "image-check"]),
        ("build-qcow2", ["just", "build-qcow2"]),
        ("artifact-metadata", ["just", "artifact-metadata"]),
        ("boot-smoke", ["just", "boot-smoke"]),
    ]


def write_candidate_handoff(paths: Any, *, review_ready: bool) -> None:
    fluxo_src = paths.repo_root / "docs" / "versions" / "v0.1" / "FLUXO.md"
    checkpoint_src = paths.repo_root / "docs" / "versions" / "v0.1" / "CHECKPOINT.md"
    out_dir = paths.evidence_dir / "candidate-handoff"
    out_dir.mkdir(parents=True, exist_ok=True)
    fluxo_text = fluxo_src.read_text(encoding="utf-8")
    checkpoint_text = checkpoint_src.read_text(encoding="utf-8")
    if review_ready:
        fluxo_text = fluxo_text.replace(
            "| M04 | Raven bootc base image + QCOW2 build path | 12 | BLOCKED |",
            "| M04 | Raven bootc base image + QCOW2 build path | 12 | REVIEW |",
        )
        checkpoint_note = (
            "Candidate handoff only (review ZIP): M04 = REVIEW after successful cloud gates. "
            "Source branch remains BLOCKED until Sol audit."
        )
    else:
        checkpoint_note = "Cloud gates did not fully pass; M04 remains BLOCKED in review handoff."
    (out_dir / "FLUXO.candidate.md").write_text(fluxo_text, encoding="utf-8")
    (out_dir / "CHECKPOINT.candidate.md").write_text(
        checkpoint_text + f"\n\n## Cloud candidate note\n\n{checkpoint_note}\n",
        encoding="utf-8",
    )


def gate_environment(name: str, base_env: dict[str, str]) -> dict[str, str]:
    env = base_env.copy()
    if name == "ci":
        env.pop("RAVEN_CLOUD_BUILDER", None)
    else:
        env["RAVEN_CLOUD_BUILDER"] = "1"
    return env


def run_m04_cloud(repo_root: Path | None = None) -> dict[str, Any]:
    paths = build_paths(repo_root)
    paths.evidence_dir.mkdir(parents=True, exist_ok=True)
    base_env = os.environ.copy()

    results: list[GateResult] = []
    overall = RESULT_PASS
    for name, command in gate_plan():
        result = run_gate(name, command, paths.repo_root, gate_environment(name, base_env))
        results.append(result)
        evidence_path = paths.evidence_dir / f"cloud-gate-{name}.txt"
        evidence_path.write_text(
            f"command: {' '.join(command)}\n"
            f"exit_code: {result.exit_code}\n"
            f"duration_seconds: {result.duration_seconds}\n"
            f"{'=' * 60}\n"
            f"{result.output}",
            encoding="utf-8",
        )
        if result.exit_code != 0:
            overall = RESULT_BLOCKED if result.exit_code == 2 else RESULT_FAILED
            print(result.output, end="")
            break

    review_ready = overall == RESULT_PASS
    write_candidate_handoff(paths, review_ready=review_ready)

    from scripts.create_review import create_review

    create_review(
        repo_root=paths.repo_root,
        increment="INC-002",
        run_quality=False,
        skip_ci=True,
        cloud_result=overall,
    )

    payload = {
        "result": overall,
        "cloud_builder": is_cloud_builder(),
        "gates": [
            {
                "name": r.name,
                "command": r.command,
                "exit_code": r.exit_code,
                "duration_seconds": r.duration_seconds,
            }
            for r in results
        ],
    }
    out = paths.evidence_dir / "run-m04-cloud.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run M04 cloud gates")
    parser.add_argument("--repo-root", type=Path, default=None)
    args = parser.parse_args(argv)
    root = resolve_repo_root(args.repo_root)
    payload = run_m04_cloud(root)
    print(f"run-m04-cloud: {payload['result']}")
    if payload["result"] == RESULT_PASS:
        return 0
    if payload["result"] == RESULT_BLOCKED:
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
