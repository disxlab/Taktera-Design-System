# Отраслевые сценарии Taktera · шесть примеров

`data.js` intentionally uses fictional sample data. All examples share one navigation system, type scale, status model, table design, modal and pagination. The distinguishing data are industry-specific and not represented as production requirements.

| Product | Theme accent source | Example modules | Domain-specific future work |
|---|---|---|---|
| Taktera Platform | v3.3 `platform` | operations, approvals, support load | organizations, tenants, RBAC, cross-product health |
| Taktera Clinic | `clinic` | specialist timetable, patients and admissions | clinical consent, protected data, schedule conflicts, audit trails |
| Taktera Beauty | `beauty` | masters, procedures, booking | complex service length, resources, staff scheduling |
| Taktera Spa | `spa` | rooms, rituals, gift certificates | equipment/room conflicts, packages, resource availability |
| Taktera Fitness | `fitness` | coaches, classes, membership | membership rules, class capacity, attendance |
| Taktera Travel | `travel` | tours, managers, consultation requests | reservations, providers, exchange rates, contracts |

The examples intentionally do not provide live pricing, legal/medical advice, accounting, fulfillment or integrations. Changing `data-product` alters brand visuals; source fixtures alter the text and example records. Both themes are supplied for each product.

Recommended review order: first check visual consistency of Clinic/Travel (opposite contrast profiles), then compare all six in light/dark, then component states and responsive 320/390/1440px screenshots. Design acceptance must precede use in any customer-facing product.
