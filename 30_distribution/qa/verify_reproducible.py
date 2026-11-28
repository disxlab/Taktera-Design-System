#!/usr/bin/env python3
"""BR7-01: compare exact npm and NuGet archives from two isolated clean builds."""
import hashlib
import datetime
import struct
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
          "nugetLockPolicy": "committed NuGet lock; all four restores use locked mode",
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

def pe_comparison(a, b):
    """Read-only diagnostics; never mutate or normalize compiled assemblies."""
    x, y = a.read_bytes(), b.read_bytes()
    def header(data):
        offset = struct.unpack_from("<I", data, 0x3c)[0]
        if data[:2] != b"MZ" or data[offset:offset+4] != b"PE\0\0":
            raise RuntimeError("Invalid PE diagnostic assembly")
        return {"coffTimestamp": struct.unpack_from("<I", data, offset+8)[0],
                "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    differences = [i for i, (u, v) in enumerate(zip(x, y)) if u != v]
    return {"a": header(x), "b": header(y), "identical": x == y,
            "differentByteCount": len(differences) + abs(len(x)-len(y)),
            "firstDifferentOffsets": differences[:32]}

def build(tree, work, lock):
    dest = work / "out"
    dest.mkdir()
    epoch = run(["git", "show", "-s", "--format=%ct", report["source"]], tree)
    stamp = datetime.datetime.fromtimestamp(int(epoch), datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    env = dict(os.environ, npm_config_cache=str(work / "npm-cache"),
               NUGET_PACKAGES=str(work / "nuget-cache"),
               DOTNET_CLI_HOME=str(work / "dotnet-home"),
               DOTNET_CLI_TELEMETRY_OPTOUT="1", AVALONIA_TELEMETRY_OPTOUT="1",
               MSBUILDDISABLENODEREUSE="1", DOTNET_CLI_USE_MSBUILD_SERVER="0",
               TZ="UTC", LC_ALL="C.UTF-8", SOURCE_DATE_EPOCH=epoch)
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
    if not local_lock.is_file():
        raise RuntimeError("Committed NuGet lock is required")
    restore.append("--locked-mode")
    run(restore, lib, env)
    if local_lock.read_bytes() != lock.read_bytes():
        raise RuntimeError("NuGet lock changed between builds")
    diagnostics = work / "diagnostics"
    diagnostics.mkdir()
    run(["dotnet", "pack", project, "-c", "Release", "--no-restore",
         "--disable-build-servers", "-o", dest, "-warnaserror",
         "-p:ContinuousIntegrationBuild=true", "-p:Deterministic=true",
         f"-p:PathMap={work}=/build", f"-p:DeterministicTimestamp={stamp}",
         f"-p:TakteraReproEvidenceDirectory={diagnostics}"], lib, env)
    for name in ("before-xaml.dll", "after-xaml.dll"):
        if not (diagnostics / name).is_file():
            raise RuntimeError("Missing compiler-stage diagnostic: " + name)
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
        shutil.copyfile(ROOT / "17_packages/avalonia/library/packages.lock.json", lock)
        results = []
        for name in ("a", "b"):
            work = temp / ("build-" + name)
            work.mkdir()
            tree = work / "checkout"
            run(["git", "worktree", "add", "--detach", tree, report["source"]])
            try:
                if run(["git", "status", "--porcelain"], tree):
                    raise RuntimeError("Checkout was not clean")
                packages = build(tree, work, lock)
                dest = OUT / name
                dest.mkdir()
                for p in packages:
                    shutil.copyfile(p, dest / p.name)
                shutil.copytree(work / "diagnostics", dest / "compiler-stages")
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
        report["compilerStages"] = {}
        for name in ("before-xaml.dll", "after-xaml.dll"):
            a = OUT / "a" / "compiler-stages" / name
            b = OUT / "b" / "compiler-stages" / name
            report["compilerStages"][name] = pe_comparison(a, b)
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
