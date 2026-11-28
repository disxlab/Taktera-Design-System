# Alpha.6 — Project Board + Design System Studio

## Launch

Open `dashboard.html` from the `21_alpha6` directory. Use the sidebar link to `studio.html`. Both are standalone HTML/CSS/JS applications requiring no package install, network access, or backend.

## Working with the project board

- Edit a task by clicking it. New tasks use IDs `CUSTOM-001`, etc. Priorities: P0 critical, P1 high, P2 backlog. Statuses: planned, in_progress, blocked, deferred, done.
- Dependencies are comma-separated existing task IDs; unknown or self-dependencies are rejected. **Cycles among multiple tasks are not yet detected**.
- Default Board counts 31 tasks and six phases. Nine tasks are marked done, five Beta prerequisites are blocked, one icon decision deferred. Check the live board for current state.
- Local browser storage stores changes automatically on the *same* browser/profile/origin. In some browsers, file:// localStorage is limited or partitioned; always export JSON manually. No cross-device synchronization; no server account.
- Export JSON creates a full board/history backup. Import JSON **replaces** the current board after confirmation. CSV is a task export, not full backup. Use the same JSON to continue work on another PC.
- "Reset" deletes local changes after confirmation. No network sync, permissions, audit-grade signatures or shared multi-user editing. Imported JSON should be from a trusted source.
- Initial task status evidence: `ROADMAP-TO-BETA.md` of Alpha.5 and earlier release descriptions. Dates in future were intentionally not invented.

## Design System Studio

- Choose Platform, Clinic, Beauty, Spa, Fitness, Travel; light/dark; comfortable/compact; RU/EN labels.
- Shows raw computed colors from canonical CSS v3.3 and additive Alpha.6 tokens; swatches show actual resolved values.
- Explicit contrast checks use WCAG relative luminance for two known text/background pairs. These **do not** constitute a complete accessibility review.
- Experimental color override only affects demonstration and can be saved as CSS; brand palette is not changed or approved by this operation.
- UI controls are examples, not the real reusable React/Avalonia component implementations.

## QA and limitations

- `qa/browser-tests.json`: 31/31 isolated Chromium checks (mocked page markup and scripts), no JavaScript page errors. Covers task edits, filters, export, import, state changes, initial milestones, 12 theme/product combinations, density, RU/EN and mobile overflow.
- Browser policy here blocked navigation to file:// and localhost: use of `set_content`/`add_script_tag` isolates the DOM/JS behavior but **does not verify full navigation or file-origin persistence**.
- No NVDA or VoiceOver audits, cross-browser QA, React build, Avalonia native build, user-research signoff or multi-user server synchronization performed.
- Approved branding and original package inputs retained.

## Next roadmap

Alpha.6 remaining: rich locale formatters, canonical token generator for React/Avalonia, typography and density specs. Alpha.7: advanced tables/calendar/forms/KPI. Alpha.8: fully documented component Studio. Alpha.9: signature graphics, icon governance, corporate templates. Beta requires React/Avalonia native builds, assistive technology tests and staging integration.
