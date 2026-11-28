# Manual native / accessibility QA — evidence template
Status: NOT RUN. Headless and build are prerequisites, not native QA.
For each of Windows/macOS: record OS version, architecture, .NET SDK, commit SHA, date, tester. Run sample from repository: dotnet run --project 17_packages/avalonia/sample/TakteraUiAvalonia.Sample.csproj -c Release.
- Confirm visible launch, resources, text and DPI at 100/150/200% where supported; keyboard Tab/Shift+Tab, Space, Enter, visible focus, field input, combo and check state; capture screenshots and note defects.
- Windows: NVDA; macOS: VoiceOver. Check names, roles, states, order, modal focus and keyboard navigation. Browser native Safari on macOS: repeat HTTP sample and React hydration, keyboard and screenshots; WebKit Linux is not native Safari.
- Record PASS/FAIL/NOT RUN for each scenario; attach evidence to issues #3, #4, #6. Do not mark as done without evidence. Never use real patient data.
