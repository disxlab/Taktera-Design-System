#!/usr/bin/env python3
"""Static policy checks for the repository's current block-style workflow subset.
Not a general YAML parser or an external branch protection control.
"""
import base64
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/"30_distribution/security/actions.lock.json"

def require(ok,message):
    if not ok:
        raise ValueError(message)

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def inspect_workflow(text,pins,trusted=False):
    lines=text.splitlines()
    action_count=0
    perms={}
    job=None
    in_jobs=False
    i=0
    while i<len(lines):
        line=lines[i]
        i+=1
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        require("\t" not in line,"Tabs in workflow")
        require(not re.search(r"\b(?:pull_request_target|workflow_run)\s*:",line),"Privileged/unreviewed event")
        require(not re.search(r"\bsecrets\s*(?:\.|\[|:)",line),"Secrets reference is forbidden in this workflow")
        require(not re.search(r"\bwrite-all\b|\bread-all\b",line),"Broad permission")
        if line=="jobs:":
            in_jobs=True
            continue
        if in_jobs:
            m=re.fullmatch(r"  ([a-z][a-z0-9-]*):",line)
            if m: job=m.group(1)
        if re.match(r"^\s*(?:-\s+)?permissions\s*:",line):
            require(line in ("permissions:","    permissions:"),"Only literal block permissions allowed")
            key="root" if line=="permissions:" else job
            require(key is not None and key not in perms,"Duplicate/unknown permission block")
            indent=2 if key=="root" else 6
            values={}
            while i<len(lines):
                row=lines[i]
                if not row.strip() or row.lstrip().startswith("#"):
                    i+=1
                    continue
                if len(row)-len(row.lstrip())<indent:
                    break
                m=re.fullmatch(r" {%d}([a-z][a-z-]*): (read|write|none)"%indent,row)
                require(m is not None,"Unsupported permissions syntax")
                require(m.group(1) not in values,"Duplicate permission")
                values[m.group(1)]=m.group(2)
                i+=1
            perms[key]=values
            continue
        m=re.fullmatch(r"\s*(?:-\s+)?uses:\s*(\S+)(?:\s+#.*)?",line)
        if m:
            action=m.group(1)
            if trusted and action=="./.github/workflows/taktera-beta-readiness.yml":
                require(job=="rebuild","Reusable workflow in wrong job")
                continue
            require("@" in action,"Unpinned or unreviewed action")
            name,sha=action.rsplit("@",1)
            require(name in pins and re.fullmatch("[0-9a-f]{40}",sha) is not None
                    and sha==pins[name]["sha"],"Action pin mismatch: "+action)
            if not trusted:
                require(name!="actions/attest","Signing action in active PR pipeline")
            action_count+=1
            if name=="actions/checkout":
                # checkout step must explicitly disable stored Git credentials.
                following=[]
                for row in lines[i:]:
                    if re.match(r"^\s*-\s+",row) or (row.strip() and len(row)-len(row.lstrip())<=6):
                        break
                    following.append(row)
                require(any(re.fullmatch(r"\s+persist-credentials: false",row) for row in following),
                        "Checkout persists credentials")
        elif re.match(r"^\s*(?:-\s+)?uses\s*:",line):
            raise ValueError("Unsupported uses syntax")
    require(perms.get("root")=={"contents":"read"},"Unexpected root permissions")
    for name,values in perms.items():
        if trusted:
            allowed={"root":{"contents":"read"},"rebuild":{"contents":"read","issues":"read","actions":"read"},
                     "attest":{"contents":"read","id-token":"write","attestations":"write"},
                     "verify-signature":{"contents":"read","attestations":"read"}}
            require(name in allowed and values==allowed[name],"Unexpected trusted permissions: "+str(name))
        else:
            allowed={"contents":"read","issues":"read"} if name=="board-sync" else ({"contents":"read","actions":"read"} if name=="rollback-rehearsal" else {"contents":"read"})
            require(values==allowed,"Unexpected PR permissions: "+str(name))
    if trusted:
        require(set(perms)=={"root","rebuild","attest","verify-signature"},"Incomplete trusted permission scope")
        require("    environment: taktera-provenance-approval" in lines,"Missing protected signing environment")
        require("pull_request:" not in text,"Trusted template cannot run on PR")
        for marker in ("github.ref == 'refs/heads/main'","inputs.approve_attestation == true",
                       "vars.TAKTERA_ATTESTATION_ENABLED == 'true'","github.event_name == 'workflow_dispatch'"):
            require(marker in text,"Missing trusted workflow guard: "+marker)
    require(action_count>0,"No actions inspected")
    return action_count

def inspect_npm_lock(lock):
    require(lock["lockfileVersion"]==3,"Unexpected npm lock format")
    count=0
    for name,item in lock["packages"].items():
        if not name:
            continue
        require(not item.get("link") and name.startswith("node_modules/"),"Unreviewed local/link dependency")
        identity=item.get("name") or name.rsplit("node_modules/",1)[-1]
        require(not identity.lower().startswith("@taktera/"),"Private package in public dependency lock")
        url=urlsplit(item.get("resolved",""))
        require(url.scheme=="https" and url.netloc=="registry.npmjs.org" and not url.query and not url.fragment
                and url.path.endswith(".tgz"),"Unexpected npm dependency source: "+name)
        integrity=item.get("integrity","")
        require(integrity.startswith("sha512-") and len(base64.b64decode(integrity[7:],validate=True))==64,
                "Missing npm SHA-512 integrity: "+name)
        count+=1
    require(count>0,"Empty npm dependency lock")
    return count

def inspect_nuget_lock(lock):
    require(set(lock["dependencies"])=={"net10.0"},"Unexpected native lock framework")
    entries=lock["dependencies"]["net10.0"]
    require(entries,"Empty native lock")
    for name,entry in entries.items():
        require(re.fullmatch(r"[A-Za-z0-9_.-]+",name) is not None and not name.lower().startswith("taktera"),
                "Private or invalid NuGet ID in public dependency set")
        require(entry["type"] in ("Direct","Transitive") and entry["resolved"]
                and len(base64.b64decode(entry["contentHash"],validate=True))==64,
                "Unresolved or unhashed NuGet dependency")
    return len(entries)

def main():
    pins=read(LOCK)["actions"]
    tracked=subprocess.check_output(["git","ls-files",".github/workflows"],cwd=ROOT,text=True).splitlines()
    active=[p for p in tracked if p.endswith((".yaml",".yml"))]
    require(active==[".github/workflows/taktera-beta-readiness.yml"],"Unreviewed active workflow set: "+str(active))
    count=sum(inspect_workflow((ROOT/p).read_text(),pins) for p in active)
    template=inspect_workflow((ROOT/"30_distribution/workflows/taktera-trusted-attestation.yml").read_text(),pins,True)
    npm=inspect_npm_lock(read(ROOT/"17_packages/react/package-lock.json"))
    nuget=inspect_nuget_lock(read(ROOT/"17_packages/avalonia/library/packages.lock.json"))
    policy=read(ROOT/"30_distribution/registry/policy.json")
    require(policy["mode"]=="unconfigured" and policy["provider"] is None
            and policy["publicationEnabled"] is False and policy["ownerApproved"] is False,
            "Unexpected registry activation")
    require(policy["npm"]["registry"] is None and policy["nuget"]["registry"] is None,"Registry configured without review")
    for package in ("web-core","react"):
        require(read(ROOT/("17_packages/"+package+"/package.json"))["private"] is True,"npm private flag removed")
    print(json.dumps({"supplyChainStatic":{"status":"passed","activeActionOccurrences":count,
                          "templateActionOccurrences":template,"pinnedActionIdentities":len(pins),
                          "npmLockedDependencies":npm,"nugetLockedDependencies":nuget,
                          "registryPublicationEnabled":False}},sort_keys=True))
if __name__=="__main__":
    main()
