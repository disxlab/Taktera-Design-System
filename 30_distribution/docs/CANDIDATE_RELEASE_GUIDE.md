# Taktera Design System — Candidate release guide

**DRAFT / NOT APPROVED FOR DISTRIBUTION.** This guide concerns independent synthetic SDK reference applications, not Taktera Platform integration. A green CI run is not permission to publish, a cryptographic signature, legal clearance, accessibility certification, or a production acceptance result.

## 1. Release identification and integrity

Use a single successful CI run. Download canonical-packages, taktera-candidate-release-evidence, candidate-independent-verification, release-preflight-evidence, rollback-rehearsal-evidence, version-policy-evidence and release-documentation-evidence from that same run. Check the source SHA (PR merge commit if applicable), run ID and attempt and the exact archive digests in the generated release dossier. Do not mix runs. In the candidate directory on Linux, run:

    sha256sum --strict --check SHA256SUMS.txt

This checks listed bytes, not authenticity or the absence of extra files. The CI independent candidate verifier also checks exact file coverage and cross-compares canonical packages and inventories. Until approved signed provenance is available, these unsigned checks provide integrity evidence only. Never accept a changed archive under an already published version.

## 2. Independent local installation

Prerequisites: pinned Node 26.13.1, npm 11.20.0, Python 3.12 and .NET SDK 10.0.404. Use a checkout of the corresponding source (including templates and CLI), verified canonical archive directory and fresh destination outside the repository. From repository root, replacing the example paths with actual paths:

    python 30_distribution/taktera.py init web --packages /path/to/canonical-packages --output /path/to/work/web
    python 30_distribution/taktera.py init react --packages /path/to/canonical-packages --output /path/to/work/react
    python 30_distribution/taktera.py init avalonia --packages /path/to/canonical-packages --output /path/to/work/avalonia

The output parent must already exist; the target must not. In the generated Web or React directory:

    npm install --package-lock-only --ignore-scripts
    npm ci --ignore-scripts

For React, then run npm run build. For either host, npm start starts the local reference app. Keep generated locks. Public dependencies may require internet access; do not describe this as a fully offline restore. For Avalonia, from the generated app directory:

    dotnet restore --configfile NuGet.Config
    dotnet build -c Release --no-restore
    dotnet run --no-restore

Use a compatible desktop environment for graphical tests; retain an exact global.json SDK pin outside the repository as needed. Never put real patient, customer or operational records into fixtures. Generated local source mapping is intended for these reference apps, not an approved production registry configuration. Production must follow registry/README.md with separate scoped credentials and explicit allowlisted dependency sources. No real private registry has been configured.

## 3. Migration and compatibility

Current internal package identities are listed in the generated dossier. Proposed coordinated releases: 4.0.0-beta.1, 4.0.0-rc.1, 4.0.0. These are not published versions or an approved promotion. Under SemVer beta.1 sorts below beta-readiness.3; the proposal is only for first publication, never an upgrade from a published beta-readiness.3. Preserve the original archive and lock before updating; review package exports, declarations, native resources, dependency constraints, host frameworks and accessibility/interaction behavior. Rebuild all gates after any changed package identity or byte. Native XML documentation comparison is not complete CLR ABI verification; additions and breaking changes require explicit review and a reviewed baseline. No automatic source/data migration is implemented. Refer to versioning/README.md.

## 4. License, assets and provenance

Use candidate/licenses/THIRD-PARTY-NOTICES.draft.txt, dependency-license-evidence.json, upstream-license-evidence.json and asset-attribution-review.json plus product CycloneDX/SPDX and consumer SBOMs. Exact texts were collected for tested external dependency scope; legal/asset approval is pending. MicroCom.Runtime source-to-binary commit association is not confirmed. Font family references do not prove that fonts are shipped. Product SBOM and source-marker checks are not full legal or binary asset certification. See security/README.md and RELEASE.md for current technical scope.

Signing template is inactive. Owner must approve trusted main workflow, protected environment, exact source SHA and public attestation metadata before enabling OIDC. Verify signatures independently. No package publication or actual registry use is allowed by this guide. A changed version, private flag or other byte requires a new candidate and all checks again.

## 5. Recovery and release stop conditions

Keep verified immutable approved prior releases and manifests in access-controlled durable storage when a real release exists. Stop on package digest mismatch, absent evidence, unreviewed API/version change, unavailable recovery artifact, unresolved security or attribution issue, or failed manual acceptance. Never overwrite a registry version. Restore prior signed package pins into a clean reference/staging host; verify the archive and installed assembly/files, build and smoke-test, then switch deployment only after owner-approved staged acceptance. Rehearse return to the current snapshot. See recovery/README.md. The local CI rollback rehearsal measures its own duration only; it does not demonstrate production RTO/RPO or native graphical recovery.

## 6. Mandatory approvals

- Confirm package ownership, distribution terms and asset attribution.
- Choose and verify a real private HTTPS registry, access control, retention and immutable version behavior.
- Approve the coordinated release version, signed provenance and trusted workflow.
- Complete independent SDK acceptance and final manual native/browser/accessibility/security/performance QA.
- Confirm staging acceptance, recovery, migration compatibility and release decision.
- Retain no-publish state until the owner authorizes release of the exact verified bytes.

Platform integration remains strictly post-Stable. The generated release dossier records technical evidence, not owner approval.
