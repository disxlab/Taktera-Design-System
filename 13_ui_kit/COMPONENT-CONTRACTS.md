# Taktera UI · Component Contracts / v4.0 alpha.1

**Status:** clickable HTML/CSS/JS prototype, not production component packages. **Source of brand identity:** unchanged Taktera Brand v3.2 masters and v3.3 semantic token compiler. The alpha includes 18 visual/behavioral patterns; this does **not** equal 18 framework-specific published components.

## Architecture

- `index.html` — application shell, pages, forms, demo patterns; labels and base native semantics.
- `ui.css` — Taktera web style primitives and responsive shell. Consumes `--tk-*` semantic and brand variables from `../04_tokens/taktera.tokens.css` without overriding approved accent hex codes.
- `data.js` — six **fictional** industry fixtures, independent of CRM/ERP data.
- `ui.js` — in-memory demo interactions; inputs are escaped before HTML rendering; no network/storage/personal data.
- `window.takteraDemo` — QA-only state reference, **not a public runtime SDK**. Any application integration must provide its own state management, validation, API requests, permissions and domain rules.

## CSS and UX contract

| Primitive/pattern | DOM/CSS contract | State/keyboard behavior | Implementation status |
|---|---|---|---|
| Button | `.tk4-button` `.tk4-button-primary` `.tk4-button-outline` | native button, focus, hover, pressed, disabled | Alpha interactive |
| Icon button | `.tk4-icon-button` + `aria-label` | activation with Enter/Space, tooltip via title when relevant | Alpha |
| Text field | `.tk4-field input` | explicit label, required and error linked to input | Alpha |
| Select | `.tk4-field select` | native select, product/theme controlled through JS | Alpha |
| Checkbox | `.tk4-check input[type=checkbox]` | Space toggle, native checked | Alpha |
| Radio | `.tk4-check input[type=radio]` | Arrow keys, native semantics | Alpha |
| Switch | `input[role=switch]+.tk4-switch` | Space toggle; visible focus on wrapping label | Alpha |
| Tabs | `[role=tablist]`, `[role=tab]` | Left/Right/Home/End, selected state, roving tab index | Alpha (records filters) |
| Navigation | `.tk4-nav-link` + `aria-current=page` | tab order, visible route state, mobile labels | Alpha (single-page demo) |
| KPI card | `.tk4-metric` | title, value, unit/value context, tabular numbers | Alpha |
| Data table | `.tk4-table` in `.tk4-table-scroll` | `scope=col`, click to sort id/contact/date; explicit status labels | Alpha, not virtualized |
| Pagination | `.tk4-pager` | Previous/Next disabled at boundaries, live total text | Alpha |
| Status chip | `.tk4-status-{success/info/warning/error}` | text + marker, product-independent semantic roles | Alpha |
| Toast | `.tk4-toast-stack` | polite live region, explicit manual close; no auto-dismiss | Alpha |
| Alert | `.tk4-alert` | informational text + icon | Alpha |
| Dialog | native `<dialog>` | Escape, modal focus and return handled by UA; labeled heading | Alpha |
| Accordion | native `<details>/<summary>` | keyboard toggling without JavaScript | Alpha |
| Empty & skeleton | `.tk4-empty-table`, `.tk4-skeleton` | informative empty label, loading motion obeys reduced-motion | Alpha |

## Cross-platform naming and semantics

Keep CSS token roles separate from `Color` values: e.g. **accent** is a brand color; **error** is an application semantic status. On a new product, create a new `products` JSON entry, update localized labels and test light/dark contrast before app integration.

Use `aria-invalid=true` and `aria-describedby` for invalid input; do not replace native interactive controls with nonsemantic `div`. Desktop dense tables may use 32px actions when intentionally designed, but touchscreen interactions need larger targets and separate acceptance testing. Currency/date values in UI fixtures are examples only, not business calculations.

## Explicit gaps (not shipped)

- Reusable versioned React/TypeScript component library, npm packaging, Storybook, automated axe-core audit, unit coverage in production frameworks, frozen snapshot approvals.
- Native Avalonia `ControlTheme` templates, compiled C# app, adaptive macOS app icons, screen reader and real-hardware test matrix.
- Actual appointment scheduling collision detection, role permissions, medical/financial records security, backend, offline persistence, analytics, messaging, regulatory validation.
- RTL/languages beyond Russian UI fixtures; professional accessibility certification.

## Expected framework contract for the next implementation

Future product packages SHOULD expose controlled/uncontrolled state explicitly. For example:

```ts
// Design target only — this file does not provide a published TypeScript runtime.
type TkButtonProps = {
  variant?: 'primary' | 'secondary' | 'text';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  disabled?: boolean;
  children: React.ReactNode;
  onClick?: () => void;
};

type TkDataTableProps<T> = {
  rows: readonly T[];
  columns: readonly { key: string; header: string; sortable?: boolean }[];
  rowKey: (row: T) => string;
  sort?: { column: string; direction: 'asc' | 'desc' };
  onSortChange?: (value: { column: string; direction: 'asc' | 'desc' }) => void;
};
```

These are **draft contracts**, not verified exported APIs. Before implementation approve data volume, accessibility behavior and platform target.
