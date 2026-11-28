# Accessibility scope · UI alpha

## Verified automatically in a rendered Chromium document

- 12 combinations (six products × two themes) update the root theme, product and brand logo label.
- Navigation to journal and component explorer, filter, tabs, pagination, dialog open/invalid/submit, toast display, Escape close.
- No JS console or page errors in the captured run.
- No document-level horizontal overflow at 1440, 390 and 320 px. Data tables deliberately scroll **inside** their containers on narrow screens.
- Mobile navigation buttons retain `aria-label` when visible text is hidden.
- v3.3 token compiler separately checks 76 solid foreground/background or border pairs against WCAG contrast thresholds.

## Not yet verified / release blockers

- Complete WCAG 2.2 conformance, screen reader testing (NVDA/VoiceOver/TalkBack), 200–400% zoom, high-contrast OS themes, cognitive accessibility and localized announcements.
- Focus progression across repeated modal opens, form error announcements under assistive technology, and status notifications in actual screen readers.
- Contrast of every rendered state, focus ring and overlay in every component (token checks are not a rendered-screen accessibility audit).
- Real application performance, virtualized data tables, chart alternatives and power-user keyboard workflows.

## Component principles

1. Brand color may not be the only indication of status. Error, success, warning and info have explicit labels.
2. Native `button`, `input`, `select`, `table`, `dialog`, `details` used wherever possible.
3. Text must not be placed on decorative patterns without actual background contrast validation.
4. Essential UI controls use `--tk-control-border`, not decorative `--tk-border`.
5. Respect `prefers-reduced-motion`; animations must remain optional and nonessential.

**Verdict:** alpha meets the listed mechanical checks; no formal accessibility certification is claimed.
