#!/usr/bin/env python3
"""BR7-01: compare exact npm and NuGet archives from two isolated clean builds."""
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "30_distribution/qa/results/reproducible"
OUT.mkdir(parents=True, exist_ok=True)
NODE = "v26.13.1"
DOTNET = "10.0.404"
NPM = "11.20.0"
report = {"scope": "same source, same pinned toolchain, isolated worktrees and caches",
          "source": None, "toolchain": {}, "builds": [], "comparisons": [], "errors": [],
          "nugetLockPolicy": "first restore generates lock; second uses locked mode; committed lock pending",
          "canonicalCrossOsConsumer": False, "passed": False}

def run(args, cwd=ROOT, env=None):
    print("+", " ".join(map(str, args)), flush=True)
    return subprocess.check_output(list(map(str, args)), cwd=cwd, env=env, text=True).strip()

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def zip_entries(path):
    with zipfile.ZipFile(path) as z:
        return {i.filename: {"sha256": hashlib.sha256(z.read(i)).hexdigest(),
                             "timestamp": list(i.date_time), "compression": i.compress_type}
                for i in z.infolist()}

def build(tree, work, lock):
    dest = work / "out"
    dest.mkdir()
    env = dict(os.environ, npm_config_cache=str(work / "npm-cache"),
               NUGET_PACKAGES=str(work / "nuget-cache"),
               DOTNET_CLI_HOME=str(work / "dotnet-home"),
               DOTNET_CLI_TELEMETRY_OPTOUT="1", AVALONIA_TELEMETRY_OPTOUT="1",
               MSBUILDDISABLENODEREUSE="1", DOTNET_CLI_USE_MSBUILD_SERVER="0",
               TZ="UTC", LC_ALL="C.UTF-8")
    actual = {"node": run(["node", "--version"], tree, env),
              "npm": run(["npm", "--version"], tree, env),
              "dotnet": run(["dotnet", "--version"], tree, env)}
    if actual != {"node": NODE, "npm": NPM, "dotnet": DOTNET}:
        raise RuntimeError(f"Unexpected isolated build toolchain: {actual}")
    react = tree / "17_packages/react"
    web = tree / "17_packages/web-core"
    run(["npm", "ci", "--no-audit", "--no-fund"], react, env)
    run(["npm", "run", "build"], react, env)
    for package in (react, web):
        run(["npm", "pack", "--ignore-scripts", "--pack-destination", dest], package, env)
    lib = tree / "17_packages/avalonia/library"
    assets = lib / "Assets"
    assets.mkdir()
    for name in ("TkControls.axaml", "TkFieldStyles.axaml"):
        shutil.copyfile(tree / "17_packages/avalonia" / name, assets / name)
    for source in sorted((tree / "27_beta_readiness_3/avalonia_compat").glob("Taktera.*.axaml")):
        shutil.copyfile(source, assets / source.name)
    if len(list(assets.glob("*.axaml"))) != 14:
        raise RuntimeError("Unexpected Avalonia resource inventory")
    cfg = work / "NuGet.Config"
    config = ET.Element("configuration")
    sources = ET.SubElement(config, "packageSources")
    ET.SubElement(sources, "clear")
    ET.SubElement(sources, "add", key="nuget.org", value="https://api.nuget.org/v3/index.json")
    ET.ElementTree(config).write(cfg, encoding="utf-8", xml_declaration=True)
    project = lib / "Taktera.UI.Avalonia.csproj"
    local_lock = lib / "packages.lock.json"
    if lock.exists():
        if local_lock.exists() and local_lock.read_bytes() != lock.read_bytes():
            raise RuntimeError("Committed NuGet lock differs from first build")
        shutil.copyfile(lock, local_lock)
    restore = ["dotnet", "restore", project, "--configfile", cfg, "--use-lock-file",
               "-p:NuGetAudit=true", "-p:NuGetAuditMode=all",
               "-warnaserror:NU1900,NU1903,NU1904,NU1905"]
    if lock.exists() or local_lock.exists():
        restore.append("--locked-mode")
    run(restore, lib, env)
    if not lock.exists():
        shutil.copyfile(local_lock, lock)
    if local_lock.read_bytes() != lock.read_bytes():
        raise RuntimeError("NuGet lock changed between builds")
    run(["dotnet", "pack", project, "-c", "Release", "--no-restore",
         "--disable-build-servers", "-o", dest, "-warnaserror",
         "-p:ContinuousIntegrationBuild=true", "-p:Deterministic=true",
         f"-p:PathMap={tree}=/src"], lib, env)
    packages = sorted(p for p in dest.iterdir() if p.suffix in (".tgz", ".nupkg"))
    if len(packages) != 3 or sum(p.suffix == ".nupkg" for p in packages) != 1:
        raise RuntimeError("Expected exactly two npm tarballs and one NuGet package")
    return packages

try:
    report["source"] = run(["git", "rev-parse", "HEAD"])
    report["toolchain"] = {"node": run(["node", "--version"]), "npm": run(["npm", "--version"]),
                           "dotnet": run(["dotnet", "--version"]), "python": run(["python", "--version"])}
    if (report["toolchain"]["node"] != NODE or report["toolchain"]["dotnet"] != DOTNET
            or report["toolchain"]["npm"] != NPM):
        raise RuntimeError(f"Unexpected release toolchain: {report['toolchain']}")
    with tempfile.TemporaryDirectory(prefix="taktera-repro-") as tmp:
        temp = Path(tmp).resolve()
        lock = temp / "packages.lock.json"
        results = []
        for name in ("a", "b"):
            tree = temp / ("checkout-" + name)
            work = temp / ("build-" + name)
            work.mkdir()
            run(["git", "worktree", "add", "--detach", tree, report["source"]])
            try:
                if run(["git", "status", "--porcelain"], tree):
                    raise RuntimeError("Checkout was not clean")
                packages = build(tree, work, lock)
                dest = OUT / name
                dest.mkdir()
                for p in packages:
                    shutil.copyfile(p, dest / p.name)
                result = {p.name: sha(p) for p in packages}
                results.append(result)
                report["builds"].append({"name": name, "packages": result})
            finally:
                run(["git", "worktree", "remove", "--force", tree])
        shutil.copyfile(lock, OUT / "packages.lock.json")
        if set(results[0]) != set(results[1]):
            raise RuntimeError("Package filenames differ")
        for name, first in results[0].items():
            second = results[1][name]
            item = {"file": name, "sha256A": first, "sha256B": second, "identical": first == second}
            if first != second and name.endswith(".nupkg"):
                a, b = zip_entries(OUT / "a" / name), zip_entries(OUT / "b" / name)
                item["zipEntryDifferences"] = [
                    {"entry": key, "a": a.get(key), "b": b.get(key)}
                    for key in sorted(set(a) | set(b)) if a.get(key) != b.get(key)]
            report["comparisons"].append(item)
        report["passed"] = all(item["identical"] for item in report["comparisons"])
        if not report["passed"]:
            report["errors"].append("Exact package SHA-256 mismatch; do not promote release")
except Exception as exc:
    report["errors"].append(str(exc))
finally:
    (OUT / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
if not report["passed"] or report["errors"]:
    raise SystemExit(1)
