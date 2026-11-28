#!/usr/bin/env python3
"""Independent post-download candidate integrity gate; no signing or publication."""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path, PurePosixPath
from product_sbom import archive_files

def require(ok,message):
    if not ok:
        raise ValueError(message)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def safe_path(root,name):
    require(isinstance(name,str) and name and not name.startswith("/") and "\\" not in name
            and all(p not in ("",".","..") for p in name.split("/"))
            and not PurePosixPath(name).is_absolute(),"Unsafe evidence path")
    p=root/name
    require(p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(root.resolve()),"Missing or unsafe evidence file: "+name)
    return p

def verify(root,canonical,source,run_id,attempt):
    require(root.is_dir() and canonical.is_dir(),"Missing downloaded artifacts")
    require(not any(p.is_symlink() for p in root.rglob("*")),"Symlink in candidate")
    checksums={}
    for line in (root/"SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        m=re.fullmatch(r"([0-9a-f]{64})  (.+)",line)
        require(m is not None,"Malformed SHA256SUMS entry")
        digest,name=m.groups()
        require(name!="SHA256SUMS.txt" and name not in checksums,"Duplicate or recursive manifest entry")
        require(sha(safe_path(root,name).read_bytes())==digest,"Candidate checksum mismatch: "+name)
        checksums[name]=digest
    actual={p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}-{"SHA256SUMS.txt"}
    require(set(checksums)==actual,"Candidate contains missing or extra files")
    build=read(root/"build-evidence.json")
    require(build["sourceCommit"]==source and str(build["githubRunId"])==run_id
            and str(build["githubRunAttempt"])==attempt,"Candidate source/run identity mismatch")
    require(build["signed"] is False and build["registryPublished"] is False
            and build["licenseReview"]=="pending","Unexpected publication/approval claim")
    manifest=read(canonical/"canonical.json")
    require(manifest==read(root/"evidence/reproducibility/canonical.json")
            and manifest["source"]==source and manifest["cleanBuilds"]==4
            and manifest["independentRunnerJobs"]==2 and manifest["published"] is False,
            "Canonical manifest/source mismatch")
    lock=canonical/"packages.lock.json"
    require(sha(lock.read_bytes())==manifest["nugetLockSha256"]
            ==sha((root/"evidence/reproducibility/packages.lock.json").read_bytes()),"NuGet lock evidence mismatch")
    require(len(build["packages"])==3,"Expected three packages")
    packages={}
    members={}
    for pkg in build["packages"]:
        p=safe_path(root,pkg["file"])
        require(p.name not in packages,"Duplicate package filename")
        digest=sha(p.read_bytes())
        require(digest==pkg["sha256"]==manifest["packages"][p.name]
                ==sha(safe_path(canonical,p.name).read_bytes()),"Canonical package bytes mismatch")
        packages[p.name]=digest
        for member,data in archive_files(p).items():
            members[(pkg["file"],member)]={"sha256":sha(data),"size":len(data)}
    require(packages==manifest["packages"],"Canonical package set mismatch")
    inventory=read(root/"sbom/product-file-inventory.json")
    listed={(f["archive"],f["member"]):{"sha256":f["sha256"],"size":f["size"]} for f in inventory["files"]}
    require(inventory["source"]==source and len(listed)==len(inventory["files"]) and listed==members,
            "Downloaded archive member inventory mismatch")
    schema=read(root/"sbom/schema-validation.json")
    expected={"npm-consumer.cdx.json","nuget-windows-consumer.cdx.json","nuget-macos-consumer.cdx.json",
              "product.cyclonedx.json","product.spdx.json"}
    require(schema["status"]=="passed" and set(schema["documents"])==expected,"Incomplete schema validation")
    for name,doc in schema["documents"].items():
        require(doc["status"]=="pass" and doc["sha256"]==checksums["sbom/"+name],"SBOM validation digest mismatch")
    attribution=read(root/"licenses/asset-attribution-review.json")
    require(attribution["source"]==source and attribution["releaseApproval"] is False,"Attribution source/approval mismatch")
    attr={(f["path"].split("!",1)[0],f["path"].split("!",1)[1]):{"sha256":f["sha256"],"size":f["bytes"]}
          for f in attribution["shippedArchiveMembers"]}
    require(len(attr)==len(attribution["shippedArchiveMembers"]) and attr==members,"Asset attribution inventory mismatch")
    review=read(root/"licenses/dependency-license-evidence.json")
    upstream=read(root/"licenses/upstream-license-evidence.json")
    require(review["releaseApproval"] is False and upstream["releaseApproval"] is False,"Unapproved license claim")
    license_files=[]
    for record in review["components"]:
        for text in record["texts"]:
            license_files.append(text)
    for item in upstream["sources"]:
        license_files.append(item)
        if item.get("versionEvidence"):
            license_files.append(item["versionEvidence"])
    for f in license_files:
        require(checksums[f["file"]]==f["sha256"],"License evidence digest mismatch")
    return {"status":"passed","sourceCommit":source,"githubRunId":run_id,"githubRunAttempt":attempt,
            "canonicalPackages":packages,"candidateManifestSha256":sha((root/"SHA256SUMS.txt").read_bytes()),
            "hashedFiles":len(checksums),"archiveMembers":len(members),"schemaDocuments":len(expected),
            "licenseEvidenceFiles":len(license_files),"signed":False,"registryPublished":False,
            "licenseReview":"pending","scope":"Independent same-run artifact download integrity, not signed provenance"}

def negative_controls(root,canonical,source,run_id,attempt):
    # Exercise the real downloaded candidate, never mutate its retained copy.
    with tempfile.TemporaryDirectory(prefix="taktera-candidate-negative-") as tmp:
        test=Path(tmp)/"candidate"
        shutil.copytree(root,test)
        def rejected(label,change,restore):
            change()
            try:
                verify(test,canonical,source,run_id,attempt)
            except ValueError as e:
                print(label+": rejected ("+str(e)+")")
            else:
                raise ValueError("Negative control unexpectedly passed: "+label)
            finally:
                restore()
        path=test/"sbom/product.spdx.json"
        original=path.read_bytes()
        rejected("tampered SBOM",lambda:path.write_bytes(original+b"\n"),lambda:path.write_bytes(original))
        rejected("missing SBOM",lambda:path.unlink(),lambda:path.write_bytes(original))
        extra=test/"unexpected.txt"
        rejected("extra file",lambda:extra.write_text("unexpected"),lambda:extra.unlink())
        manifest=test/"SHA256SUMS.txt"
        data=manifest.read_bytes()
        rejected("duplicate checksum",lambda:manifest.write_bytes(data+data.splitlines(keepends=True)[0]),lambda:manifest.write_bytes(data))
    return 4

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate",type=Path)
    parser.add_argument("canonical",type=Path)
    parser.add_argument("output",type=Path)
    args=parser.parse_args()
    source=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
    require(source==os.environ["GITHUB_SHA"],"Unexpected workflow checkout")
    run_id=os.environ["GITHUB_RUN_ID"]
    attempt=os.environ["GITHUB_RUN_ATTEMPT"]
    result=verify(args.candidate,args.canonical,source,run_id,attempt)
    result["negativeControls"]=negative_controls(args.candidate,args.canonical,source,run_id,attempt)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"independentCandidateVerification":result},sort_keys=True))
