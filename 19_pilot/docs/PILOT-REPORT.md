# Alpha.4 offline consumer pilot — evidence

- A **separate consumer project** (`19_pilot/pilot-app`) installed the actual `@taktera/ui-core@4.0.0-alpha.4` tarball with `npm ci --offline` and a lockfile.
- Test execution used Chromium with **locally injected content from the installed package**; the sandbox's browser administrator policy blocks the local HTTP URL. Thus **hosted HTTP/browser module loading was NOT verified**.
- Passed **14/14** integration interactions: EN/RU table, dialog labels, locale switching, theme switching, pagination, keyboard focus restoration, 320 px layout, and JS-error checks.
- Prior Web Core regression: 53/53 + 29/29; static: 274/274.
- React dependency installation/real build, Avalonia native compile, Safari/Firefox, NVDA/VoiceOver, accessibility conformance, hosted application integration and release signoff remain open.

## Running on a developer workstation

1. `cd 19_pilot/pilot-app`
2. `npm ci --offline` (the local npm tarball is included at `../offline/`)
3. `python -m http.server 8765`
4. Open `http://127.0.0.1:8765/` in Chromium, Firefox and Safari as appropriate and inspect console and network requests.

The pilot is synthetic and contains no production customer data.
