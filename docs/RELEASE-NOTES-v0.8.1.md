# palinode v0.8.1 — Packaging Hotfix

**Release date:** 2026-04-27
**Previous:** v0.8.0 (2026-04-27)

This is a small packaging hotfix release.

## Fixed

- The PyPI package now includes the `palinode.diagnostics` modules added in `v0.8.0`.
- This ensures `palinode doctor` and its supporting diagnostics code are present in the published distribution, not just the GitHub source tree.

## Upgrade

```bash
pip install --upgrade palinode
```

## Full changelog

See [CHANGELOG.md](CHANGELOG.md) for the full release history.
