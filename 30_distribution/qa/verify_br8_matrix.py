#!/usr/bin/env python3
"""Aggregate the full independent SDK acceptance matrix, never grant release approval."""
import argparse
import json
import math
import statistics
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
BASE_CHECKS.update({"all 72 localized axe scans","no detected localized axe violations"})
BASE_CHECKS.update({"standalone Web canonical archive","standalone Web exact lock","standalone Web installed identity"})
BASE_CHECKS.update(p+" "+label for p in ("@taktera/ui-core","@taktera/ui-react") for label in ("canonical archive","exact npm integrity","installed identity"))
SCENARIO_CHECKS=("product/theme","registry filtering","scheduler booking","CRM host save","analytics export available","notification state","Web Core callback","synthetic state reset","no browser errors","no external requests","separate audit document state","audit no browser errors","audit no external requests")
TRANSPORT_CHECKS=("initial","locale","validation","accessible error","unavailable","retry","idempotent replay","competing write","conflict","reload current","draft reloaded","resolved save","literal markup saved","markup stays inert","keyboard focus forward","keyboard focus reverse","keyboard save","event attribute inert")
OPERATIONS_CHECKS=("locale","initial booking","week mode","timezone","scheduler conflict","scheduler applied","analytics complete","invalid period retained","incomplete export denied","table mode","day details","csv exact bytes","local overlap blocked","scheduler create","scheduler cancellation","atomic series create","series occurrences visible")
EXPECTED_CHECKS=BASE_CHECKS|{p+"/"+t+" "+label for p,t in SCENARIOS for label in SCENARIO_CHECKS}|{p+"/"+t+" "+locale+" transport "+label for p,t in SCENARIOS for locale in ("en","ru") for label in TRANSPORT_CHECKS}|{p+"/"+t+" "+locale+" operations "+label for p,t in SCENARIOS for locale in ("en","ru") for label in OPERATIONS_CHECKS}|{p+"/"+t+" "+locale+" web transport "+label for p,t in SCENARIOS for locale in ("en","ru") for label in TRANSPORT_CHECKS}|{p+"/"+t+" standalone Web "+label for p,t in SCENARIOS for label in ("product/theme","no browser errors","no external requests")}|{p+"/"+t+" "+locale+" "+surface+" audit "+label for p,t in SCENARIOS for locale in ("en","ru") for surface in ("transport","operations","web") for label in ("state","no browser errors","no external requests")}


# Provisional engineering smoke thresholds, not approved product SLA.
PERFORMANCE_LIMITS={"reactNavigationMs":5000,"webNavigationMs":5000,"reactSaveMs":2000,"webSaveMs":2000}
def performance_report(record):
    data=record["performance"]
    result={}
    for metric,limit in PERFORMANCE_LIMITS.items():
        rows=data[metric]
        keys=[(r["product"],r["theme"],r["locale"]) if metric.endswith("SaveMs") else (r["product"],r["theme"]) for r in rows]
        expected={(p,t,l) for p,t in SCENARIOS for l in ("en","ru")} if metric.endswith("SaveMs") else SCENARIOS
        require(len(keys)==len(expected) and set(keys)==expected,"Missing or duplicate performance samples: "+metric)
        values=sorted(r["ms"] for r in rows)
        require(all(type(v) in (int,float) and math.isfinite(v) and v>0 for v in values),"Invalid performance sample: "+metric)
        p95=values[math.ceil(.95*len(values))-1]
        require(p95<=limit,"Provisional performance smoke budget exceeded: "+metric)
        result[metric]={"samples":len(values),"p50Ms":statistics.median(values),"p95Ms":p95,"maxMs":values[-1],"provisionalLimitMs":limit}
    return result

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
    localized=record["localizedAxe"]
    localized_keys=[(r["product"],r["theme"],r["locale"],r["surface"]) for r in localized]
    expected_localized={(p,t,l,s) for p,t in SCENARIOS for l in ("en","ru") for s in ("transport","operations","web")}
    require(len(localized_keys)==len(expected_localized) and set(localized_keys)==expected_localized,"Incomplete localized axe matrix")
    require(all(r["violations"]==[] and isinstance(r["incomplete"],list) for r in localized),"Localized axe violation or incomplete report")
    checks=record["checks"]
    names={r["name"] for r in checks}
    require(len(checks)==len(names),"Duplicate browser check")
    require(names==EXPECTED_CHECKS,"Browser check name mismatch; missing="+repr(sorted(EXPECTED_CHECKS-names))+"; unexpected="+repr(sorted(names-EXPECTED_CHECKS)))
    require(all(r["ok"] is True for r in checks),"Failed browser check")
    return {"checks":len(checks),"scenarios":len(record["scenarios"]),"axeScans":len(record["axe"]),
            "localizedAxeScans":len(localized),"violations":0,"incompleteFindings":sum(len(r["incomplete"]) for r in record["axe"]+localized),"performance":performance_report(record)}

def native_report(record,system,actual,dossier_sha):
    identity(record,actual,dossier_sha)
    require(record["os"]==system and record["dependencyGraphMatch"] is True,"Native OS or graph mismatch")
    name,=[n for n in actual["canonicalPackages"] if n.endswith(".nupkg")]
    require(record["package"]["name"]==name and record["package"]["sha256"]==actual["canonicalPackages"][name],"Native package mismatch")
    require(record["scenarios"]=={n:"Passed" for n in MATRIX_TESTS} and record["totalTests"]==len(MATRIX_TESTS|BASELINE_TESTS),"Native test coverage mismatch")
    elapsed=record["performance"]["cleanConsumerWallSeconds"]
    require(type(elapsed) in (int,float) and math.isfinite(elapsed) and 0<elapsed<=900,"Native clean consumer smoke budget exceeded")
    return {"scenarios":len(MATRIX_TESTS),"tests":record["totalTests"],"performance":{"cleanConsumerWallSeconds":elapsed,"provisionalLimitSeconds":900}}

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
            "publicationAllowed":False,"ownerApproved":False,"signed":False,"manualAcceptance":"pending","performanceBudgetApproval":"pending-owner-review",
            "localizationTransportAcceptance":"localized-react-and-web-host-transport-scheduler-analytics-automated-only","scope":"English package-only browser workflows and registry axe; RU/EN host transport, scheduler single-record updates and analytics CSV; native headless RU/EN host labels; not full BR8/BR9, production, native graphical or WCAG certification"}
    (out/"acceptance-summary.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"br8Acceptance":result},sort_keys=True))

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for n in ("candidate","canonical","dossier","download","output"):p.add_argument(n,type=Path)
    a=p.parse_args()
    main(a.candidate,a.canonical,a.dossier,a.download,a.output)
