# 05. Подключение и внедрение

Taktera · редакция 3.2 · 18 октября 2026

Пакет содержит ресурсы и базовые токены, а не готовую библиотеку всех компонентов. Пример ниже показывает схему подключения. Пути заменяются на пути ресурсов в конкретном приложении.

## Тема и продукт

```html
<html lang="ru" data-theme="light" data-product="fitness">
  <head>
    <link rel="stylesheet" href="/brand/taktera.tokens.css">
  </head>
  <body>
    <a href="/" aria-label="Taktera Fitness — главная">
      <img src="/brand/fitness-light.svg" width="200"
           alt="" style="display:block;max-width:100%;height:auto">
    </a>
    <button class="tk-primary tk-focus">Сохранить запись</button>
  </body>
</html>
```

data-theme и data-product рекомендуется ставить на один корневой элемент. Допустимые продукты: platform, clinic, beauty, spa, fitness, travel. При переключении темы меняются и токены, и файл логотипа light/dark: CSS-токены не перекрашивают содержимое SVG, подключённого через img. Размер и охранное поле логотипа задаёт макет.

## Локальные шрифты

```css
@font-face {
  font-family: Inter;
  src: url("/brand/fonts/Inter-Regular.ttf") format("truetype");
  font-style: normal; font-weight: 400; font-display: swap;
}
@font-face {
  font-family: Inter;
  src: url("/brand/fonts/Inter-SemiBold.ttf") format("truetype");
  font-style: normal; font-weight: 600; font-display: swap;
}
@font-face {
  font-family: Inter;
  src: url("/brand/fonts/Inter-Bold.ttf") format("truetype");
  font-style: normal; font-weight: 700; font-display: swap;
}
body { font-family: Inter, Arial, sans-serif; }
.amount { font-variant-numeric: tabular-nums; }
```

## Контракт токенов

04_tokens/taktera.tokens.json содержит палитру, геометрию и параметры UI. CSS содержит переменные и небольшие вспомогательные классы. .tk-primary задаёт цвета, но не все размеры, состояния и поведение кнопки. .tk-focus задаёт видимый focus-visible. .tk-brand-mark, .tk-brand-dot и .tk-product-name задают цвет соответствующих частей для компонентов, которые поддерживают такое подключение.

В inline SVG используйте stroke="var(--tk-mark)" для основного контура и fill="var(--tk-accent)" для точки. Не применяйте один общий fill или CSS-фильтр ко всему продуктовому логотипу: это уничтожит разделение чёрно-белого знака и цветных элементов. Подпись берётся из готовых контуров.

## Порядок внедрения

- Скопировать ресурсы и сохранить лицензию Inter. Подключить токены и шрифт в одном общем месте.
- Добавить тему и продукт на общий корневой элемент. Проверить логотип и кнопки во всех 12 сочетаниях продукта и темы.
- Заменить логотипы, favicon и app icons. ICO использовать там, где требуется именно этот формат.
- Обновить письма, PDF-документы, Open Graph, установщик и стартовые экраны.
- Проверить формы, таблицы, состояния, фокус, адаптивность и доступные названия.
- Удалять старые ресурсы только после проверки оставшихся ссылок. Выпускать с возможностью возврата предыдущего набора.

07_migration/IMPLEMENTATION-MAP.md содержит предполагаемые точки замены из прежней документации. Эти пути не подтверждены проверкой текущего репозитория. Перед изменением кода разработчик должен сопоставить их с фактической структурой проекта.

## Письма и внешние сервисы

Для почтовых шаблонов используйте PNG с указанным размером и текстовым alt. Для SVG сначала проверьте поддержку целевой среды. Прозрачный белый логотип должен находиться на явно заданной тёмной подложке. Ресурсы для production размещают по доступным адресам; локальные пути из пакета не вставляют в отправляемые письма.
