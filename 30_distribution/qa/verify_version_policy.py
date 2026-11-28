#!/usr/bin/env python3
"""Version and archive API policy preflight. No version edits or publication."""
import argparse
import copy
import json
import os
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from product_sbom import archive_files
from verify_candidate_download import verify, require, read, sha, safe_path
from verify_rollback_rehearsal import validate_historical

ROOT=Path(__file__).resolve().parents[2]
SEMVER=re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?")
NPM_FIELDS=("name","type","exports","types","peerDependencies","peerDependenciesMeta","dependencies","optionalDependencies","engines","sideEffects")

def version(value):
    match=SEMVER.fullmatch(value)
    require(match is not None,"Invalid SemVer: "+value)
    major,minor,patch,pre,build=match.groups()
    parts=pre.split(".") if pre else []
    require(not any(p.isdigit() and len(p)>1 and p[0]=="0" for p in parts),"Leading zero in prerelease")
    return int(major),int(minor),int(patch),parts,build

def precedence(left,right):
    a,b=version(left),version(right)
    if a[:3]!=b[:3]: return (a[:3]>b[:3])-(a[:3]<b[:3])
    x,y=a[3],b[3]
    if not x or not y: return (not x)-(not y)
    for p,q in zip(x,y):
        if p==q: continue
        if p.isdigit() and q.isdigit(): return (int(p)>int(q))-(int(p)<int(q))
        if p.isdigit()!=q.isdigit(): return -1 if p.isdigit() else 1
        return (p>q)-(p<q)
    return (len(x)>len(y))-(len(x)<len(y))

def promotion(versions,target,policy):
    require(target in ("beta","rc","stable"),"Unknown promotion stage")
    require(set(versions)==set(policy["packageIds"]),"Incomplete release package set")
    expected=policy["targetVersions"][target]
    version(expected)
    require(all(v==expected for v in versions.values()),"Unaligned release version")
    for v in versions.values():
        require(version(v)[4] is None,"Build metadata cannot avoid immutable version conflicts")
    return expected

def immutable(existing,proposed):
    for key,value in proposed.items():
        if key in existing:
            require(existing[key]==value,"Immutable package identity collision: "+key)

def normalized(data):
    return sha(data.replace(b"\r\n",b"\n"))

def contract(path):
    files=archive_files(path)
    if path.suffix==".tgz":
        meta=json.loads(files["package/package.json"])
        key="npm:"+meta["name"]
        ver=meta["version"]
        require(meta.get("private") is True,"Expected unpublished npm candidate")
        declarations={n:normalized(data) for n,data in files.items() if n.endswith((".d.ts",".d.mts",".d.cts"))}
        require(declarations,"Missing public declaration files")
        return key,ver,{"metadata":{field:meta.get(field) for field in NPM_FIELDS},"declarations":declarations}
    names=[n for n in files if n.endswith(".nuspec")]
    require(len(names)==1,"Invalid native manifest")
    root=ET.fromstring(files[names[0]])
    for element in root.iter(): element.tag=element.tag.rsplit("}",1)[-1]
    m=root.find("metadata")
    key="nuget:"+m.findtext("id").lower()
    ver=m.findtext("version")
    docs=ET.fromstring(files["lib/net10.0/Taktera.UI.Avalonia.xml"])
    member_ids=[e.attrib["name"] for e in docs.findall("./members/member")]
    require(len(member_ids)==len(set(member_ids)),"Duplicate XML documentation member ID")
    deps=sorted((g.get("targetFramework",""),d.get("id","").lower(),d.get("version",""))
                for g in m.findall("./dependencies/group") for d in g.findall("dependency"))
    direct=sorted((d.get("id","").lower(),d.get("version","")) for d in m.findall("./dependencies/dependency"))
    return key,ver,{"documentedMemberIds":sorted(member_ids),"dependencyGroups":deps,"directDependencies":direct,
                    "assemblyName":docs.findtext("./assembly/name"),
                    "libraryPaths":sorted(n for n in files if n.startswith("lib/") and n.endswith(".dll"))}

def inventory(canonical,expected):
    packages={}
    for filename,digest in sorted(expected.items()):
        p=safe_path(canonical,filename)
        require(sha(p.read_bytes())==digest,"Package changed before version gate")
        key,ver,api=contract(p)
        version(ver)
        require(key not in packages,"Duplicate package identity")
        packages[key]={"version":ver,"filename":filename,"sha256":digest,"api":api}
    return packages

def compare(before,after):
    require(set(before)==set(after),"Package identity set changed")
    diffs={}
    for key in before:
        old,new=before[key]["api"],after[key]["api"]
        if old!=new:
            diffs[key]=sorted(field for field in old.keys()|new.keys() if old.get(field)!=new.get(field))
    return diffs

def controls(policy,previous,current):
    rejected=[]
    def deny(label,fn):
        try: fn()
        except ValueError: rejected.append(label)
        else: raise ValueError("Version policy control accepted: "+label)
    for v in ("04.0.0","4.0","4.0.0-beta.01","4.0.0-","4.0.0-beta..1"):
        deny("invalid SemVer "+v,lambda v=v:version(v))
    actual={k:v["version"] for k,v in current.items()}
    deny("mixed candidate versions cannot promote",lambda:promotion(actual,"beta",policy))
    good={k:policy["targetVersions"]["beta"] for k in policy["packageIds"]}
    require(promotion(good,"beta",policy)==policy["targetVersions"]["beta"],"Valid beta promotion rejected")
    require(precedence("4.0.0-beta.1","4.0.0-beta-readiness.3")<0,"Prerelease precedence warning lost")
    require(precedence("4.0.0-beta.2","4.0.0-beta.10")<0,"Numeric prerelease precedence")
    require(precedence("4.0.0-beta.1","4.0.0-rc.1")<0 and precedence("4.0.0-rc.1","4.0.0")<0,"Release stage order")
    require(precedence("4.0.0+one","4.0.0+two")==0,"Build metadata must not affect precedence")
    bad=dict(good);bad.pop(next(iter(bad)))
    deny("incomplete promotion",lambda:promotion(bad,"beta",policy))
    bad=dict(good);bad[next(iter(bad))]+="+build.2"
    deny("metadata version workaround",lambda:promotion(bad,"beta",policy))
    deny("unknown promotion stage",lambda:promotion(good,"nightly",policy))
    old={"nuget:taktera.ui.avalonia@4.0.0-beta.1":"a"*64}
    immutable(old,dict(old))
    deny("published version byte replacement",lambda:immutable(old,{next(iter(old)):"b"*64}))
    require(compare(previous,current)=={},"Archive API surface changed; review and approve new baseline explicitly")
    bad=copy.deepcopy(current);key=next(iter(bad));bad[key]["api"]["syntheticChange"]=True
    require(key in compare(previous,bad),"API change detection failed")
    return rejected

def main(candidate,canonical,historical,historical_canonical,preflight,out):
    source=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
    require(source==os.environ["GITHUB_SHA"],"Unexpected checkout")
    current=verify(candidate,canonical,source,os.environ["GITHUB_RUN_ID"],os.environ["GITHUB_RUN_ATTEMPT"])
    plan=read(preflight/"release-preflight.json")
    require(plan["status"]=="preflight-passed" and plan["publicationAllowed"] is False and
            all(plan[k]==current[k] for k in ("sourceCommit","githubRunId","githubRunAttempt","canonicalPackages","candidateManifestSha256")),"Release plan mismatch")
    baseline=read(ROOT/"30_distribution/recovery/historical-candidate.json")
    old=validate_historical(historical,historical_canonical,baseline)
    before=inventory(historical_canonical,old["canonicalPackages"])
    after=inventory(canonical,current["canonicalPackages"])
    policy=read(ROOT/"30_distribution/versioning/policy.json")
    require(policy["publicationEnabled"] is False and policy["status"]=="proposal-awaiting-owner-approval","Unexpected promotion authorization")
    require({k:v["version"] for k,v in after.items()}==policy["packageIds"],"Current candidate identity differs from policy")
    collisions=[k+"@"+v["version"] for k,v in after.items() if k in before and v["version"]==before[k]["version"] and v["sha256"]!=before[k]["sha256"]]
    diffs=compare(before,after)
    require(not diffs,"Archive API surface changed: "+str(diffs))
    negative=controls(policy,before,after)
    report={"status":"passed","scope":"unsigned version and archive API policy preflight","sourceCommit":source,
            "githubRunId":current["githubRunId"],"githubRunAttempt":current["githubRunAttempt"],
            "candidateManifestSha256":current["candidateManifestSha256"],"historicalSourceCommit":old["sourceCommit"],
            "canonicalPackages":current["canonicalPackages"],"versions":{k:v["version"] for k,v in after.items()},
            "apiContracts":{k:v["api"] for k,v in after.items()},"apiDifferences":diffs,
            "sameVersionDifferentBytes":collisions,"negativeControls":negative,
            "promotionAllowed":False,"publicationAllowed":False,"signed":False,
            "versionPrecedenceWarning":"4.0.0-beta.1 sorts below 4.0.0-beta-readiness.3; first publication only, not an upgrade from that version.",
            "limitations":["Native XML member IDs and dependencies are not complete CLR ABI or behavioral compatibility.",
                           "Strict npm declaration equality does not establish semantic compatibility.",
                           "Historical candidate is not an approved published baseline.",
                           "Target release versions are a proposal, not an actual version change."]}
    out.mkdir(parents=True,exist_ok=False)
    (out/"version-policy.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"versionPolicy":{"status":"passed","packageCount":len(after),"negativeControls":len(negative),
                     "apiDifferences":diffs,"sameVersionDifferentBytes":collisions,
                     "promotionAllowed":False}},sort_keys=True))

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("candidate","canonical","historical","historical_canonical","preflight","output"):p.add_argument(name,type=Path)
    a=p.parse_args()
    main(a.candidate,a.canonical,a.historical,a.historical_canonical,a.preflight,a.output)
