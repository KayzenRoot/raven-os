#!/usr/bin/env python3
"""Generate SHA-256 and provenance metadata for build artifacts (M04)."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from scripts.raven_build_config import build_paths, ensure_within_build_root


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_metadata(repo_root: Path | None = None) -> int:
    paths = build_paths(repo_root)
    paths.evidence_dir.mkdir(parents=True, exist_ok=True)
    artifacts: list[dict[str, str | int]] = []

    for qcow2 in sorted(paths.qcow2_dir.glob("*.qcow2")):
        qcow2 = ensure_within_build_root(paths, qcow2)
        stat = qcow2.stat()
        artifacts.append(
            {
                "path": str(qcow2.relative_to(paths.repo_root)),
                "size_bytes": stat.st_size,
                "sha256": sha256_file(qcow2),
            }
        )

    payload = {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "artifacts": artifacts,
    }
    out = paths.evidence_dir / "artifact-metadata.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not artifacts:
        print("warning: no QCOW2 artifacts found (metadata records empty set)")
        return 0
    print(f"metadata: {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Artifact metadata")
    parser.add_argument("--repo-root", type=Path, default=None)
    args = parser.parse_args(argv)
    return write_metadata(args.repo_root)


if __name__ == "__main__":
    raise SystemExit(main())
