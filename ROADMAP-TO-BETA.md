# Beta Readiness 3 — реальная сборка и CI

## Подготовлено

- BR3-01: GitHub Actions workflow и руководство — выполнено (артефакт).
- BR3-02: React smoke — код создан, выполнить в CI.
- BR3-03: Avalonia XAML resource preflight — выполнить и устранить замечания, затем настоящая сборка.
- BR3-04: журнал реально выполненных CI и доказательства готовности — заблокировано до GitHub запуска.

## Открытые условия релиза

BETA-01, BETA-02, BETA-03, BETA-04, BETA-05, BETA-06 и DS-032 остаются открытыми; автоматические статические проверки сами по себе не подтверждают React, нативные UI, скринридеры или production readiness.

## Owner decision — 2026-11-28 (supersedes earlier integration gates)
Real Taktera Platform integration is forbidden before Design System 4.0 Stable. No changes to the Platform repository, real ERP endpoints or staging credentials. Pre-Stable acceptance uses independent package-only reference consumers and synthetic data; retain manual/native accessibility, security and performance gates. BR5-07 is standalone acceptance; BETA-04, DS-032 and BR5-06 are deferred until REL-STABLE. Earlier real-staging prerequisites are historical and superseded.

## BR7 — Release Hardening
See Project Board BR7-01–10 and Issue #14. BR7-01 strict exact-archive reproducibility job is implemented; CI pending. Beta → RC → Stable milestones precede real Platform integration.
