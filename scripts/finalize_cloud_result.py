#!/usr/bin/env python3
"""Exit non-zero unless M04 cloud orchestration reached PASS_REVIEW_READY."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from scripts.raven_build_config import build_paths, resolve_repo_root

RESULT_PASS = "PASS_REVIEW_READY"


def finalize_cloud_result(repo_root: Path | None = None) -> int:
    paths = build_paths(repo_root)
    evidence = paths.evidence_dir / "run-m04-cloud.json"
    if not evidence.is_file():
        print("cloud result: FAILED (missing run-m04-cloud.json)", file=sys.stderr)
        return 1

    payload = json.loads(evidence.read_text(encoding="utf-8"))
    result = payload.get("result", "FAILED")
    print(f"cloud result: {result}")
    if result != RESULT_PASS:
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Finalize CircleCI job from cloud gate result")
    parser.add_argument("--repo-root", type=Path, default=None)
    args = parser.parse_args(argv)
    return finalize_cloud_result(resolve_repo_root(args.repo_root))


if __name__ == "__main__":
    raise SystemExit(main())
