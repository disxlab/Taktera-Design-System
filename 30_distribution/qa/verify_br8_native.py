#!/usr/bin/env python3
"""Run exact canonical Avalonia package-only acceptance on Windows/macOS."""
import argparse
import json
import os
import platform
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from verify_candidate_download import verify, require, read, sha, safe_path
ROOT=Path(__file__).resolve().parents[2]
PRODUCTS=("Platform","Clinic","Beauty","Spa","Fitness","Travel")
THEMES=("Light","Dark")
LOCALES=("ru","en")
BASELINE_TESTS={"PublicResourceContractRemainsCompatible","AllTwelvePackagedPalettesResolveBrushes","ActualSampleLoadsAndUsesThemes","RealSampleAcceptsHeadlessTextInput","SelectionAndCheckStateAreAvailable"}
MATRIX_TESTS={p+"_"+t+"_"+l for p in PRODUCTS for t in THEMES for l in LOCALES}
def validate_trx(path):
    root=ET.parse(path).getroot()
    tests=[e for e in root.iter() if e.tag.rsplit("}",1)[-1]=="UnitTestResult"]
    seen={}
    for e in tests:
        require(e.get("outcome")=="Passed","Non-passing native test")
        name=e.get("testName","").rsplit(".",1)[-1]
        require(name in BASELINE_TESTS|MATRIX_TESTS,"Unexpected native test: "+name)
        require(name not in seen,"Duplicate native test: "+name)
        seen[name]="Passed"
    require(set(seen)==BASELINE_TESTS|MATRIX_TESTS,"Incomplete native test coverage")
    return {name:seen[name] for name in sorted(MATRIX_TESTS)}

def graph(data):
    return {k.lower():v["sha512"] for k,v in data["libraries"].items() if v["type"]=="package"}
def main(candidate,canonical,dossier,out):
    source=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    require(source==os.environ["GITHUB_SHA"],"Unexpected checkout")
    actual=verify(candidate,canonical,source,os.environ["GITHUB_RUN_ID"],os.environ["GITHUB_RUN_ATTEMPT"])
    dpath=safe_path(dossier,"release-dossier.json")
    d=read(dpath)
    require(d["status"]=="draft-evidence-only" and d["ownerApproved"] is False and d["publicationAllowed"] is False and d["signed"] is False,"Unexpected approval")
    require(all(d[k]==actual[k] for k in ("sourceCommit","githubRunId","githubRunAttempt","candidateManifestSha256")),"Dossier identity mismatch")
    require({v["filename"]:v["sha256"] for v in d["packages"].values()}==actual["canonicalPackages"],"Dossier package mismatch")
    os_name={"Windows":"windows","Darwin":"macos"}.get(platform.system())
    require(os_name is not None,"Unsupported native acceptance OS")
    env=dict(os.environ,TAKTERA_CANONICAL_INPUT=str(canonical.resolve()),TAKTERA_BR8_NATIVE="1")
    subprocess.run([sys.executable,str(ROOT/"30_distribution/qa/verify_nuget_consumer.py")],cwd=ROOT,env=env,check=True)
    results=ROOT/"30_distribution/qa/results/nuget"
    report=read(results/"report.json")
    require(report["errors"]==[] and report["mode"]=="canonical" and report["canonicalSource"]==source
            and all(x["ok"] is True for x in report["checks"]),"Native consumer failed")
    pkg=report["package"]
    require(pkg["sha256"]==actual["canonicalPackages"][pkg["name"]],"Native package digest mismatch")
    previous=read(safe_path(candidate,"evidence/nuget-"+os_name+"/consumer-project.assets.json"))
    require(graph(previous)==graph(read(results/"consumer-project.assets.json")),"Native application dependency graph changed")
    cases=validate_trx(results/"consumer.trx")
    tests_count=len(cases)+len(BASELINE_TESTS)
    out.mkdir(parents=True,exist_ok=False)
    result={"status":"passed","sourceCommit":source,"githubRunId":actual["githubRunId"],
            "githubRunAttempt":actual["githubRunAttempt"],"candidateManifestSha256":actual["candidateManifestSha256"],
            "dossierSha256":sha(dpath.read_bytes()),"os":os_name,"package":pkg,
            "scenarios":cases,"totalTests":tests_count,"dependencyGraphMatch":True,"publicationAllowed":False,
            "scope":"Headless package-only palette, local host localization and interaction tests; not graphical desktop, actual pointer input, accessibility or production acceptance"}
    (out/"native-acceptance.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"nativeAcceptance":{"status":"passed","os":os_name,"scenarios":len(cases),"tests":tests_count,"dependencyGraphMatch":True}}))
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for n in ("candidate","canonical","dossier","output"):p.add_argument(n,type=Path)
    a=p.parse_args()
    main(a.candidate,a.canonical,a.dossier,a.output)
