namespace Taktera.UI.Avalonia;

/// <summary>Supported product palettes.</summary>
public enum TakteraProduct
{
    /// <summary>Platform palette.</summary>
    Platform,
    /// <summary>Clinic palette.</summary>
    Clinic,
    /// <summary>Beauty palette.</summary>
    Beauty,
    /// <summary>Spa palette.</summary>
    Spa,
    /// <summary>Fitness palette.</summary>
    Fitness,
    /// <summary>Travel palette.</summary>
    Travel
}
/// <summary>Explicit theme selection; consumer owns theme lifecycle.</summary>
public enum TakteraTheme
{
    /// <summary>Light palette.</summary>
    Light,
    /// <summary>Dark palette.</summary>
    Dark
}
/// <summary>Resource addresses for the packaged Avalonia design system.</summary>
public static class TakteraResources
{
    private const string Prefix = "avares://Taktera.UI.Avalonia/Assets/";
    /// <summary>Returns selected product and theme dictionary URI.</summary>
    public static Uri Palette(TakteraProduct product, TakteraTheme theme)
    {
        if (!Enum.IsDefined(product)) throw new ArgumentOutOfRangeException(nameof(product));
        if (!Enum.IsDefined(theme)) throw new ArgumentOutOfRangeException(nameof(theme));
        return new Uri($"{Prefix}Taktera.{product}.{theme}.axaml");
    }
    /// <summary>Named opt-in button control themes.</summary>
    public static Uri ControlThemes => new(Prefix + "TkControls.axaml");
    /// <summary>Opt-in text, combo and checkbox styles.</summary>
    public static Uri FieldStyles => new(Prefix + "TkFieldStyles.axaml");
}
