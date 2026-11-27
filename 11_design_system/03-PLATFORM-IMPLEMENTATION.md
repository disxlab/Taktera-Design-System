# 03 · Интеграция и технические границы

## Браузерные приложения

Добавьте CSS из `04_tokens/taktera.tokens.css` и собственную библиотеку компонентов или начните с `11_design_system/taktera.components.css` **только как прототипа**. Установите `data-product` и `data-theme` на **одном** корневом элементе — это предотвращает неоднозначное наследование при вложенных темах. Для каждого theme/product обновляйте путь к SVG через соответствующий готовый ресурс: CSS не перекрашивает SVG внутри `<img>`.

```html
<html lang="ru" data-theme="light" data-product="clinic">
<link rel="stylesheet" href="/brand/04_tokens/taktera.tokens.css">
<img src="/brand/02_logos/products/ru/svg/clinic-ru-light.svg" alt="Taktera Клиника">
<button type="button" class="tk-primary tk-focus">Сохранить</button>
</html>
```

Этот фрагмент демонстрирует палитру, но классы `.tk-primary/.tk-focus` сами по себе не создают компонент и его поведение. В демо подключена дополнительная библиотека стилей.

## Desktop и Avalonia

CSS-токены браузера **нельзя считать готовыми ресурсами Avalonia**. Для приложений на Avalonia следует построить генератор `ResourceDictionary`/`DynamicResource` из DTCG или исходного JSON. Для каждой комбинации 6 продуктов × 2 темы сформируйте независимые словари, выделите семантические роли, проверяйте DPI, масштабирование, клавиатуру, OS high-contrast и реальные системные иконки.

Нельзя автоматически переносить `color-mix` в XAML: в DTCG сохранены **численные** RGB-значения hover/pressed. Для Windows ICO уже есть 7 слоёв; macOS app bundles и ICNS требуют отдельного проверенного экспорта.

## Источник / релиз

```bash
python 09_source/generate_tokens.py           # Создать CSS, DTCG, contrast
python 09_source/generate_tokens.py --check   # Проверить актуальность
python 09_source/release.py                   # Проверить пакет и создать ZIP
python 09_source/rebuild_assets.py --output ../_test_assets # Не трогает source
```

`rebuild_assets.py` требует Pillow + CairoSVG. `release.py` дополнительно требует Pillow, fontTools и pypdf. Для генерации WOFF2 необходим fontTools + brotli. Старые скрипты из v3.2 сохранены в `09_source/legacy_v3.2`: они были жёстко привязаны к оригинальному компьютеру, не использовать их для новой сборки.

## Границы воспроизводимости

Новый SVG->PNG/ICO реэкспорт независим от машины автора, но не выполняет оригинальную оптическую реконструкцию выбранного растрового знака из `08_reference` (это отдельный дизайнерский процесс). Готовые SVG в `02_logos` — фактические канонические векторы. 14-страничный брендбук v3.2 остаётся исходной публикацией; отдельное дополнение v3.3 описывает изменения. Изменение исходных SVG потребует согласования, ререндеринга и визуального диффа.
