#!/usr/bin/env python3
"""Prepare a run-bound canonical npm consumer; never pack source or publish."""
import argparse, json, os, shutil, subprocess, sys
from pathlib import Path
from verify_candidate_download import verify, require, read, sha, safe_path
ROOT=Path(__file__).resolve().parents[2]

def main(candidate,canonical,dossier_dir,out):
    source=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    require(source==os.environ["GITHUB_SHA"],"Unexpected checkout")
    actual=verify(candidate,canonical,source,os.environ["GITHUB_RUN_ID"],os.environ["GITHUB_RUN_ATTEMPT"])
    d=read(safe_path(dossier_dir,"release-dossier.json"))
    require(d["status"]=="draft-evidence-only" and d["ownerApproved"] is False and d["publicationAllowed"] is False and d["signed"] is False,"Unexpected release approval")
    require(all(d[k]==actual[k] for k in ("sourceCommit","githubRunId","githubRunAttempt","candidateManifestSha256")),"Dossier identity mismatch")
    require({v["filename"]:v["sha256"] for v in d["packages"].values()}==actual["canonicalPackages"],"Dossier package mismatch")
    out=out.resolve()
    require(not out.exists(),"Refusing existing consumer")
    subprocess.run([sys.executable,str(ROOT/"30_distribution/taktera.py"),"init","react","--packages",str(canonical.resolve()),"--output",str(out)],cwd=ROOT,check=True)
    inventory=read(out/"package-inventory.json")
    require({v["name"] for v in inventory}=={"@taktera/ui-core","@taktera/ui-react"} and len(inventory)==2,"Missing npm SDK")
    for item in inventory:
        p=safe_path(out,item["file"])
        require(sha(p.read_bytes())==item["sha256"]==actual["canonicalPackages"][p.name],"Vendor digest mismatch")
    web=out.with_name(out.name+"-web")
    require(not web.exists(),"Refusing existing standalone Web consumer")
    subprocess.run([sys.executable,str(ROOT/"30_distribution/taktera.py"),"init","web","--packages",str(canonical.resolve()),"--output",str(web)],cwd=ROOT,check=True)
    web_inventory=read(web/"package-inventory.json")
    require(len(web_inventory)==1 and web_inventory[0]["name"]=="@taktera/ui-core","Unexpected standalone dependencies")
    item=web_inventory[0]
    p=safe_path(web,item["file"])
    require(sha(p.read_bytes())==item["sha256"]==actual["canonicalPackages"][p.name],"Standalone Core archive mismatch")
    lock=safe_path(candidate,"evidence/npm/consumer-package-lock.json")
    shutil.copyfile(lock,out/"package-lock.json")
    report={"sourceCommit":source,"githubRunId":actual["githubRunId"],"githubRunAttempt":actual["githubRunAttempt"],
            "candidateManifestSha256":actual["candidateManifestSha256"],"dossierSha256":sha((dossier_dir/"release-dossier.json").read_bytes()),
            "canonicalPackages":actual["canonicalPackages"],"consumerLockSha256":sha(lock.read_bytes()),"publicationAllowed":False}
    (out/"acceptance-input.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for n in ("candidate","canonical","dossier","output"): p.add_argument(n,type=Path)
    a=p.parse_args()
    main(a.candidate,a.canonical,a.dossier,a.output)
