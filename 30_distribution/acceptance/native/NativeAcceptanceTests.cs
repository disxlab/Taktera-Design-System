using Avalonia;
using Avalonia.Controls;
using Avalonia.Headless;
using Avalonia.Headless.XUnit;
using Avalonia.Interactivity;
using Avalonia.Markup.Xaml.Styling;
using Avalonia.Media;
using Avalonia.VisualTree;
using Taktera.Reference;
using Taktera.UI.Avalonia;
using Xunit;

namespace Taktera.HeadlessTests;

// Synthetic host-owned localization; this is not SDK translation certification.
public class NativeAcceptanceTests
{
    [AvaloniaFact]
    public void Platform_Light_ru() => Exercise(TakteraProduct.Platform, TakteraTheme.Light, "ru");

    [AvaloniaFact]
    public void Platform_Light_en() => Exercise(TakteraProduct.Platform, TakteraTheme.Light, "en");

    [AvaloniaFact]
    public void Platform_Dark_ru() => Exercise(TakteraProduct.Platform, TakteraTheme.Dark, "ru");

    [AvaloniaFact]
    public void Platform_Dark_en() => Exercise(TakteraProduct.Platform, TakteraTheme.Dark, "en");

    [AvaloniaFact]
    public void Clinic_Light_ru() => Exercise(TakteraProduct.Clinic, TakteraTheme.Light, "ru");

    [AvaloniaFact]
    public void Clinic_Light_en() => Exercise(TakteraProduct.Clinic, TakteraTheme.Light, "en");

    [AvaloniaFact]
    public void Clinic_Dark_ru() => Exercise(TakteraProduct.Clinic, TakteraTheme.Dark, "ru");

    [AvaloniaFact]
    public void Clinic_Dark_en() => Exercise(TakteraProduct.Clinic, TakteraTheme.Dark, "en");

    [AvaloniaFact]
    public void Beauty_Light_ru() => Exercise(TakteraProduct.Beauty, TakteraTheme.Light, "ru");

    [AvaloniaFact]
    public void Beauty_Light_en() => Exercise(TakteraProduct.Beauty, TakteraTheme.Light, "en");

    [AvaloniaFact]
    public void Beauty_Dark_ru() => Exercise(TakteraProduct.Beauty, TakteraTheme.Dark, "ru");

    [AvaloniaFact]
    public void Beauty_Dark_en() => Exercise(TakteraProduct.Beauty, TakteraTheme.Dark, "en");

    [AvaloniaFact]
    public void Spa_Light_ru() => Exercise(TakteraProduct.Spa, TakteraTheme.Light, "ru");

    [AvaloniaFact]
    public void Spa_Light_en() => Exercise(TakteraProduct.Spa, TakteraTheme.Light, "en");

    [AvaloniaFact]
    public void Spa_Dark_ru() => Exercise(TakteraProduct.Spa, TakteraTheme.Dark, "ru");

    [AvaloniaFact]
    public void Spa_Dark_en() => Exercise(TakteraProduct.Spa, TakteraTheme.Dark, "en");

    [AvaloniaFact]
    public void Fitness_Light_ru() => Exercise(TakteraProduct.Fitness, TakteraTheme.Light, "ru");

    [AvaloniaFact]
    public void Fitness_Light_en() => Exercise(TakteraProduct.Fitness, TakteraTheme.Light, "en");

    [AvaloniaFact]
    public void Fitness_Dark_ru() => Exercise(TakteraProduct.Fitness, TakteraTheme.Dark, "ru");

    [AvaloniaFact]
    public void Fitness_Dark_en() => Exercise(TakteraProduct.Fitness, TakteraTheme.Dark, "en");

    [AvaloniaFact]
    public void Travel_Light_ru() => Exercise(TakteraProduct.Travel, TakteraTheme.Light, "ru");

    [AvaloniaFact]
    public void Travel_Light_en() => Exercise(TakteraProduct.Travel, TakteraTheme.Light, "en");

    [AvaloniaFact]
    public void Travel_Dark_ru() => Exercise(TakteraProduct.Travel, TakteraTheme.Dark, "ru");

    [AvaloniaFact]
    public void Travel_Dark_en() => Exercise(TakteraProduct.Travel, TakteraTheme.Dark, "en");

    private static Color BrushColor(IBrush? brush) => Assert.IsAssignableFrom<ISolidColorBrush>(brush).Color;
    private static Color PaletteColor(ResourceInclude palette, string key)
    {
        Assert.True(palette.TryGetResource(key, null, out var value), key);
        return Assert.IsAssignableFrom<ISolidColorBrush>(value).Color;
    }
    private static void Exercise(TakteraProduct product, TakteraTheme theme, string locale)
    {
        var uri = TakteraResources.Palette(product, theme);
        var palette = new ResourceInclude(uri) { Source = uri };
        var window = new MainWindow();
        window.Resources.MergedDictionaries.Add(palette);
        window.RequestedThemeVariant = theme == TakteraTheme.Dark ? Avalonia.Styling.ThemeVariant.Dark : Avalonia.Styling.ThemeVariant.Light;
        try
        {
            window.Show();
            var field = Assert.Single(window.GetVisualDescendants().OfType<TextBox>());
            var combo = Assert.Single(window.GetVisualDescendants().OfType<ComboBox>());
            var checkbox = Assert.Single(window.GetVisualDescendants().OfType<CheckBox>());
            var buttons = window.GetVisualDescendants().OfType<Button>().ToArray();
            var primary = Assert.Single(buttons, b => Equals(b.Content, "Сохранить"));
            var secondary = Assert.Single(buttons, b => Equals(b.Content, "Отмена"));
            Assert.Equal(PaletteColor(palette, "TkCanvasBrush"), BrushColor(window.Background));
            Assert.Equal(PaletteColor(palette, "TkAccentBrush"), BrushColor(primary.Background));
            Assert.Equal(PaletteColor(palette, "TkOnAccentBrush"), BrushColor(primary.Foreground));
            Assert.Equal(PaletteColor(palette, "TkSurfaceBrush"), BrushColor(field.Background));
            Assert.Equal(PaletteColor(palette, "TkTextBrush"), BrushColor(field.Foreground));
            Assert.True(primary.Bounds.Width > 0 && field.Bounds.Height > 0);
            primary.Content = locale == "ru" ? "Сохранить" : "Save";
            secondary.Content = locale == "ru" ? "Отмена" : "Cancel";
            field.Watermark = locale == "ru" ? "Название услуги" : "Service name";
            checkbox.Content = locale == "ru" ? "Подтверждено" : "Confirmed";
            var text = locale == "ru" ? "Тестовая услуга" : "Synthetic service";
            Assert.True(field.Focus());
            window.KeyTextInput(text);
            Assert.Equal(text, field.Text);
            combo.SelectedIndex = 1;
            checkbox.IsChecked = true;
            Assert.Equal(1, combo.SelectedIndex);
            Assert.True(checkbox.IsChecked == true);
            var saved = 0;
            primary.Click += (_, _) => saved++;
            // Routed event exercises the host callback, not real pointer input.
            primary.RaiseEvent(new RoutedEventArgs(Button.ClickEvent));
            Assert.Equal(1, saved);
            primary.IsEnabled = false;
            Assert.False(primary.IsEnabled);
            Assert.Equal(PaletteColor(palette, "TkDisabledBgBrush"), BrushColor(primary.Background));
            Assert.Equal(PaletteColor(palette, "TkDisabledTextBrush"), BrushColor(primary.Foreground));
        }
        finally { window.Close(); }
    }
}
