# Taktera v4.0 alpha.1 — QA / known limitations

**Tested:** 22 November 2026. The preview has been run in a Chromium DOM with **all local HTML, CSS, JS and the three Inter WOFF2 fonts injected into `about:blank`** because direct file and URL navigations in the evaluation container return `ERR_BLOCKED_BY_ADMINISTRATOR`. This runs the same UI code but does not establish that `file://` navigation or packaging behaves on every user machine.

## Passed

- `browser-qa.json` stores 42 Chromium assertions: 12 product/theme combinations, 12 desktop width checks, navigation/filter/tabs/pagination/create/modal/toast, 320 and 390 px width, accessible mobile nav names and JS errors.
- Screenshots of six products × two themes, mobile and component library are in `16_quality/screenshots`.
- `python 09_source/generate_tokens.py --check` validates unchanged CSS/DTCG/contrast artifacts from v3.3.
- `python 15_platform_adapters/generate_avalonia.py --check` verifies 12 generated Avalonia dictionaries parse as XML and match the canonical JSON input.
- New icon concepts are staged **separately** and original v3.3 masters are byte-for-byte retained.
- `python 16_quality/build_release.py` additionally checks links/assets/manifest/compressed archive.

## Important limitations

1. v4.0 **alpha.1** is an offline interactive reference, not a React/npm/Avalonia production UI-kit.
2. Avalonia dictionaries compile colors/brush keys only; the set of controls, resource selection, and real Windows/macOS integration are not implemented.
3. New A/B icons and background patterns are design **candidates** requiring formal approval; original brand assets remain canonical.
4. Browser validation is not a substitute for a normal `file://` or hosted smoke run on the developer's machine, and does not establish WCAG 2.2 conformance. Formal screen-reader, keyboard edge cases, touch, zoom and contrast-state testing remains.
5. All business/medical/travel data are fictional. No authentication, backend, data protection, legal review, scheduling constraints, financial computations or production APIs are included.
6. Original 14-page v3.2 PDF and v3.3 engineering guide are retained **unchanged**; there is no newly typeset official v4.0 brandbook.

## Suggested promotion criteria for v4.0 beta

- Owner approval of icon and marketing proposals, formal visual QA for six verticals across both themes; eliminate major WCAG/UX issues.
- Implement shared React or Avalonia control library with stable documented component API, behavior tests, snapshots and integration examples.
- Actual screen-reader runs Windows + macOS, keyboard audits, input masking/validation and responsive review.
- Verify versioned token outputs against production apps (not just offline demo), bundle/file-size budgets, performance telemetry and real-data-safe security review.
