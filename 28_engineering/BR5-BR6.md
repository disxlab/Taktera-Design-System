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
