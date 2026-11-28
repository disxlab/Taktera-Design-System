# @taktera/ui-web-core · alpha.2

Dependency-free DOM component library. **Actual reusable library**, separate from `13_ui_kit` reference application.

- `taktera-ui.js` — classic `<script>` entrypoint for the local, offline `samples/index.html`, provides `globalThis.TakteraUI`.
- `index.mjs` — ESM entrypoint for bundlers/hosted pages.
- `taktera-ui.css` — generated, self-contained tokens + components for product/theme styling.
- API: `setTheme`, `button`, `field`, `select`, `checkbox`, `status`, `alert`, `card`, `tabs`, `dialog`, `table`, `toastRegion`.

All user-provided labels and row values enter via `textContent`, not `innerHTML`. The table is intended for small, client-side datasets; server sorting, virtualization, mutations, permissions and domain validation are out of scope. `dialog` requires attachment to DOM before `open()`; caller owns its lifecycle. Theme scope is inherited from the `.tku-root[data-product][data-theme]` element.

**Tests:** Playwright/Chromium functional keyboard and 320/390/1440 px checks in `../qa/test_web.py` using source injection due to container navigation restrictions.

## Alpha.3 — installable offline package

The Web Core now ships as **private** `@taktera/ui-core@4.0.0-alpha.3` with `package.json`, NodeNext ESM declaration `index.d.mts`, default and named exports, a CSS subpath and a classic-script subpath. It is not published on npm.

Run `npm test` in this directory to syntax-check JavaScript and compile the strict public TypeScript contract. Rebuild the local tarball with `npm pack --offline`; the complete Alpha.3 archive already contains one at `18_beta_readiness/offline/`.

An automated offline clean-project installation and ESM import check is provided by `18_beta_readiness/qa/verify_install.py`. See also `18_beta_readiness/docs/OFFLINE-INSTALL.md`.

Web Core Alpha.3 fixes absolute row keys across table pages, validates invalid `pageSize`/tones, adds an accessible name and live range to its pager, uses alert semantics for critical errors and supports Windows High Contrast/forced-colors mode. The earlier browser demonstration remains accessible under `17_packages/samples/index.html`.
