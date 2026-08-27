# Raven OS image source and build metadata (M04)

See [image-source.toml](image-source.toml) for the machine-readable base/tooling manifest.

Refresh verified base digest on the Raven Builder:

```bash
just builder-preflight
```

Build artifacts are written under `.build/` (gitignored).
