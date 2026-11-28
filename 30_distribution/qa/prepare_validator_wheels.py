#!/usr/bin/env python3
"""Fetch exact committed binary wheels and verify both pinned and registry hashes."""
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen

VERSIONS={"jsonschema":"4.25.1","attrs":"25.3.0","jsonschema-specifications":"2025.4.1",
          "referencing":"0.36.2","rpds-py":"0.27.1","typing-extensions":"4.15.0"}
ROOT=Path(__file__).resolve().parents[2]
COMMITTED=ROOT/"30_distribution/security/validator-wheels.lock.json"

def require(ok,message):
    if not ok: raise ValueError(message)

def main(wheels,out):
    require(sys.version_info[:2]==(3,12) and sys.platform=="linux" and platform.machine()=="x86_64","Expected Linux x86_64 Python 3.12 validator host")
    require(COMMITTED.is_file(),"Committed validator wheel lock required")
    pinned=json.loads(COMMITTED.read_text())
    require(set(pinned)=={"schemaVersion","platform","python","wheels"} and pinned["schemaVersion"]==1 and pinned["platform"]=="linux" and pinned["python"]=="3.12","Unexpected wheel lock format")
    require(set(pinned["wheels"])==set(VERSIONS),"Unexpected committed wheel set")
    wheels.mkdir(parents=True,exist_ok=False)
    out.mkdir(parents=True,exist_ok=False)
    for name,version in sorted(VERSIONS.items()):
        item=pinned["wheels"][name]
        filename=item["filename"]
        url=item["url"]
        u=urlsplit(url)
        require(item["version"]==version and re.fullmatch(r"[A-Za-z0-9_.-]+\.whl",filename) is not None
                and re.fullmatch(r"[0-9a-f]{64}",item["sha256"]) is not None
                and u.scheme=="https" and u.netloc=="files.pythonhosted.org" and not u.query and not u.fragment
                and u.path.endswith("/"+filename),"Invalid committed wheel: "+name)
        with urlopen(url,timeout=60) as response:
            require(response.geturl()==url,"Unexpected wheel redirect")
            data=response.read(32_000_001)
        require(len(data)<=32_000_000 and hashlib.sha256(data).hexdigest()==item["sha256"],
                "Committed wheel checksum mismatch: "+name)
        require(not (wheels/filename).exists(),"Duplicate wheel filename")
        (wheels/filename).write_bytes(data)
    files={p.name:p for p in wheels.iterdir()}
    require(len(files)==len(VERSIONS) and all(p.is_file() and p.suffix==".whl" for p in files.values()),"Unexpected wheel set")
    records={}
    used=set()
    for name,version in sorted(VERSIONS.items()):
        url="https://pypi.org/pypi/"+name+"/"+version+"/json"
        with urlopen(url,timeout=60) as response:
            require(urlsplit(response.geturl()).netloc=="pypi.org","Unexpected metadata redirect")
            data=response.read(8_000_001)
        require(len(data)<=8_000_000,"Oversized PyPI metadata")
        metadata=json.loads(data)
        require(metadata["info"]["version"]==version,"PyPI version mismatch")
        matches=[f for f in metadata["urls"] if f["filename"] in files and f["packagetype"]=="bdist_wheel"]
        require(len(matches)==1,"Ambiguous wheel resolution: "+name)
        entry=matches[0]
        filename=entry["filename"]
        u=urlsplit(entry["url"])
        require(u.scheme=="https" and u.netloc=="files.pythonhosted.org" and not u.query and not u.fragment,
                "Unexpected wheel host")
        digest=hashlib.sha256(files[filename].read_bytes()).hexdigest()
        require(digest==entry["digests"]["sha256"] and not entry.get("yanked",False),"Wheel hash/yank mismatch")
        require(filename not in used,"Duplicate wheel")
        used.add(filename)
        records[name]={"version":version,"filename":filename,"sha256":digest,"url":entry["url"]}
    require(used==set(files),"Unverified wheel")
    lock={"schemaVersion":1,"platform":"linux","python":"3.12","wheels":records}
    payload=json.dumps(lock,indent=2,sort_keys=True)+"\n"
    require(pinned==lock,"Committed validator wheel lock changed")
    state="committed-match"
    (out/"validator-wheels.lock.json").write_text(payload,encoding="utf-8")
    (out/"requirements.sha256.txt").write_text("".join(n+"=="+v["version"]+" --hash=sha256:"+v["sha256"]+"\n" for n,v in sorted(records.items())),encoding="utf-8")
    (out/"status.json").write_text(json.dumps({"status":"passed","lockState":state,"wheelCount":len(records),
        "sourceCommit":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
        "githubRunId":os.environ["GITHUB_RUN_ID"],"githubRunAttempt":os.environ["GITHUB_RUN_ATTEMPT"],
        "lockSha256":hashlib.sha256(COMMITTED.read_bytes()).hexdigest()},indent=2)+"\n")
    print("TAKTERA_VALIDATOR_WHEEL_LOCK_BEGIN")
    print(payload,end="")
    print("TAKTERA_VALIDATOR_WHEEL_LOCK_END")
    print(json.dumps({"validatorWheelEvidence":{"lockState":state,"wheelCount":len(records)}},sort_keys=True))
if __name__=="__main__":
    if len(sys.argv)!=3: raise SystemExit("usage: prepare_validator_wheels.py wheelhouse output")
    main(Path(sys.argv[1]),Path(sys.argv[2]))
