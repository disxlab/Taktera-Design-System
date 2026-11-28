# Beta Readiness 3 — сборки и интеграционные ворота

## Состояние

Это **подготовка к запуску реальных CI-сборок**, а не подтверждённый Beta-кандидат. Архив содержит оригинальные исходники React и Avalonia, а также новый межплатформенный CI workflow.

### Запуск в репозитории

1. Создайте отдельный GitHub-репозиторий (без производственных секретов). Распакуйте содержимое так, чтобы `.github/workflows/taktera-beta-readiness.yml` находился в корне.
2. Создайте ветку `beta/readiness-3`, откройте Pull Request в `main`. Actions автоматически выполнит статические, React и Avalonia задания.
3. Приложите ссылки на job, логи и подтверждённые результаты к задачам BETA-01, BETA-02, BETA-06 в Project Board.
4. После успешного первого React build сгенерируйте `package-lock.json` командой `npm install --package-lock-only`, зафиксируйте в Git и замените `npm install` на `npm ci`.
5. Нативную проверку отображения, взаимодействия и скринридеров проведите отдельно. Build не равен UI-приёмке.

### Локальные команды

```bash
python 27_beta_readiness_3/qa/check_sources.py
cd 17_packages/react
npm install
npm run verify
cd ../avalonia/sample
dotnet restore
dotnet build -c Release --no-restore -warnaserror
```

### Проверка пилота

React smoke теперь использует `react-dom/server`, рендерит 6 продуктов × 2 темы и проверяет экранирование пользовательского текста. Реального runtime/browser теста React в этом релизе **нет**. Avalonia Sample предназначен для сборки и последующей ручной проверки на Windows и macOS. Прямое включение в production Taktera.Mail или CRM в этом выпуске не выполнялось.

### Необходимо для Beta

- [ ] Успешный GitHub Actions React: Windows, macOS, Linux
- [ ] Успешный GitHub Actions Avalonia Release: Windows, macOS
- [ ] React browser interactions и доступность в реальном браузере
- [ ] Avalonia нативный smoke, визуальная сверка и UI-проверка
- [ ] NVDA / VoiceOver
- [ ] Сценарий подключения в тестовом приложении и безопасность
- [ ] Регрессионные тесты Firefox/Safari
- [ ] Закреплённый lockfile и политика отката

### Обнаруженная несовместимость и исправление

В источнике обнаружено различие ресурсных ключей: генератор Design Tokens 2.0 выдаёт `Tkn*`, а компоненты `TkControls.axaml` ссылаются на `Tk*`. В `27_beta_readiness_3/generate_avalonia_compat.py` добавлена воспроизводимая генерация 12 адаптеров `Tk*` из канонических словарей. Встроенный пример Clinic Light переведён на генерируемый адаптер; оригинальные `Tkn*` не изменены. Статическая проверка покрывает все используемые компоненты и 12 словарей.

**Не подтверждено:** XAML-компиляция этих адаптеров, состояние визуального фокуса, UI на Mac/Windows.
