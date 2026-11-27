# Taktera UI integration · migration from alpha.1 to alpha.2

## Where to start

1. Open `START-HERE.html`, then `17_packages/samples/index.html` to interact with new stand-alone library (no server required for classic-script demo).
2. Web no-framework consumer: include `17_packages/web-core/taktera-ui.css` and `17_packages/web-core/taktera-ui.js` in the site; set root class `.tku-root` and root `data-product`, `data-theme`; call `window.TakteraUI.button(...)`, etc. For bundler projects, ESM `index.mjs` re-exports the same API.
3. React consumer: see `17_packages/react` — source only, requires `npm install`, `npm run typecheck`, `npm run build`, CI and peer-dependency review. Do not publish before those checks.
4. Avalonia consumer: merge the correct generated product/theme palette dictionary before `TkControls.axaml` and add `TkFieldStyles.axaml` via `Application.Styles`. See `17_packages/avalonia/sample/`. Do not copy the sample directly to production until `dotnet build` and Windows/macOS native QA pass.
5. Continue using the existing 3.2 approved logo/brand assets in `02_logos` and `03_icons`. `14_brand_extensions` remains unapproved and optional.

## Breaking change policy

No modifications were made to existing alpha.1 `13_ui_kit` demonstration or v3.3 source tokens. The new `17_packages` APIs are parallel alpha components, not automatic replacements. Names, rendering, and prop contracts remain provisional before Beta.

## Recommended pre-production gates

- Approve visual state tables and API by product owner.
- Run React typecheck, runtime tests and bundle analysis with registry access.
- Build Avalonia on both target operating systems and test actual focus, keyboard, high contrast and screen readers.
- Build one representative domain module (client records table with permissions and safe data patterns) without copying a base component per product.
- Obtain explicit approval for product icon A/B or retain current canonical icon family.
