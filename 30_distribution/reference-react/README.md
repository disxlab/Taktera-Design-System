# Taktera reference consumer (pre-release)
This is an independent synthetic ERP/CRM example, not the real platform. It imports only @taktera/ui-react and @taktera/ui-core public exports. No credentials, production data, persistent storage or server booking writes.

From repository root on the CI-compatible Linux/Node baseline:

    cd 17_packages/react
    npm ci
    npm run verify
    npx playwright install --with-deps chromium
    cd ../..
    node 30_distribution/qa/verify_npm_consumer.mjs

The verifier builds a temporary independent consumer from both npm tarballs, compiles TypeScript, checks SSR and browser interactions, then writes evidence in 30_distribution/qa/results/npm and deletes the temporary directory. The reference source can also be copied to a separate app with the packed packages installed. Real staging, stable distribution and license approval are still required.
