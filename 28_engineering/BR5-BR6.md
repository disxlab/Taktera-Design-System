# BR5 / BR6 execution plan — planned, not implemented
BR5 Product Integration: issue #12. BR6 Distribution & Developer Experience: issue #13. See roadmap IDs BR5-01–06 and BR6-01–06.
## BR5 exit criteria
A real Taktera Platform staging host and agreed contracts; synthetic fixtures only; DataGrid, Resource Scheduler, CRM, form, shell, KPI integration; six product variants and light/dark themes, RU/EN; measured performance, security and accessibility results; native browser evidence. Set budgets with owner before claiming performance success.
## BR6 exit criteria
Versioned public API and migration policy; offline/clean npm consumer installs packed Web Core and React tarballs, verifies types/exports/styles; NuGet clean consumer references packaged compiled Avalonia resources, Windows/macOS build; license and third-party notices, SBOM, checksums/provenance; private distribution decision; rollback drill and owner approval. No publishing, public registry or tag until approved.
## Dependency policy
BR5 host contract can be prepared while BR4 manual QA is open, but cannot claim a completed product integration. BR6 packaging may be prepared in parallel; release remains blocked on all Beta gates. Keep canonical brand assets untouched.

BR5 initial implementation: see `29_product_integration/ARCHITECTURE.md`. Contract proposed, real host/staging remains unconfirmed.

## Release sequence and integration
- Beta: BR5 acceptance in a real staging host with synthetic data, BR6 clean package-consumer verification and required Beta gates. No registry publication or release tag without approval.
- RC: frozen public interfaces, manual accessibility/native QA, security/performance acceptance, license/SBOM and rollback rehearsal.
- Stable: accepted pilot, final documented versions, approved migration/rollback and owner sign-off.
- React local pilot recipe: see 17_packages/react/README.md; use a tarball from a pinned, verified commit. React package remains private. Avalonia sample compilation is not a NuGet library; BR6 must build and verify a reusable package before consumption. Web Core and React remain separate delivery targets.
- External dependencies: authorized host repository/staging endpoint, synthetic tenant/fixtures, API contracts, performance budgets and manual Windows/macOS/Safari/screen-reader reviewers. No confirmed date or release approval.

## Independent consumer gate (BR6-02)
Run #23 https://github.com/disxlab/Taktera-Design-System/actions/runs/46081513783: 11/14, browser test selector ambiguity, corrected exact names. New CI job packs both private npm packages, installs into a temporary independent project with locked direct tool/peer versions, compiles strict NodeNext TypeScript against public declarations, SSR and Chromium hydration/interactions. Artifacts include tarballs, SHA-256 and consumer lock/report if successful. This is not a registry publish, production staging, license approval or reproducibility proof; the generated consumer lock is evidence, not a committed lock yet. NuGet packaging and other release gates remain open.

## BR6 native package gate
Run #24 15/15 PASS, CRM/analytics 434/434 per engine; 1302/1302 total, npm clean consumer 16/16. https://github.com/disxlab/Taktera-Design-System/actions/runs/46082895789
Taktera.UI.Avalonia candidate: compiled resource dictionaries and control themes, typed URI SDK; independent PackageReference consumer and headless checks on Windows/macOS. No registry publication. No native ERP component parity or manual native certification. See 30_distribution/SDK.md. New CI pending.

## BR6 release engineering and SDK tools
Run #25 https://github.com/disxlab/Taktera-Design-System/actions/runs/46083389234: 15/17; npm consumer 16/16. Windows native consumer 22/22 plus 4/4 headless tests, cleanup failed due locked Avalonia build task DLL. macOS pack and independent app compiled, 21/21 checks, test CS0234. Fix explicit test package ref, canonical temp directory, shutdown/no reuse and cleanup retry. Added API candidate baseline, CLI starter integration, searchable developer portal, aggregate candidate release evidence after all required jobs. Revalidation pending. SBOM scope is actual consumer dependency inventory; license review, signed provenance, reproducibility, registry approval and staging remain open.

Run #26 final: 16/18 jobs success, 1 Windows cleanup failure, 1 candidate evidence skipped as required. All three browser jobs PASS; CRM/Analytics 434/434 per engine and 48 CRM axe scans per engine, zero detected violations. New CI required.
