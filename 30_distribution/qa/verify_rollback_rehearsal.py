#!/usr/bin/env python3
"""Historical candidate recovery rehearsal in an isolated local workspace only."""
import argparse
import base64
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from verify_candidate_download import verify, require, read, sha, safe_path
from product_sbom import archive_files

ROOT=Path(__file__).resolve().parents[2]

def validate_historical(candidate,canonical,baseline):
    require(baseline["approvedRelease"] is False,"Not an approved production rollback target")
    result=verify(candidate,canonical,baseline["sourceCommit"],baseline["githubRunId"],baseline["githubRunAttempt"])
    require(result["candidateManifestSha256"]==baseline["candidateManifestSha256"]
            and result["canonicalPackages"]==baseline["canonicalPackages"],"Historical baseline digest mismatch")
    return result

def collision_check(previous,current):
    return sorted(name for name in previous if name in current and previous[name]!=current[name])

def run(args,cwd,env):
    subprocess.run(args,cwd=cwd,env=env,check=True,timeout=240)

def stage(target,source,expected):
    target.mkdir()
    for name,digest in expected.items():
        p=safe_path(source,name)
        require(sha(p.read_bytes())==digest,"Snapshot archive mismatch: "+name)
        shutil.copyfile(p,target/name)
    validate_snapshot(target,expected)

def validate_snapshot(path,expected):
    require(path.is_dir() and not path.is_symlink(),"Unsafe snapshot directory")
    require({p.name for p in path.iterdir()}==set(expected),"Snapshot set mismatch")
    for name,digest in expected.items():
        require(sha(safe_path(path,name).read_bytes())==digest,"Snapshot digest mismatch: "+name)

def select_pointer(work,slot,expected):
    require(slot in ("current","historical"),"Invalid snapshot selection")
    validate_snapshot(work/slot,expected)
    temp=work/"active.tmp"
    temp.write_text(slot+"\n",encoding="utf-8")
    os.replace(temp,work/"active.txt")

def consumers(feed,work,expected,env):
    # Independent fresh starter projects, no Taktera Platform sources.
    react=work/"restored-react"
    run([sys.executable,str(ROOT/"30_distribution/taktera.py"),"init","react","--packages",str(feed),"--output",str(react)],work,env)
    inventory=read(react/"package-inventory.json")
    require(len(inventory)==2,"Incomplete restored React package inventory")
    for item in inventory:
        p=safe_path(react,item["file"])
        require(sha(p.read_bytes())==item["sha256"]==expected[p.name],"Restored npm archive mismatch")
    run(["npm","install","--package-lock-only","--ignore-scripts","--no-audit","--no-fund"],react,env)
    run(["npm","ci","--ignore-scripts","--no-audit","--no-fund"],react,env)
    run(["npm","run","build"],react,env)
    lock=read(react/"package-lock.json")
    for item in inventory:
        p=safe_path(react,item["file"])
        entry=lock["packages"]["node_modules/"+item["name"]]
        require(entry["integrity"]=="sha512-"+base64.b64encode(hashlib.sha512(p.read_bytes()).digest()).decode(),
                "Restored npm lock integrity mismatch")
        for member,data in archive_files(p).items():
            if member.startswith("package/"):
                relative=member[len("package/"):]
                installed=safe_path(react/"node_modules"/item["name"],relative)
                require(installed.read_bytes()==data,"Installed npm file mismatch: "+member)
    smoke=react/"rollback-smoke.mjs"
    smoke.write_text("import React from 'react';import {renderToString} from 'react-dom/server';import {App} from './dist/App.js';const html=renderToString(React.createElement(App));if(!html.includes('Synthetic Alice'))throw Error('Restored React SSR failed');\n",encoding="utf-8")
    run(["node",str(smoke)],react,env)
    native=work/"restored-native"
    run([sys.executable,str(ROOT/"30_distribution/taktera.py"),"init","avalonia","--packages",str(feed),"--output",str(native)],work,env)
    item,=read(native/"package-inventory.json")
    archive=safe_path(native,item["file"])
    require(sha(archive.read_bytes())==item["sha256"]==expected[archive.name],"Restored native archive mismatch")
    # Restrict this isolated consumer to the exact historical public dependency IDs.
    import xml.etree.ElementTree as ET
    config=native/"NuGet.Config"
    tree=ET.parse(config)
    mapping=tree.find("./packageSourceMapping/packageSource[@key='nuget.org']")
    for child in list(mapping): mapping.remove(child)
    for name in sorted(read(feed.parent/"historical-lock.json")["dependencies"]["net10.0"]):
        ET.SubElement(mapping,"package",pattern=name)
    tree.write(config,encoding="utf-8",xml_declaration=True)
    proj=native/"Taktera.Reference.csproj"
    require(not ET.parse(proj).findall(".//ProjectReference"),"Non-independent native consumer")
    run(["dotnet","restore",str(proj),"--configfile",str(config),"-p:NuGetAudit=true","-p:NuGetAuditMode=all",
         "-warnaserror:NU1900,NU1903,NU1904,NU1905"],native,env)
    run(["dotnet","build",str(proj),"-c","Release","--no-restore","--disable-build-servers","-warnaserror"],native,env)
    restored=Path(env["NUGET_PACKAGES"])/item["name"].lower()/item["version"].lower()
    package=restored/(item["name"].lower()+"."+item["version"].lower()+".nupkg")
    require(sha(package.read_bytes())==expected[archive.name],"Restored NuGet package differs")
    require((restored/"lib/net10.0/Taktera.UI.Avalonia.dll").read_bytes()==archive_files(archive)["lib/net10.0/Taktera.UI.Avalonia.dll"],
            "Restored NuGet assembly differs")
    return ["fresh-react-install","npm-lock-and-installed-bytes","react-typescript-build","react-ssr",
            "fresh-avalonia-restore","nuget-archive-and-dll-bytes","avalonia-release-build"]

def main(candidate,canonical,historical,historical_canonical,preflight,out):
    source=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
    require(source==os.environ["GITHUB_SHA"],"Unexpected checkout")
    current=verify(candidate,canonical,source,os.environ["GITHUB_RUN_ID"],os.environ["GITHUB_RUN_ATTEMPT"])
    plan=read(preflight/"release-preflight.json")
    require(plan["status"]=="preflight-passed" and plan["publicationAllowed"] is False
            and all(plan[k]==current[k] for k in ("sourceCommit","githubRunId","githubRunAttempt","candidateManifestSha256","canonicalPackages")),
            "Release preflight mismatch")
    baseline=read(ROOT/"30_distribution/recovery/historical-candidate.json")
    prior=validate_historical(historical,historical_canonical,baseline)
    conflicts=collision_check(prior["canonicalPackages"],current["canonicalPackages"])
    require(conflicts,"Expected historical same-version/different-bytes conflict")
    start=time.monotonic()
    checks=[]
    with tempfile.TemporaryDirectory(prefix="taktera-rollback-") as temp:
        work=Path(temp)
        shutil.copyfile(ROOT/"global.json",work/"global.json")
        shutil.copyfile(historical_canonical/"packages.lock.json",work/"historical-lock.json")
        env=dict(os.environ,NPM_CONFIG_CACHE=str(work/"npm-cache"),NUGET_PACKAGES=str(work/"nuget-cache"),
                 NUGET_HTTP_CACHE_PATH=str(work/"nuget-http"),DOTNET_CLI_HOME=str(work/"dotnet-home"),
                 DOTNET_CLI_TELEMETRY_OPTOUT="1",AVALONIA_TELEMETRY_OPTOUT="1",MSBUILDDISABLENODEREUSE="1")
        for args,version in [(["node","--version"],"v26.13.1"),(["npm","--version"],"11.20.0"),(["dotnet","--version"],"10.0.404")]:
            require(subprocess.check_output(args,cwd=work,env=env,text=True).strip()==version,"Unexpected recovery toolchain")
        stage(work/"current",canonical,current["canonicalPackages"])
        stage(work/"historical",historical_canonical,prior["canonicalPackages"])
        select_pointer(work,"current",current["canonicalPackages"])
        def reject(label,fn):
            try: fn()
            except ValueError: checks.append(label)
            else: raise ValueError("Negative rollback control passed: "+label)
            require((work/"active.txt").read_text()=="current\n","Failed rollback changed active pointer")
        reject("unknown snapshot",lambda:select_pointer(work,"unknown",prior["canonicalPackages"]))
        bad=copy.deepcopy(baseline);bad["candidateManifestSha256"]="0"*64
        reject("untrusted historical manifest",lambda:validate_historical(historical,historical_canonical,bad))
        name=next(iter(prior["canonicalPackages"]))
        p=work/"historical"/name;data=p.read_bytes()
        p.write_bytes(data+b"\n")
        reject("modified recovery archive",lambda:select_pointer(work,"historical",prior["canonicalPackages"]))
        p.unlink()
        reject("missing recovery archive",lambda:select_pointer(work,"historical",prior["canonicalPackages"]))
        p.write_bytes(data)
        extra=work/"historical"/"unexpected.txt";extra.write_text("unexpected")
        reject("unexpected recovery file",lambda:select_pointer(work,"historical",prior["canonicalPackages"]))
        extra.unlink()
        select_pointer(work,"historical",prior["canonicalPackages"])
        require((work/"active.txt").read_text()=="historical\n","Historical selection failed")
        restored=consumers(work/"historical",work,prior["canonicalPackages"],env)
        validate_snapshot(work/"current",current["canonicalPackages"])
        select_pointer(work,"current",current["canonicalPackages"])
        require((work/"active.txt").read_text()=="current\n","Return to current snapshot failed")
    report={"status":"passed","scope":"local historical unsigned candidate rehearsal only","sourceCommit":source,
            "githubRunId":current["githubRunId"],"githubRunAttempt":current["githubRunAttempt"],
            "historicalSourceCommit":prior["sourceCommit"],"historicalRunId":prior["githubRunId"],
            "historicalPackages":prior["canonicalPackages"],"currentPackages":current["canonicalPackages"],
            "sameVersionDifferentBytes":conflicts,"registryOverwriteAllowed":False,"publicationAllowed":False,
            "productionRollbackTested":False,"negativeControls":checks,"restoredConsumerChecks":restored,
            "elapsedSeconds":round(time.monotonic()-start,2),"scopeLimitations":"No real registry, native graphical test, production release, RTO or RPO guarantee."}
    out.mkdir(parents=True,exist_ok=False)
    (out/"rollback-rehearsal.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"rollbackRehearsal":report},sort_keys=True))

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("candidate","canonical","historical","historical_canonical","preflight","output"): p.add_argument(name,type=Path)
    a=p.parse_args()
    main(a.candidate,a.canonical,a.historical,a.historical_canonical,a.preflight,a.output)
