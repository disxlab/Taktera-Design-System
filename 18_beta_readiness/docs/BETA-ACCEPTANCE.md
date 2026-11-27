# Taktera v4.0 — Beta release acceptance matrix (Alpha.3)

This is a gate log, **not an assertion that Beta is ready**. Dates, owners and actual CI/screen-reader reports must be supplied by maintainers.

| Gate | Alpha.3 evidence | Required to close | Status |
| --- | --- | --- | --- |
| Approved brand integrity | 248 SHA-256 frozen originals checked via `validate_static.py` | Confirm brand owner signoff | Automated pass; approval open |
| Web core executable | Chromium 53 base + 29 extended checks | Cross-browser desktop/mobile, accessibility scan, live hosted app | Partial pass |
| Offline npm installability | `verify_install.py`: pack + install + ESM import; public `.d.mts` checked with global TypeScript | Actual app pilot and package change policy | Partial pass |
| Dependency security | No runtime package dependencies in `@taktera/ui-core` | Audit host application dependencies + CSP review | Open |
| React library | TSX source and package metadata preserved | `npm install`, actual `tsc`, React runtime tests, bundler, lockfile | **Blocked here** (registry DNS EAI_AGAIN) |
| Avalonia sample | XML and ResourceDictionary references checked | Native .NET 10 + Avalonia compile/launch on Windows and macOS, keyboard + focus + screenshot | **Blocked here** (.NET SDK unavailable) |
| Accessibility | Native HTML semantics, keyboard navigation, focus restore, forced-colors CSS checks | axe-core and NVDA/VoiceOver, 200/400% zoom, focus order, WCAG 2.2 AA conformance review | Open |
| Internationalization | Russian sample and sample themes available | EN text/RTL policy, long labels, pluralization, locale date and number | Open |
| Performance | Zero-runtime-dependency Web Core JS/CSS | Bundle-size budget, memory and long-table benchmark with real workflows | Open |
| Release governance | Manifest, file hashes, QA outputs, changelog, rollout notes | Code review, security approval, commercial license, owner, signed release, rollback | Open |
| Pilot integration | Offline showcase (fake records only) | One real Web screen + one native Avalonia screen with measurable acceptance | Open |
| Icon proposals A/B | Separate from approved master brand | Real Windows/macOS comparison, design approval and rollback | Open |

## Suggested P0 execution order

1. Run React typecheck, bundler, runtime tests in a repository with access to npm. Fix concrete errors, freeze a lockfile and use `npm ci`.
2. Build and launch the Avalonia sample with .NET 10 on Windows and macOS. Check named ControlTheme, focus and control states.
3. Pilot one data-entry + record-table screen in Web and one in Avalonia. Test with fake fixtures, then controlled staging data.
4. Run axe-core, NVDA, VoiceOver, forced colors and zoom tests; record issue IDs and exact evidence.
5. Obtain design/brand, accessibility and engineering approvals before assigning Beta status.

**Do not publish this alpha package as a stable library or treat it as a legal/compliance certification.**
