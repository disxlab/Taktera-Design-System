#!/usr/bin/env python3
"""Verify Sigstore bundles against the approved main commit and trusted workflow."""
import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path
from prepare_attestation_subjects import prepare
from verify_candidate_download import require

REPO="disxlab/Taktera-Design-System"
WORKFLOW=REPO+"/.github/workflows/taktera-trusted-attestation.yml"

def main(candidate,canonical,verification,bundle,out):
    require(os.environ["GITHUB_REPOSITORY"]==REPO and os.environ["GITHUB_REF"]=="refs/heads/main"
            and os.environ["GITHUB_EVENT_NAME"]=="workflow_dispatch","Not a trusted main dispatch")
    prepare(candidate,canonical,verification)
    require(bundle.is_file() and not bundle.is_symlink(),"Missing attestation bundle")
    base=["gh","attestation","verify","--repo",REPO,"--bundle",str(bundle),
          "--signer-workflow",WORKFLOW,"--source-ref","refs/heads/main",
          "--source-digest",os.environ["GITHUB_SHA"],"--signer-digest",os.environ["GITHUB_SHA"],
          "--deny-self-hosted-runners","--predicate-type","https://slsa.dev/provenance/v1","--format","json"]
    subjects=[line.split("  ",1)[1] for line in (verification/"attestation-subjects.sha256").read_text().splitlines()]
    require(len(subjects)==len(set(subjects))==8,"Unexpected signed subject count")
    out.mkdir(parents=True,exist_ok=False)
    for i,name in enumerate(subjects,1):
        result=subprocess.run(base+[name],check=True,capture_output=True,text=True)
        parsed=json.loads(result.stdout)
        require(isinstance(parsed,list) and parsed,"Missing verification result")
        (out/("subject-%02d.json"%i)).write_text(result.stdout,encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        bad=Path(tmp)/"tampered.txt"
        bad.write_bytes((candidate/"SHA256SUMS.txt").read_bytes()+b"\n")
        result=subprocess.run(base+[str(bad)],capture_output=True,text=True)
        require(result.returncode!=0,"Tampered subject signature unexpectedly passed")
    report={"status":"passed","verifiedSubjects":len(subjects),"negativeControls":1,
            "sourceCommit":os.environ["GITHUB_SHA"],"signerWorkflow":WORKFLOW,
            "predicateType":"https://slsa.dev/provenance/v1","registryPublished":False,
            "licenseReview":"pending"}
    (out/"signature-verification.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(report,sort_keys=True))

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("candidate","canonical","verification","bundle","output"):
        p.add_argument(name,type=Path)
    a=p.parse_args()
    main(a.candidate,a.canonical,a.verification,a.bundle,a.output)
