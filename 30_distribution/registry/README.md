# Private registry acceptance (BR7-05)

Status: unconfigured; no publication authorized. The policy JSON is a decision record, not a credential file or executable publication configuration.

The candidate packages remain private. Do not remove npm private flags or repack a tested candidate to publish it. A later approved release identity must produce publishable packages at build time, repeat all reproducibility, consumer, SBOM, license and provenance gates, and use the exact signed bytes.

## Local protocol fixture

verify_registry_fixture.py runs a read-only HTTP server bound to 127.0.0.1 on a random port. It uses ephemeral synthetic credentials only. It consumes the same-run candidate and canonical archives after full verification. Checks include anonymous and incorrect credential denial, authenticated SHA-256 equality, rejection of unknown private packages, PUT/DELETE denial, pinned npm CLI pack for both packages and .NET locked-toolchain restore with exact private package mapping and explicit public dependency mappings. The public NuGet dependencies come from nuget.org; this is not an offline test. Only this loopback NuGet fixture allows insecure HTTP. No external private registry writes, no production tokens, no Platform integration. A fixture PASS does not prove real server authorization, TLS, immutability, client installation from that server or registry publication.

## Real provider checklist (owner decision required)

Choose private registry provider and exact HTTPS npm registry URL and NuGet v3 service index. Confirm scope ownership, private visibility, immutable versions, retention, backup/restore and audit logging. Use separate scoped read/publish roles and protected release environment. Keep credentials out of repository and artifacts; npm auth is scoped to exact registry host/path and provided via environment token, NuGet credentials use NuGetPackageSourceCredentials_TakteraPrivate or provider-supported credential helper. Use valid TLS, never disable certificate verification. Configure @taktera scope routing, exact private NuGet ID, explicit public allowlist and no public fallback for private identities. Validate every direct and transitive package source and hash from empty caches. Test anonymous and wrong-token access, read-only write denial, attempted duplicate-version publication with synthetic non-product package in approved sandbox, and authenticated clean SDK consumers on supported OSes. Reject any mismatch or unapproved destination. Never publish real product packages as test probes.

Do not activate publication until owner has approved package license, full attribution, release version, signed provenance, registry policy, release/rollback and manual acceptance. No PR has publish or OIDC rights. Taktera Platform integration remains post-Stable.

References:
- https://docs.npmjs.com/files/npmrc/
- https://learn.microsoft.com/en-us/nuget/consume-packages/package-source-mapping
- https://learn.microsoft.com/en-us/nuget/consume-packages/consuming-packages-authenticated-feeds
- https://learn.microsoft.com/en-us/nuget/consume-packages/nuget-https-everywhere
