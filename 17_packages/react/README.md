# @taktera/ui-react · v4.0.0-alpha.2 (SOURCE ONLY)

React/TypeScript components provided: TakteraProvider, Button, Field, Select, Checkbox, Switch, Status, Alert, Card, Tabs, Dialog, DataTable, Pagination and ToastRegion. `DataTable` escapes string values by native React rendering; column `format` is application-supplied ReactNode and must not render untrusted HTML. Tab state supports controlled and uncontrolled modes; table sorting supports both. No application/domain services included.

**Unverified in this environment**: npm dependency installation, React typings/build, runtime React tests and npm publication (registry unavailable). `package.json` is intentionally `private: true`; remove that only after `npm ci`, `npm run typecheck`, `npm run build`, React tests and review. There is no fake compiled distribution or npm lockfile.

From this folder on developer machine with registry access:

```bash
npm install
npm run typecheck
npm run build
```

In the app:

```tsx
import { TakteraProvider, Button, Field } from '@taktera/ui-react';
import '@taktera/ui-react/styles.css';

<TakteraProvider product="clinic" theme="light">
  <Field label="Название услуги" required />
  <Button onClick={() => alert('Демо')}>Добавить</Button>
</TakteraProvider>
```

Components currently lack production-reviewed prop APIs, React runtime tests, safe input validation for domain data and screen-reader verification. Release gate is pending.
