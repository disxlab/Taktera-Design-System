# Visual Regression — Chromium

Модуль DS-031. Сравнивает 48 сочетаний (6 продуктов × 2 темы × 2 плотности × 2 локали) с изображениями из Beta Readiness 1.

## Запуск

```bash
python 26_visual_regression/visual_regression.py selftest --out /tmp/taktera-visual-qa
python 26_visual_regression/visual_regression.py compare --out /tmp/taktera-visual-qa-compare
```

Зависимости: Python 3, Pillow, NumPy, Playwright Python, установленный Chromium по пути `/usr/bin/chromium`. Окружение специально фиксировано на Chromium/1280×840/DPR1/UTC/reduced-motion. Инструмент формирует HTML+JSON отчёт и выделяет изменившиеся пиксели красным. **Возвращает код 1 при регрессии.**

Порог: 0,5% пикселей при отклонении хотя бы одного RGB-канала более 16. Порог — инженерная настройка, не эквивалент WCAG и не гарантия визуальной идентичности. Изменение шрифтов, ОС, браузера или драйверов может вызвать ложные различия. Для другой платформы требуется собственный baseline, а не сравнение с Chromium. Режим `selftest` вводит заведомо заметную поломку и требует, чтобы она была выявлена.

Не запускайте `capture` поверх эталонов без code review. Нативные Windows/macOS, Firefox/Safari и скринридеры остаются незакрытыми.
