# v4.0 Alpha.2 · Reusable Component Packages

New independent components, in addition to (not replacing) the alpha.1 reference UI:

| Package | Files | Status |
| --- | --- | --- |
| Web Core | `web-core/taktera-ui.js`, `index.mjs`, `taktera-ui.css` | Executable, tested in Chromium, installable by copying files; not npm published |
| React/TypeScript | `react/src/index.tsx`, `react/package.json` | Source implementation; syntactic transpilation checked, full TS type/build not tested (npm registry unavailable) |
| Avalonia | `avalonia/TkControls.axaml`, `TkFieldStyles.axaml`, `sample/` | XML/resource references checked, native .NET build not tested (.NET SDK unavailable) |
| Demo | `samples/index.html` | Offline classic-script demo with 6 products and 2 themes |
| QA | `qa/test_web.py`, `validate_static.py`, `CI-TEMPLATE.yml` | Browser smoke + static checks; CI workflow template not executed |

Use `samples/index.html` to review actual Web Core components, while `13_ui_kit/index.html` remains the alpha.1 full ERP reference application. See `MIGRATION.md` and `DECISIONS-REQUIRED.md`.

`web-core/build.py --check` verifies CSS against the canonical v3.3 tokens. The Web core constructs DOM with text nodes for all user-facing data. No network requests or actual customer data exist.

## Alpha.3 — packaging & Beta readiness (2026-11-22)

The private Web Core now has an offline-installable npm tarball (`18_beta_readiness/offline/`), strict ESM TypeScript declarations and regression tests: 53 historical Chromium checks + 29 new focused checks, alongside 274 existing static checks. See `18_beta_readiness/docs/RELEASE-NOTES.md` and `18_beta_readiness/docs/BETA-ACCEPTANCE.md` for verified results and non-verified gates.

**React and Avalonia remain source-only** pending real npm/.NET SDK installs and builds. No change to the 248 approved frozen brand files or experimental icon status.
