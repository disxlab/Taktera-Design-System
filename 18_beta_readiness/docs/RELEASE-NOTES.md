# Release notes — Taktera Design System v4.0 Alpha.3 (2026-11-22)

Alpha.3 is a deliberately limited **Beta-readiness milestone**, not v4.0 Beta.

## New executable deliverables

- `17_packages/web-core/package.json`: private `@taktera/ui-core` metadata with ESM, global script, and bundled CSS entrypoints.
- `17_packages/web-core/index.d.mts`: strongly typed public API for NodeNext ESM; supporting `index.d.ts` for tooling compatibility.
- `18_beta_readiness/offline/taktera-ui-core-4.0.0-alpha.3.tgz`: real offline-installable npm tarball. Install from this local file, not a registry.
- `18_beta_readiness/qa/verify_install.py`: clean temporary npm consumer, strict TypeScript contract check, ESM smoke, `--offline` only.
- `18_beta_readiness/qa/test_alpha3.py`: 29 extra Chromium checks and screenshots at desktop/mobile widths.
- `18_beta_readiness/ci/taktera-design-system.yml`: example platform CI jobs, **not executed as an actual CI run**.

## Corrections to Web UI Core

- Table `pageSize` validates positive integers; `rowKey` gets absolute indexes across pages.
- Pagination has an accessible navigation name and live page range.
- Error alerts use `role=alert`, while non-error notifications retain `role=status`.
- Theme root and toast tone validation; CSS forced-colors support.
- Existing source glyph, palettes, logos, and 248 frozen brand resources remain unchanged.

## Scope boundaries

- Browser tests use injected DOM/source in the local sandbox due to local navigation policy, not a production deployment.
- React TSX with actual dependencies was **not typechecked or bundled** here (npm registry unavailable).
- Avalonia sources were **not compiled** here (.NET SDK unavailable).
- NVDA, VoiceOver, axe-core and production pilot were not performed.
- Experimental A/B application icons have not been accepted.

See `BETA-ACCEPTANCE.md` for the release-blocking gates.
