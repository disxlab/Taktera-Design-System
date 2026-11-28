# Taktera CLI (candidate)
Run Python 3.12 from the design-system checkout. Use a directory containing trusted, verified tarballs or one NuGet candidate. CLI copies packages into a local vendor folder, records SHA-256 and does not install dependencies or publish. It refuses existing destinations and ambiguous package identities.

```sh
python 30_distribution/taktera.py init react --packages /path/to/npm-artifacts --output /path/to/new-react-app
python 30_distribution/taktera.py init web --packages /path/to/npm-artifacts --output /path/to/new-web-app
python 30_distribution/taktera.py init avalonia --packages /path/to/one-nuget-artifact --output /path/to/new-desktop-app
```

Open generated README.md. React: generate package-lock.json, npm ci, npm run build, npm start. Web: generate lock, npm ci, npm start. Local dev servers bind loopback (default port 4173, PORT override). Avalonia: dotnet restore --configfile NuGet.Config; dotnet run --no-restore. Preserve lockfiles and package-inventory.json. All fixtures synthetic. No global install or registry credentials required. External React/.NET dependencies still require authorized feeds; scaffold itself is offline. Verify supplied files against trusted candidate evidence before using them.
