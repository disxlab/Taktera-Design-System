#!/usr/bin/env python3
"""Derive a closed attestation subject set from independently verified same-run bytes."""
import argparse
import json
import os
import subprocess
from pathlib import Path
from verify_candidate_download import verify, require, sha, read, safe_path

def prepare(candidate, canonical, verification):
    source=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
    require(source==os.environ["GITHUB_SHA"],"Unexpected checkout")
    actual=verify(candidate,canonical,source,os.environ["GITHUB_RUN_ID"],os.environ["GITHUB_RUN_ATTEMPT"])
    report=verification/"candidate-verification.json"
    independent=read(report)
    require(independent==dict(actual,negativeControls=4),"Independent verification report differs")
    build=read(candidate/"build-evidence.json")
    names=[p["file"] for p in build["packages"]]+[
        "SHA256SUMS.txt","sbom/product.cyclonedx.json","sbom/product.spdx.json"]
    require(len(names)==len(set(names))==6,"Unexpected attestation subject count")
    files={str(safe_path(candidate,name)):sha(safe_path(candidate,name).read_bytes()) for name in names}
    files[str(report)]=sha(report.read_bytes())
    require(len(files)==7,"Unexpected subject set")
    manifest={"sourceCommit":source,"githubRunId":actual["githubRunId"],
              "githubRunAttempt":actual["githubRunAttempt"],"subjects":files,
              "candidateManifestSha256":actual["candidateManifestSha256"],
              "signed":False,"licenseReview":"pending","registryPublished":False}
    payload=json.dumps(manifest,indent=2,sort_keys=True)+"\n"
    output=verification/"attestation-subjects.json"
    if output.exists():
        require(output.read_text(encoding="utf-8")==payload,"Attestation subjects changed since independent verification")
    else:
        output.write_text(payload,encoding="utf-8")
    files[str(output)]=sha(output.read_bytes())
    checksums="".join(digest+"  "+name+"\n" for name,digest in sorted(files.items()))
    target=verification/"attestation-subjects.sha256"
    if target.exists():
        require(target.read_text(encoding="utf-8")==checksums,"Attestation checksum list changed")
    else:
        target.write_text(checksums,encoding="utf-8")
    print(json.dumps({"attestationPreflight":{"subjects":len(files),"sourceCommit":source,
                     "manifestSha256":sha(output.read_bytes()),"signed":False}},sort_keys=True))

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate",type=Path)
    parser.add_argument("canonical",type=Path)
    parser.add_argument("verification",type=Path)
    args=parser.parse_args()
    prepare(args.candidate,args.canonical,args.verification)
