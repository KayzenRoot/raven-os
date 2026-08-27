# Test Map — Raven OS V0.1

## Eventual proof categories (M01–M10)

| ID | Expected proof categories (eventually) |
|----|----------------------------------------|
| M01 | File/contract existence; FLUXO weight integrity; doc consistency |
| M02 | `just` facade; lint/format/typecheck/test gates exit nonzero on failure |
| M03 | Review ZIP contents; exclusion denylist; no path escape; valid `review.json` |
| M04 | Containerfile/manifest contracts; Builder preflight; OCI build; QCOW2 + SHA-256; bounded boot smoke |
| M05 | ravend start/stop; D-Bus contract conformance; session lifecycle |
| M06 | CognitiveBackend interface; Hermes adapter isolation; no live keys in repo |
| M07 | Migration apply/rollback; WAL mode; session/memory persistence |
| M08 | Tool allowlist; audit/correlation IDs; least-privilege checks |
| M09 | UI smoke; QML load; session UX wiring to ravend |
| M10 | Full VM acceptance chain; reboot persistence; review ZIP + objective tests |

## INC-001 automated tests

| Test module | Covers |
|-------------|--------|
| `tests/test_bootstrap_contracts.py` | Required operational files; FLUXO totals; Sol acceptance state (20 points); package imports; no heavy later deps |
| `tests/test_review_generator.py` | Review dir/ZIP; exclusions; no traversal; valid `review.json` |

## INC-002 automated tests (Layer A)

| Test module | Covers |
|-------------|--------|
| `tests/test_m04_image_contracts.py` | Containerfile/manifest; UEFI/OVMF boot smoke contract; shared Podman storage; path guards; M01–M03 ACCEPTED; M04 not ACCEPTED |

## Quality / image commands

| Command | Layer | Purpose |
|---------|-------|---------|
| `just test` … `just ci` | A | Fast repository gates |
| `just builder-preflight` | B | Builder capability + base pull/inspect |
| `just build-image` | B | Raven OCI build |
| `just image-check` | B | OCI inspection |
| `just build-qcow2` | B | QCOW2 via bootc-image-builder |
| `just artifact-metadata` | B | SHA-256 provenance |
| `just boot-smoke` | B | Bounded QEMU boot proof |
| `just ci-image` | B | Aggregate expensive gates (Builder only) |
| `just review` | A/B | Review ZIP (metadata/logs, not QCOW2 blobs) |
