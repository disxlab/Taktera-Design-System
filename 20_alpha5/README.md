# Taktera Design System v4.0 Alpha.5 — verification report

Date: 2026-11-22. Status: **Alpha, not Beta and not production-certified**.

## Implemented and verified

- `@taktera/ui-core` packaged as `4.0.0-alpha.5` tarball, installed in a separate consumer using `npm ci --offline`; Node ESM public imports passed.
- Web Core notifications support Russian (default) and English controls and announcement region labels; existing zero-argument API remains valid.
- Native-number table sorting is numeric (e.g. `9, 25, 100`, not lexicographic `100, 25, 9`). String values still use locale-aware natural sorting.
- Guarded invalid label types, button `type`, malformed table rows and attempts to open unmounted dialogs.
- Base Chromium 53/53, extended Chromium 29/29, new installed-consumer Chromium 19/19, static 274/274, TypeScript declarations and JavaScript syntax passed.
- Prior approved design resources preserved byte-for-byte: see `20_alpha5/qa/brand-diff.json` for the actual comparison scope.

## Known limitations and release gates

- Chromium browser navigation to local HTTP address returns `ERR_BLOCKED_BY_ADMINISTRATOR` in this environment. HTTP module loading **not verified**. Browser tests inject content **from the installed npm package**.
- Real React package dependency resolution / build / React runtime test **not performed**. Files remain source-only.
- .NET SDK unavailable; Avalonia native Windows/macOS compilation **not performed**.
- Firefox, Safari, NVDA, VoiceOver, 200%/400% zoom, axe-core, target-app staging and production security review **not performed**.
- A/B application icons remain proposed; no design owner approval recorded.

## Install and run

```sh
cd 19_pilot/pilot-app
npm ci --offline
# from this folder on an unrestricted developer machine:
python -m http.server 8765
# open http://localhost:8765/
```

The consumer's `file:` dependency points at `../../20_alpha5/offline/taktera-ui-core-4.0.0-alpha.5.tgz`, which is included. No network access needed to install.

Beta cannot be assigned until outstanding gates above have evidence. See `ROADMAP-TO-BETA.md`.
