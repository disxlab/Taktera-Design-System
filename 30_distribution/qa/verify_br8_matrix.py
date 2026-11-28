#!/usr/bin/env python3
"""Aggregate the full independent SDK acceptance matrix, never grant release approval."""
import argparse
import json
import os
import subprocess
from pathlib import Path
from verify_candidate_download import verify, require, read, sha, safe_path
from verify_br8_native import MATRIX_TESTS, BASELINE_TESTS

ROOT=Path(__file__).resolve().parents[2]
ENGINES=("chromium","firefox","webkit")
SYSTEMS=("windows","macos")
SCENARIOS={(p,t) for p in ("platform","clinic","beauty","spa","fitness","travel") for t in ("light","dark")}
BASE_CHECKS={"exact Node","exact npm","original consumer lock","lock unchanged after npm ci","strict TypeScript build from packages",
             "all 12 scenarios completed","all 12 registry axe scans","no detected axe violations"}
BASE_CHECKS.update(p+" "+label for p in ("@taktera/ui-core","@taktera/ui-react") for label in ("canonical archive","exact npm integrity","installed identity"))
SCENARIO_CHECKS=("product/theme","registry filtering","scheduler booking","CRM host save","analytics export available","notification state","Web Core callback","synthetic state reset","no browser errors","no external requests","separate audit document state","audit no browser errors","audit no external requests")
EXPECTED_CHECKS=BASE_CHECKS|{p+"/"+t+" "+label for p,t in SCENARIOS for label in SCENARIO_CHECKS}

def identity(record,actual,dossier_sha):
    for key in ("sourceCommit","githubRunId","githubRunAttempt","candidateManifestSha256"):
        require(record.get(key)==actual[key],"Acceptance identity mismatch: "+key)
    require(record.get("dossierSha256")==dossier_sha,"Acceptance dossier digest mismatch")
    require(record.get("status")=="passed" and record.get("publicationAllowed") is False,"Invalid acceptance status")

def exact_matrix(rows):
    keys=[(r["product"],r["theme"]) for r in rows]
    require(len(keys)==len(SCENARIOS) and set(keys)==SCENARIOS,"Missing, duplicate or unexpected browser scenario")

def browser_report(record,engine,actual,dossier_sha,lock_sha):
    identity(record,actual,dossier_sha)
    require(record.get("engine")==engine and record.get("canonicalPackages")==actual["canonicalPackages"],"Browser engine/package mismatch")
    require(record.get("consumerLockSha256")==lock_sha and record.get("errors")==[],"Browser lock/errors mismatch")
    exact_matrix(record["scenarios"])
    require(all(r["status"]=="passed" for r in record["scenarios"]),"Failed browser scenario")
    exact_matrix(record["axe"])
    require(all(r["page"]=="registry" and r["violations"]==[] and isinstance(r["incomplete"],list) for r in record["axe"]),"Failed/missing accessibility scan")
    checks=record["checks"]
    require(len(checks)==len(EXPECTED_CHECKS) and {r["name"] for r in checks}==EXPECTED_CHECKS and all(r["ok"] is True for r in checks),"Missing, duplicate, failed or unexpected browser check")
    return {"checks":len(checks),"scenarios":len(record["scenarios"]),"axeScans":len(record["axe"]),
            "violations":0,"incompleteFindings":sum(len(r["incomplete"]) for r in record["axe"])}

def native_report(record,system,actual,dossier_sha):
    identity(record,actual,dossier_sha)
    require(record["os"]==system and record["dependencyGraphMatch"] is True,"Native OS or graph mismatch")
    name,=[n for n in actual["canonicalPackages"] if n.endswith(".nupkg")]
    require(record["package"]["name"]==name and record["package"]["sha256"]==actual["canonicalPackages"][name],"Native package mismatch")
    require(record["scenarios"]=={n:"Passed" for n in MATRIX_TESTS} and record["totalTests"]==len(MATRIX_TESTS|BASELINE_TESTS),"Native test coverage mismatch")
    return {"scenarios":len(MATRIX_TESTS),"tests":record["totalTests"]}

def main(candidate,canonical,dossier,download,out):
    source=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    require(source==os.environ["GITHUB_SHA"],"Unexpected checkout")
    actual=verify(candidate,canonical,source,os.environ["GITHUB_RUN_ID"],os.environ["GITHUB_RUN_ATTEMPT"])
    dpath=safe_path(dossier,"release-dossier.json")
    d=read(dpath)
    digest=sha(dpath.read_bytes())
    require(d["status"]=="draft-evidence-only" and d["publicationAllowed"] is False and d["ownerApproved"] is False and d["signed"] is False,"Unexpected release approval")
    require(all(d[k]==actual[k] for k in ("sourceCommit","githubRunId","githubRunAttempt","candidateManifestSha256")),"Dossier identity mismatch")
    require({p["filename"]:p["sha256"] for p in d["packages"].values()}==actual["canonicalPackages"],"Dossier package mismatch")
    lock_sha=sha(safe_path(candidate,"evidence/npm/consumer-package-lock.json").read_bytes())
    browser={}
    native={}
    evidence={}
    for engine in ENGINES:
        path=safe_path(download,"br8-canonical-browser-"+engine+"/canonical-browser-acceptance.json")
        browser[engine]=browser_report(read(path),engine,actual,digest,lock_sha)
        evidence[path.relative_to(download).as_posix()]=sha(path.read_bytes())
    for system,artifact in (("windows","windows-latest"),("macos","macos-latest")):
        path=safe_path(download,"br8-canonical-native-"+artifact+"/br8-native-evidence/native-acceptance.json")
        native[system]=native_report(read(path),system,actual,digest)
        evidence[path.relative_to(download).as_posix()]=sha(path.read_bytes())
    out.mkdir(parents=True,exist_ok=False)
    result={**{k:actual[k] for k in ("sourceCommit","githubRunId","githubRunAttempt","candidateManifestSha256","canonicalPackages")},
            "status":"automated-matrix-passed","dossierSha256":digest,"browser":browser,"native":native,"evidenceSha256":evidence,
            "publicationAllowed":False,"ownerApproved":False,"signed":False,"manualAcceptance":"pending",
            "localizationTransportAcceptance":"pending","scope":"English package-only browser workflows and registry axe; native headless RU/EN host labels; not full BR8/BR9, production, native graphical or WCAG certification"}
    (out/"acceptance-summary.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"br8Acceptance":result},sort_keys=True))

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for n in ("candidate","canonical","dossier","download","output"):p.add_argument(n,type=Path)
    a=p.parse_args()
    main(a.candidate,a.canonical,a.dossier,a.download,a.output)
