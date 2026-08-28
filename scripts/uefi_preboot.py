#!/usr/bin/env python3
"""UEFI/OVMF pre-boot validation for M04 boot smoke."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.raven_build_config import (
    UefiFirmware,
    build_paths,
    iter_ovmf_firmware_candidates,
)


@dataclass(frozen=True)
class UefiPrebootResult:
    ok: bool
    error: str | None
    firmware: UefiFirmware | None
    evidence: dict[str, Any]


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_pair(code: Path, vars_template: Path, evidence_dir: Path) -> UefiFirmware | None:
    if not code.is_file() or not os.access(code, os.R_OK):
        return None
    if not vars_template.is_file() or not os.access(vars_template, os.R_OK):
        return None
    runtime_vars = evidence_dir / f"OVMF_VARS.runtime.{code.name}.fd"
    shutil.copy2(vars_template, runtime_vars)
    if not runtime_vars.is_file() or not os.access(runtime_vars, os.W_OK):
        return None
    return UefiFirmware(
        code_path=code,
        vars_template_path=vars_template,
        vars_runtime_path=runtime_vars,
        candidate_label=f"{code} + {vars_template}",
    )


def validate_uefi_preboot(evidence_dir: Path | None = None) -> UefiPrebootResult:
    paths = build_paths()
    evidence_dir = evidence_dir or paths.evidence_dir
    evidence_dir.mkdir(parents=True, exist_ok=True)
    candidates_evidence: list[dict[str, Any]] = []

    for code, vars_template in iter_ovmf_firmware_candidates():
        entry: dict[str, Any] = {
            "code_path": str(code),
            "vars_template_path": str(vars_template),
            "code_exists": code.is_file(),
            "vars_exists": vars_template.is_file(),
        }
        firmware = _validate_pair(code, vars_template, evidence_dir)
        if firmware is None:
            entry["usable"] = False
            candidates_evidence.append(entry)
            continue
        entry.update(
            {
                "usable": True,
                "code_size": code.stat().st_size,
                "vars_template_size": vars_template.stat().st_size,
                "code_sha256": _sha256_file(code),
                "vars_template_sha256": _sha256_file(vars_template),
                "runtime_vars_path": str(firmware.vars_runtime_path),
            }
        )
        candidates_evidence.append(entry)
        evidence: dict[str, Any] = {
            "ok": True,
            "selected_candidate": firmware.candidate_label,
            "code_path": str(firmware.code_path),
            "vars_template_path": str(firmware.vars_template_path),
            "runtime_vars_path": str(firmware.vars_runtime_path),
            "candidates": candidates_evidence,
        }
        return UefiPrebootResult(True, None, firmware, evidence)

    evidence = {"ok": False, "candidates": candidates_evidence}
    return UefiPrebootResult(
        False,
        "no usable paired UEFI/OVMF firmware found",
        None,
        evidence,
    )


def write_uefi_preboot_evidence(evidence_dir: Path | None = None) -> UefiPrebootResult:
    paths = build_paths()
    target = evidence_dir or paths.evidence_dir
    target.mkdir(parents=True, exist_ok=True)
    result = validate_uefi_preboot(target)
    out = target / "uefi-preboot.json"
    out.write_text(json.dumps(result.evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    result = write_uefi_preboot_evidence()
    if not result.ok:
        print(f"error: {result.error}", file=sys.stderr)
        return 1
    assert result.firmware is not None
    print(f"uefi-preboot: PASS ({result.firmware.candidate_label})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
