#!/usr/bin/env python3
"""Refuse CircleCI heavy M04 triggers (Prompt 002D / ADR-0003)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from scripts.raven_build_config import resolve_repo_root


def trigger_m04_pipeline(
    *,
    repo_root: Path | None = None,
    branch: str = "main",
) -> dict[str, Any]:
    del repo_root, branch
    raise RuntimeError(
        "CircleCI heavy M04 is disabled (Prompt 002D / ADR-0003). "
        "Do not retry osbuild/QCOW2 on CircleCI. "
        "Use Cirrus m04-cirrus-builder (.cirrus.yml) via a main commit containing [m04]."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Refuse disabled CircleCI M04 trigger")
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--branch", default="main")
    args = parser.parse_args(argv)
    resolve_repo_root(args.repo_root)
    try:
        trigger_m04_pipeline(repo_root=args.repo_root, branch=args.branch)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
