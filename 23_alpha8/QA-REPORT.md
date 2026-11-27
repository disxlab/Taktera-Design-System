# Alpha.8 · QA Report

- Chromium tests: **33/33 passed**.
- Browser test uses the same HTML, CSS, JS but inlines assets through Playwright `set_content`, since file/HTTP navigation is restricted in this environment.
- Covered eight catalog entries, six products, two themes, English locale, compact mode, A/B compare, keyboard tab behavior, invalid field ARIA, loading state and XSS-safe text rendering.
- Mobile viewport 375 px: no horizontal overflow.
- `node --check` passed for new Studio and existing Project Board JS.
- **Not yet tested:** browser loading of standalone HTML/JS via file:// or HTTP, NVDA, VoiceOver, Firefox, Safari, Avalonia / React builds, visual snapshot baselines.
