# Avalonia ControlThemes · v4.0 alpha.2

**Target:** .NET 10, Avalonia 11.3.22. Package contains `TkControls.axaml`, a named `TkPrimaryButton`, `TkSecondaryButton`, and opt-in `tku-field` / `tku-check` class styles. Color brushes are consumed from the 12 unchanged product/theme dictionaries in `15_platform_adapters/avalonia/`.

The `sample/` is an **uncompiled** Avalonia source application for development machines. It includes an explicit resource merge and examples. Run from that directory:

```bash
dotnet restore
dotnet run
```

The .NET SDK and NuGet packages are not available in this execution environment. XML well-formedness and resource references can be verified, but this does **not** establish Avalonia XAML compilation, correct native rendering, or keyboard/screen-reader conformance. Control theme semantics follow official Avalonia documentation: https://docs.avaloniaui.net/docs/styling/control-themes .

**Scope:** no global override of Fluent controls, no advanced DataGrid/scheduler, no native focus test, no WPF-style cross-framework assumptions. Evaluate separately before use in Taktera.Mail or ERP products.

## BR6 package candidate
The earlier uncompiled statement describes the original Alpha snapshot. CI has since confirmed sample compilation and headless QA. New compiled package candidate: library/Taktera.UI.Avalonia.csproj. Independent PackageReference consumer: ../../30_distribution/reference-dotnet. Run python 30_distribution/qa/verify_nuget_consumer.py at root. Package CI and native manual QA remain separate gates.
