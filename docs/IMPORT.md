# Import Beta Readiness 3

Source-of-truth snapshot: `Taktera_Design_System_v4.0-beta-readiness.3.zip` (869 archive entries; archive must be extracted before importing).

The source bundle is **not yet fully in this repository**. CI is expected to fail until it is imported. No production credentials are needed.

## Recommended process

1. Download the exact Beta Readiness 3 ZIP from the ChatGPT project deliverable.
2. Extract it. Enter the extracted `Taktera_Design_System_v4.0-beta-readiness.3/` directory (the one containing `17_packages/`, `21_alpha6/`, `27_beta_readiness_3/`, and `.github/`).
3. Clone `https://github.com/disxlab/Taktera-Design-System.git`.
4. Check out `bootstrap/beta-readiness-3`.
5. Copy **contents** of the extracted directory into the checkout without deleting `.git/`. Do not include `__pycache__`, node_modules, build outputs, or secrets.
6. Review file sizes and generated artifacts. Commit as `feat: import Beta Readiness 3 sources`, then push the branch.
7. Inspect the Draft PR and its GitHub Actions runs. Do not merge until the required CI and UI acceptance gates pass.

## Minimum layout after import

- `17_packages/react/package.json`
- `17_packages/avalonia/sample/TakteraUiAvalonia.Sample.csproj`
- `27_beta_readiness_3/qa/check_sources.py`
- `21_alpha6/data/roadmap.json`
- `.github/workflows/taktera-beta-readiness.yml`

## Unfinished gates

React npm install/typecheck/build/SSR, Avalonia native build on Windows/macOS, browser and accessibility QA, staging integration, and release policy. CI results are evidence only after actual execution.
