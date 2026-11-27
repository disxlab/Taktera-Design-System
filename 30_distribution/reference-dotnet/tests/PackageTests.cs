using Avalonia;
using Avalonia.Controls;
using Avalonia.Headless;
using Avalonia.Headless.XUnit;
using Avalonia.Media;
using Avalonia.VisualTree;
using Taktera.Reference;
using Taktera.UI.Avalonia;
using Avalonia.Markup.Xaml.Styling;
using Xunit;
[assembly: AvaloniaTestApplication(typeof(Taktera.HeadlessTests.TestAppBuilder))]
namespace Taktera.HeadlessTests;
public static class TestAppBuilder
{
    public static AppBuilder BuildAvaloniaApp() =>
        AppBuilder.Configure<App>().UseHeadless(new AvaloniaHeadlessPlatformOptions());
}
public class PackageTests
{
    [AvaloniaFact]
    public void PublicResourceContractRemainsCompatible()
    {
        Assert.Equal(new[] { "Platform", "Clinic", "Beauty", "Spa", "Fitness", "Travel" }, Enum.GetNames<TakteraProduct>());
        Assert.Equal(new[] { "Light", "Dark" }, Enum.GetNames<TakteraTheme>());
        Assert.Equal("avares://Taktera.UI.Avalonia/Assets/TkControls.axaml", TakteraResources.ControlThemes.OriginalString);
        Assert.Equal("avares://Taktera.UI.Avalonia/Assets/TkFieldStyles.axaml", TakteraResources.FieldStyles.OriginalString);
        Assert.Equal("avares://Taktera.UI.Avalonia/Assets/Taktera.Clinic.Dark.axaml", TakteraResources.Palette(TakteraProduct.Clinic,TakteraTheme.Dark).OriginalString);
    }
    [AvaloniaFact]
    public void AllTwelvePackagedPalettesResolveBrushes()
    {
        foreach (var product in Enum.GetValues<TakteraProduct>())
        foreach (var theme in Enum.GetValues<TakteraTheme>())
        {
            var uri = TakteraResources.Palette(product, theme);
            var include = new ResourceInclude(uri) { Source = uri };
            foreach (var key in new[] { "TkCanvasBrush", "TkTextBrush", "TkAccentBrush", "TkFocusRingBrush" })
            {
                Assert.True(include.TryGetResource(key, null, out var value), $"{uri}: {key}");
                Assert.IsAssignableFrom<IBrush>(value);
            }
        }
        Assert.Throws<ArgumentOutOfRangeException>(() => TakteraResources.Palette((TakteraProduct)99, TakteraTheme.Light));
    }
    [AvaloniaFact]
    public void ActualSampleLoadsAndUsesThemes()
    {
        var window = new MainWindow();
        try
        {
            window.Show();
            var buttons = window.GetVisualDescendants().OfType<Button>().ToArray();
            var primary = Assert.Single(buttons, b => Equals(b.Content, "Сохранить"));
            var secondary = Assert.Single(buttons, b => Equals(b.Content, "Отмена"));
            Assert.NotNull(primary.Theme);
            Assert.NotNull(secondary.Theme);
            Assert.NotSame(primary.Theme, secondary.Theme);
            Assert.IsAssignableFrom<IBrush>(primary.Background);
            Assert.IsAssignableFrom<IBrush>(primary.Foreground);
            Assert.True(primary.Bounds.Width > 0);
            Assert.IsAssignableFrom<IBrush>(window.Background);
        }
        finally { window.Close(); }
    }
    [AvaloniaFact]
    public void RealSampleAcceptsHeadlessTextInput()
    {
        var window = new MainWindow();
        try
        {
            window.Show();
            var field = Assert.Single(window.GetVisualDescendants().OfType<TextBox>(), field => field.Classes.Contains("tku-field"));
            Assert.True(field.Focus());
            Assert.True(field.IsFocused);
            window.KeyTextInput("Taktera test");
            Assert.Equal("Taktera test", field.Text);
            Assert.Contains("tku-field", field.Classes);
        }
        finally { window.Close(); }
    }
    [AvaloniaFact]
    public void SelectionAndCheckStateAreAvailable()
    {
        var window = new MainWindow();
        try
        {
            window.Show();
            var combo = Assert.Single(window.GetVisualDescendants().OfType<ComboBox>());
            Assert.Equal(0, combo.SelectedIndex);
            combo.SelectedIndex = 1;
            Assert.Equal("Повторный приём", Assert.IsType<ComboBoxItem>(combo.SelectedItem).Content);
            var check = Assert.Single(window.GetVisualDescendants().OfType<CheckBox>());
            Assert.True(check.Focus());
            check.IsChecked = true;
            Assert.True(check.IsChecked == true);
            Assert.Contains("tku-check", check.Classes);
        }
        finally { window.Close(); }
    }
}
