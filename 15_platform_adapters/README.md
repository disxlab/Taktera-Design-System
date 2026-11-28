# Taktera Platform Adapters · 4.0 alpha.1

## Avalonia UI / Windows + macOS

`generate_avalonia.py` creates twelve independent `ResourceDictionary` (`avalonia/Taktera.<Product>.<Light|Dark>.axaml`) from unchanged v3.3 master JSON. Each contains color and brush keys for canvas/surface/text/muted, borders, accent and its interactive states, disabled controls and four semantic status colors. This is a **token adapter**, not a built or tested Avalonia control library.

```bash
python 15_platform_adapters/generate_avalonia.py
python 15_platform_adapters/generate_avalonia.py --check
```

Example resource usage after an appropriate dictionary is included in the application:

```xml
<TextBlock Foreground="{DynamicResource TkTextBrush}" Text="Taktera" />
<Button Background="{DynamicResource TkAccentBrush}"
        Foreground="{DynamicResource TkOnAccentBrush}" Content="Сохранить" />
```

In real Avalonia apps, decide `ThemeVariant` integration and product switching in the app's actual resource management. **Do not** include all 12 dictionaries in one scope: keys conflict intentionally. Keep separately keyed dictionaries or load the correct theme/product combination. Test dynamic theme changes, OS contrast modes, scale 100–200%, platform font rendering, focus rings and keyboard with installed Avalonia versions. SVG app icon export for macOS ICNS and notarized app packaging are not implemented in this adapter.

## Web

`04_tokens/taktera.tokens.css` is the canonical web-facing generated token layer. `13_ui_kit/ui.css` is a framework-independent alpha style library and `13_ui_kit/ui.js` demonstrates behavior. The alpha has no npm/React adapter or reusable TypeScript component exports. React/Avalonia bindings remain future implementation tasks.
