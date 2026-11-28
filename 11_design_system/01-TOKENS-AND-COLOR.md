# 01 · Токены, цвета и доступность

## Источник истины и экспорт

`04_tokens/taktera.tokens.json` — редактируемый единый источник значений. Генерируемые файлы:

| Артефакт | Для чего |
|---|---|
| `04_tokens/taktera.tokens.css` | Совместимые с исходным пакетом CSS-переменные и новые UI-роли |
| `04_tokens/taktera.tokens.dtcg.json` | Выгрузка DTCG 2025.10 со структурированными значениями `colorSpace/components/hex` и `dimension` |
| `10_documentation/COLOR-CONTRAST-v3.3.json` | Проверка конкретных непрозрачных пар sRGB на контраст |

DTCG реализована как **экспорт из единого Taktera JSON**; HEX с прямым `$value` не используется. Стандарт: https://www.designtokens.org/TR/2025.10/format/ и https://www.w3.org/community/reports/design-tokens/CG-FINAL-color-20251028/.

## Слои токенов

- **Brand:** `--tk-mark`, `--tk-accent`, `--tk-on-accent` — для логотипов/кнопок; значения цвета продуктовой идентичности **не менялись**.
- **Content:** `--tk-text`, `--tk-muted`, `--tk-accent-text` для светлой поверхности, `--tk-accent-text-canvas` для холста paper.
- **Layout:** `--tk-canvas`, `--tk-surface`, `--tk-border`, `--tk-control-border`; декоративный бордер допускается слабым, но не используется единственной видимой границей поля.
- **Interactive:** `--tk-accent-hover`, `--tk-accent-pressed`, `--tk-focus-ring`, disabled роли.
- **Semantic:** `--tk-status-success-*`, `--tk-status-info-*`, `--tk-status-warning-*`, `--tk-status-error-*`.

## Отдельная роль для цвета текста на холсте

В исходной палитре Spa `#118569` на paper `#F4F3EF` — 4,13:1; Fitness `#D52B35` — 4,48:1. Брендовые цвета остаются неизменными, **для мелкого интерфейсного текста на paper** вводятся:

- Spa: `--tk-accent-text-canvas: #0D755B` (контраст приблизительно 5,09:1).
- Fitness: `--tk-accent-text-canvas: #BE2430` (приблизительно 5,43:1).

Для Travel жёлтый фирменный `#D4A600` остаётся цветом точки/акцента, а UI-текст по-прежнему `#806300`. В остальных продуктах текстовая роль холста наследует согласованный UI-текст.

## Контур элементов управления

| Тема | `--tk-border` (декоративный) | `--tk-control-border` (значимый) |
|---|---|---|
| Светлая | `#D9DCDF` | `#858A93` |
| Тёмная | `#444A52` | `#8D939C` |

Пара `#858A93` на paper даёт приблизительно 3,12:1; `#8D939C` на тёмной поверхности `#22262B` — приблизительно 4,92:1. Не используйте цветной shadow, placeholder или декоративный разделитель как единственный сигнал доступности компонента.
