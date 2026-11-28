#!/usr/bin/env python3
"""Fail-closed unsigned release plan. No publishing client or production credentials."""
import argparse
import copy
import json
import os
import subprocess
from pathlib import Path
from verify_candidate_download import verify, require, read, sha, safe_path
from prepare_attestation_subjects import prepare

ROOT=Path(__file__).resolve().parents[2]
BLOCKERS=["signed-provenance-not-activated","license-and-asset-review-pending",
          "real-private-registry-not-configured-or-tested","manual-and-staging-acceptance-pending",
          "owner-release-approval-not-granted","npm-candidate-private-flags-retained"]

def check_identity(record,actual):
    require(record.get("sourceCommit")==actual["sourceCommit"] and
            str(record.get("githubRunId"))==actual["githubRunId"] and
            str(record.get("githubRunAttempt"))==actual["githubRunAttempt"],"Evidence source/run identity mismatch")

def check_registry(report,actual,expected_labels):
    check_identity(report,actual)
    require(report.get("status")=="passed" and report.get("candidateManifestSha256")==actual["candidateManifestSha256"]
            and report.get("canonicalPackages")==actual["canonicalPackages"],"Registry evidence mismatch")
    require(report.get("realRegistryTested") is False and report.get("registryPublished") is False
            and report.get("signed") is False and report.get("licenseReview")=="pending","Unexpected registry approval claim")
    labels=report["checks"]
    require(len(labels)==len(set(labels))==len(expected_labels) and set(labels)==expected_labels,
            "Missing, duplicate or unexpected registry control")
    require(report["requestCounts"]["writesDenied"]==6,"Missing registry write denial evidence")

def registry_labels(packages,public_names):
    expected=set()
    for filename in packages:
        for suffix in (" anonymous denied"," wrong credential denied"," authenticated raw bytes"," overwrite denied"," deletion denied"):
            expected.add(filename+suffix)
    expected.update(("unknown private package rejected /npm/@taktera/unknown",
        "unknown private package rejected /flat/taktera.unknown/index.json",
        "anonymous npm metadata denied","anonymous NuGet index denied","pinned Node","pinned npm","pinned .NET",
        "npm CLI fetched exact @taktera/ui-core","npm CLI fetched exact @taktera/ui-react",
        "NuGet CLI restored exact canonical archive","NuGet private source identity","fixture has no write implementation"))
    expected.update("NuGet public mapping "+name for name in public_names)
    return expected

def check_wheel(status,observed,committed,actual,committed_hash,requirements):
    check_identity(status,actual)
    require(status.get("status")=="passed" and status.get("lockState")=="committed-match"
            and status.get("wheelCount")==len(committed["wheels"])==6,"Validator wheels not committed")
    require(observed==committed and status.get("lockSha256")==committed_hash,"Validator lock evidence mismatch")
    expected="".join(n+"=="+v["version"]+" --hash=sha256:"+v["sha256"]+"\n" for n,v in sorted(committed["wheels"].items()))
    require(requirements==expected,"Validator hash requirements mismatch")

def plan(policy,actual,requested):
    # This preflight has deliberately no executable publish mode or override.
    require(requested=="plan-only","Publication disabled in candidate workflow")
    require(policy["mode"]=="unconfigured" and policy["provider"] is None
            and policy["ownerApproved"] is False and policy["publicationEnabled"] is False
            and policy["npm"]["registry"] is None and policy["nuget"]["registry"] is None
            and policy["npm"]["retainPrivateFlag"] is True,"Unexpected registry activation")
    require(actual["signed"] is False and actual["registryPublished"] is False
            and actual["licenseReview"]=="pending","Unexpected candidate release approval")
    return {"status":"preflight-passed","publicationAllowed":False,"mode":"plan-only",
            "blockers":BLOCKERS,"sourceCommit":actual["sourceCommit"],
            "githubRunId":actual["githubRunId"],"githubRunAttempt":actual["githubRunAttempt"],
            "canonicalPackages":actual["canonicalPackages"],
            "candidateManifestSha256":actual["candidateManifestSha256"],
            "registryPublished":False,"signed":False,"licenseReview":"pending"}

def controls(policy,actual,registry,labels,status,observed,committed,committed_hash,requirements):
    checks=[]
    def rejected(label,fn):
        try: fn()
        except ValueError:
            checks.append(label)
            print(label+": rejected")
        else: raise ValueError("Negative release control accepted: "+label)
    rejected("publish requested",lambda:plan(policy,actual,"publish"))
    p=copy.deepcopy(policy);p["publicationEnabled"]=True
    rejected("publication override",lambda:plan(p,actual,"plan-only"))
    p=copy.deepcopy(policy);p["ownerApproved"]=True
    rejected("unverified owner approval",lambda:plan(p,actual,"plan-only"))
    p=copy.deepcopy(policy);p["npm"]["registry"]="https://registry.example/"
    rejected("unapproved registry destination",lambda:plan(p,actual,"plan-only"))
    r=copy.deepcopy(registry);r["githubRunId"]="0"
    rejected("wrong registry run",lambda:check_registry(r,actual,labels))
    r=copy.deepcopy(registry);r["githubRunAttempt"]="0"
    rejected("wrong registry attempt",lambda:check_registry(r,actual,labels))
    r=copy.deepcopy(registry);r["checks"].pop()
    rejected("missing registry check",lambda:check_registry(r,actual,labels))
    r=copy.deepcopy(registry);r["canonicalPackages"][next(iter(r["canonicalPackages"]))]="0"*64
    rejected("registry package mismatch",lambda:check_registry(r,actual,labels))
    s=copy.deepcopy(status);s["lockState"]="observed-not-committed"
    rejected("uncommitted validator lock",lambda:check_wheel(s,observed,committed,actual,committed_hash,requirements))
    o=copy.deepcopy(observed);o["wheels"][next(iter(o["wheels"]))]["sha256"]="0"*64
    rejected("modified wheel hash",lambda:check_wheel(status,o,committed,actual,committed_hash,requirements))
    rejected("modified requirements",lambda:check_wheel(status,observed,committed,actual,committed_hash,requirements+"\n"))
    return checks

def main(candidate,canonical,verification,registry_dir,wheel_dir,out):
    source=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
    require(source==os.environ["GITHUB_SHA"],"Unexpected checkout")
    actual=verify(candidate,canonical,source,os.environ["GITHUB_RUN_ID"],os.environ["GITHUB_RUN_ATTEMPT"])
    prepare(candidate,canonical,verification)
    registry=read(registry_dir/"registry-fixture-report.json")
    labels=registry_labels(actual["canonicalPackages"],read(canonical/"packages.lock.json")["dependencies"]["net10.0"])
    check_registry(registry,actual,labels)
    lock=ROOT/"30_distribution/security/validator-wheels.lock.json"
    committed=read(lock);observed=read(wheel_dir/"validator-wheels.lock.json");status=read(wheel_dir/"status.json")
    requirements=(wheel_dir/"requirements.sha256.txt").read_text(encoding="utf-8")
    check_wheel(status,observed,committed,actual,sha(lock.read_bytes()),requirements)
    policy=read(ROOT/"30_distribution/registry/policy.json")
    result=plan(policy,actual,"plan-only")
    result["evidenceHashes"]={
        "candidateVerification":sha((verification/"candidate-verification.json").read_bytes()),
        "attestationSubjects":sha((verification/"attestation-subjects.json").read_bytes()),
        "registryFixture":sha((registry_dir/"registry-fixture-report.json").read_bytes()),
        "validatorWheelLock":sha(lock.read_bytes()),
        "validatorWheelStatus":sha((wheel_dir/"status.json").read_bytes())}
    result["negativeControls"]=controls(policy,actual,registry,labels,status,observed,committed,sha(lock.read_bytes()),requirements)
    out.mkdir(parents=True,exist_ok=False)
    (out/"release-preflight.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"releasePreflight":result},sort_keys=True))

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("candidate","canonical","verification","registry","wheels","output"): p.add_argument(name,type=Path)
    a=p.parse_args()
    main(a.candidate,a.canonical,a.verification,a.registry,a.wheels,a.output)
