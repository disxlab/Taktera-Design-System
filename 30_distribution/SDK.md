# Taktera Developer SDK — 4.0 pre-release
## What is supported
| Target | Package | Public entry |
|---|---|---|
| React 18.3–19 (19 tested) | @taktera/ui-react | package root, styles.css |
| Browser DOM | @taktera/ui-core | package root, styles.css, script.js |
| .NET 10 / Avalonia 11.3.22 | Taktera.UI.Avalonia | TakteraResources, avares assets |

Run #24 15/15 PASS, CRM/analytics 434/434 per engine; 1302/1302 total, npm clean consumer 16/16. https://github.com/disxlab/Taktera-Design-System/actions/runs/46082895789
Native package is a candidate, not yet validated at this commit. React/Web Core remain private; versions are not immutable release versions yet. No public publishing.

## Quickstart
React: build with npm ci and npm run verify in 17_packages/react, npm pack, install the actual tarball into your application; import TakteraProvider and @taktera/ui-react/styles.css. Set product (platform, clinic, beauty, spa, fitness, travel) and theme (light, dark). The independent example is reference-react/App.tsx.
Web Core: pack 17_packages/web-core, install tarball, import setTheme/button from @taktera/ui-core and styles.css. For plain HTML use the documented script entry.
Avalonia: run python 30_distribution/qa/verify_nuget_consumer.py from root with .NET 10; output nupkg in qa/results/nuget. Copy the package to an authorized local feed, pin exact version with PackageReference and configure NuGet source mapping. Add FluentTheme and resource/style includes as in reference-dotnet/app/App.axaml. The typed SDK returns palette and style URIs. Existing native scope is resource themes and basic controls, not React feature parity.

## Host contract
DataGrid reads and bulk operations: inject GridTransport scoped to authenticated tenant, with versions and idempotency. Scheduler: host checks all resources, permissions and time conflicts atomically; uncertain mutation requires reconciliation. CRM: host handles authorized data, versioned saves and draft lifecycle; no personal data in browser storage. Analytics: complete daily rows in a single currency; host defines metrics, permissions and period completeness. Reference apps contain synthetic data only.

## Versioning proposal
Before Stable, API changes are documented in release notes and verified by consumer tests. After approval of API baseline, SemVer patch for compatible fixes, minor for additive features, major for breaking public API/token/resource changes. No silent modifications of approved brand assets. Pin exact versions in application lockfiles; retain checksums and immutable artifacts. A candidate built twice under the same version is not a stable published release.

## Upgrade / rollback
Test the candidate in a separate branch and isolated staging tenant; preserve lockfiles and prior verified packages. Run clean consumers, native/browser/manual accessibility, security and agreed performance tests. Approve deployment only after evidence. If regression: revert consumer dependency and lockfile to previous verified version, rebuild, redeploy, reconcile outstanding mutations with server; database migrations and rollback are host-owned. No automated production release yet.

## Remaining release gates
Actual staging, native Safari, Windows/macOS manual QA, NVDA/VoiceOver, performance budgets, third-party notices/license/SBOM/provenance, repeatability, registry access policy and owner sign-off. The SDK does not imply that all these gates have passed.

## Developer tools
- Portal: 30_distribution/portal/index.html (open locally or serve repository root over loopback HTTP).
- CLI: python 30_distribution/taktera.py init react|web|avalonia --packages PATH --output NEW_DIRECTORY; see CLI.md. Generates local-vendor starter without overwriting existing directories. No registry write.
- Release evidence: RELEASE.md; CI creates checksummed candidate bundle only when every required job passes; no publishing.
- Run #25 https://github.com/disxlab/Taktera-Design-System/actions/runs/46083389234: npm passed, both NuGet jobs require revalidation. Windows cleanup and macOS package test reference corrected in this change; not yet verified.
