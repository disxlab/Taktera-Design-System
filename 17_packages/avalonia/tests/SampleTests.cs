using Avalonia;
using Avalonia.Controls;
using Avalonia.Headless;
using Avalonia.Headless.XUnit;
using Avalonia.Media;
using Avalonia.VisualTree;
using TakteraUiAvalonia.Sample;
using Xunit;
[assembly: AvaloniaTestApplication(typeof(Taktera.HeadlessTests.TestAppBuilder))]
namespace Taktera.HeadlessTests;
public static class TestAppBuilder
{
    public static AppBuilder BuildAvaloniaApp() =>
        AppBuilder.Configure<App>().UseHeadless(new AvaloniaHeadlessPlatformOptions());
}
public class SampleTests
{
    [AvaloniaFact]
    public void ActualSampleLoadsAndUsesThemes()
    {
        var window = new MainWindow();
        try
        {
            window.Show();
            var buttons = window.GetVisualDescendants().OfType<Button>().ToArray();
            var primary = Assert.Single(buttons.Where(b => Equals(b.Content, "Сохранить")));
            var secondary = Assert.Single(buttons.Where(b => Equals(b.Content, "Отмена")));
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
            var field = Assert.Single(window.GetVisualDescendants().OfType<TextBox>());
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
