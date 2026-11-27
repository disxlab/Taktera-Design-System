# Taktera v3.2 - внедрение
Пакет ресурсов обновлён. Код приложения не менялся.
Пути ниже перенесены из v2.2 и требуют сверки с текущим репозиторием.

| Область | Путь | Действие |
|---|---|---|
| Токены | apps/web/app/globals.css | Подключить 04_tokens, явно задать тему и продукт |
| Знак | apps/web/components/brand/mark.tsx | Один канонический изгиб; цвет только --tk-mark; точка --tk-accent |
| Подпись | apps/web/components/brand/wordmark.tsx, logo.tsx | Master taktera ч/б; продуктовые имена цветные |
| Маркетинг | apps/marketing/components/brand/mark.tsx, og-template.tsx | Те же мастера, новые OG |
| Desktop | apps/desktop/assets/generate-icon.ps1 | Новые app icons; не перекрашивать основной знак |
| Web | apps/web/app/favicon.ico | 03_icons/app/platform-dark.ico |
| Start | apps/web/desktop-start/start.css | Цветовые роли и новый знак |
| Installer | packages/installer/web/src/index.css | Master и токены |
| Email | apps/api/src/core/email/templates/Layout.tsx | 06_templates/email-header.svg; для писем использовать PNG экспорт |
| PDF | apps/pdf-worker | Обновить логотипы в шаблонах |

1. Сначала подключить новые ресурсы рядом со старыми.
2. Задать data-theme и data-product на одном корневом элементе.
3. Проверить все шесть продуктов в двух темах.
4. Проверить focus, hover, selected, disabled, error отдельно; токены не заменяют UI-аудит.
5. Проверить 360/390/768/1215/1280/1920 px, письма, PDF, установщик.
6. Найти старые Nexus assets и legacy HEX. Удалять только после проверки ссылок.
7. Провести отдельную проверку товарных знаков перед регистрацией и коммерческим запуском.
