# @taktera/ui-react — pre-release integration

Source package, currently private. CI has verified React compilation/SSR and browser suites for prior commits; consult the exact commit's Actions result. Do not treat this as a published stable registry package.

## Local consumer pilot
From repository root, on Node 26 (current CI baseline):
```sh
cd 17_packages/react
npm ci
npm run verify
npm pack
```
Install the generated tarball in a separate React application with React/React DOM 18.3–19 (React 19 is the tested dev baseline).
```sh
npm install /absolute/path/to/taktera-ui-react-4.0.0-beta-readiness.3.tgz
```
```tsx
import { TakteraProvider, Button } from '@taktera/ui-react';
import '@taktera/ui-react/styles.css';

export function App() {
 return <TakteraProvider product="clinic" theme="light"><Button>Demo</Button></TakteraProvider>;
}
```
Local packing is a pilot recipe, not completed clean-consumer acceptance. BR6 must validate package contents, exports, dependency/React peer compatibility, license/SBOM, reproducible builds, registry authorization and rollback. Do not publish or remove private flag until approved. DataGrid, Scheduler, CRM and analytics consume authorized host data/callbacks; the host owns domain rules, tenant/RBAC, concurrency, privacy and storage. See 29_product_integration/ARCHITECTURE.md in the repository.
