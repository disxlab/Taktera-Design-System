# Offline installation — Taktera Web Core Alpha.3

After extracting the full ZIP, install from a local npm tarball in a test project:

```bash
npm install --offline /path/to/Taktera_Design_System_v4.0-alpha.3/18_beta_readiness/offline/taktera-ui-core-4.0.0-alpha.3.tgz
```

Then use the public ESM API from `@taktera/ui-core` and import its stylesheet via your bundler. The stylesheet contains all six product themes and does not need an online font; local Inter files in the brand package are optional.

```js
import { setTheme, button } from '@taktera/ui-core';
import '@taktera/ui-core/styles.css'; // browser bundler, not plain Node
const root = document.querySelector('#app');
root.classList.add('tku-root');
setTheme(root, { product: 'clinic', theme: 'light' });
root.append(button({ label: 'Новая запись', onClick: () => console.log('open form') }));
```

The package has `private:true` and `license:UNLICENSED` intentionally; no publishing or redistribution permission is implied. It has zero runtime npm dependencies. The React and Avalonia source libraries are **not** included in this npm tarball.

Run from the extracted archive root:

```bash
python 18_beta_readiness/qa/verify_install.py
python 17_packages/qa/test_web.py
python 18_beta_readiness/qa/test_alpha3.py
```

Use `node >=20`, npm, Python 3.12 with Playwright + Chromium, and TypeScript (globally available in the build environment) for these exact checks. External production builds need their own dependency and CI policy.
