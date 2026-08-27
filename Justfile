# Raven OS — local quality, image build and review facade
# Requires: uv. Optional host tool: just. Fallback commands: docs/INDEX.md

set windows-shell := ["powershell.exe", "-NoProfile", "-Command"]

default:
    @just --list

test:
    uv run pytest -q

lint:
    uv run ruff check .

format-check:
    uv run ruff format --check .

format:
    uv run ruff format .

typecheck:
    uv run mypy src scripts tests

# Fast repository gates (no multi-GB image downloads)
ci: test lint format-check typecheck

# M04 Builder diagnostics (Layer B; may return BLOCKED on non-Builder hosts)
builder-preflight:
    uv run python -m scripts.builder_preflight

build-image:
    uv run python -m scripts.build_image

image-check:
    uv run python -m scripts.image_check

build-qcow2:
    uv run python -m scripts.build_qcow2

artifact-metadata:
    uv run python -m scripts.artifact_metadata

boot-smoke:
    uv run python -m scripts.boot_smoke

# Expensive real-image gates for Raven Builder / CircleCI (not part of fast ci)
ci-image: builder-preflight build-image image-check build-qcow2 artifact-metadata boot-smoke

# CircleCI/cloud orchestrator (sets RAVEN_CLOUD_BUILDER=1)
run-m04-cloud:
    uv run python -m scripts.run_m04_cloud

# Validate CircleCI config before cloud spend (requires CircleCI CLI)
circleci-validate:
    circleci config validate

# Trigger manual M04 cloud pipeline (boolean run_m04 via API JSON)
trigger-m04-cloud:
    uv run python -m scripts.trigger_m04_pipeline

review:
    uv run python scripts/create_review.py --increment INC-002
