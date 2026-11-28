# Decisions not implicit in Alpha.2

**Not approved automatically:** app icon A or B, Signature illustration patterns, full English wordmark, production UI API, a specific Avalonia 12 migration, external design asset licenses.

**Proposed review order:**

1. Compare canonical icons vs proposed A and B in 16/24/32/48/64/256 px on Windows and macOS; select A, B, or retain original. Record owner/date, rollback path.
2. Review new Web UI primary and secondary buttons, error and disabled states across all 12 product/theme combinations.
3. Approve React naming/controlled APIs and Avalonia theme names. Until then, packages remain alpha.
4. Verify what can be reused for the Taktera.Mail app vs industry CRM apps; do not assume the same densities/sidebars are desirable everywhere.
5. Determine default language, supported localization, RTL and privacy/accessibility requirements by target market.

The UI implementation in this package does not require the user to select icons to run the demo.
