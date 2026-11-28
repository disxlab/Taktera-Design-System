# Accessibility & UX Gate · Alpha.2

**Scope:** partial automated QA, NOT WCAG 2.2 certification and NOT NVDA/VoiceOver validation.

| Component / scenario | Automated | Still required before Beta |
| --- | --- | --- |
| Input label & error | Chromium accessible-name and `aria-describedby` check | NVDA/VoiceOver announcements, error recovery, localization |
| Tabs | ArrowRight/Home/End, selected/focus, native button | ArrowLeft, wrap, zoom 400%, screen readers |
| Dialog | HTML `<dialog>`, Escape, initial focus, return focus, confirmation | screen reader, nested dialog, asynchronous validation |
| Table | sorting `aria-sort`, pagination, text-only untrusted values | large dataset, row selection, screen reader table navigation |
| Switch, disabled, loading | role checked; disabled; `aria-busy` | native screen readers and high-contrast systems |
| Themes | 6 products × 2 themes exact canonical `accent` CSS value | exhaustive button hover/focus/error contrast, PDF contrast |
| Responsive | viewport overflow 320 / 390 / 768 / 1440 | touch, actual Windows/macOS OS zoom and mobile browsers |
| Motion | `prefers-reduced-motion: reduce` in QA | full sensory/motion audit |
| Focus order | first dialog focus, focus restoration | all keyboard combinations, touch and assistive tech |
| Accessibility color | inherited verified semantic tokens v3.3 | full WCAG contrast + non-text boundary audit on every state |

**Security boundary:** data table renders raw strings as text nodes; it never parses provided HTML. This is not a security review of future business applications and does not validate input fields against domain constraints. No actual patients/customers are present.

Reference: W3C WAI modal dialog guidance (https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/); WCAG 2.2 (https://www.w3.org/TR/WCAG22/).

## Alpha.3 added checks

- Automatic verification of alert severity (`role=alert` for errors) and ordinary status messages.
- Named pagination navigation and live-announced page range.
- Full ArrowLeft/ArrowRight wrap-around for tabs and focus restoration after Escape.
- Validation/recovery of dynamic field errors; rejection of invalid API parameters.
- `@media(forced-colors: active)` CSS and Chromium emulated high-contrast mode.
- Two independent product/theme scopes on one page; mobile width 320 px.
- All 29 results at `18_beta_readiness/qa/browser-extended.json`.

**No axe-core scan, NVDA, VoiceOver, automated WCAG conformance claim or real screen-reader evidence is included.**
