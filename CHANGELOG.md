# Beta Readiness 3 — 2026-11-23

- Добавлен GitHub Actions `.github/workflows/taktera-beta-readiness.yml` с матрицами React (Linux/Windows/macOS) и Avalonia (Windows/macOS).
- Для React добавлен SSR smoke-тест 6×2, проверка безопасного экранирования таблицы, test scripts и отдельная проверка TypeScript QA.
- Добавлена локальная статическая проверка XAML-словарей, ссылок на ресурсы и исходников. Обнаружено несовпадение ключей `Tkn*` / `Tk*`; подготовлены 12 совместимых словарей, демонстрация Clinic Light переведена на такой словарь.
- Обновлена Project Board: BR3-01—BR3-04. BETA-01/02/06 остаются открытыми до реальных CI-сборок.
- Все утверждённые фирменные ресурсы унаследованы без изменения.

**Ограничения:** npm registry не доступен (EAI_AGAIN), .NET SDK отсутствует; workflow не был запущен в GitHub. Этот пакет не является Beta-релизом.
