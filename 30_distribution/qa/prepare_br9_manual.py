#!/usr/bin/env python3
"""Generate a run-bound NOT RUN manual acceptance checklist; never grant approval."""
import argparse
import json
from pathlib import Path
from verify_candidate_download import read,require,sha,safe_path
PRODUCTS=("platform","clinic","beauty","spa","fitness","travel")
THEMES=("light","dark")
LANGUAGES=("ru","en")
NATIVE=("visible-launch","keyboard-focus","text-selection-controls","scaling-100-150-200-supported","screen-reader-names-roles-states","contrast-and-clipping")
BROWSER=("keyboard-focus","screen-reader-names-roles-states","zoom-200-and-reflow","localized-errors-and-status","download-and-scheduler","contrast-and-clipping")
SECURITY=("review-sbom-and-dependency-findings","review-host-data-boundary","review-release-permissions-and-provenance","review-license-attribution","review-rollback-and-registry-policy")
def cases():
    result=[]
    for os,at in (("windows","NVDA"),("macos","VoiceOver")):
        for p in PRODUCTS:
            for t in THEMES:
                for l in LANGUAGES:
                    for check in NATIVE:
                        result.append({"id":f"native/{os}/{p}/{t}/{l}/{check}","surface":"Avalonia desktop","assistiveTechnology":at})
    for browser,os,at in (("Chrome","windows","NVDA"),("Firefox","windows","NVDA"),("Safari","macos","VoiceOver")):
        for p in PRODUCTS:
            for t in THEMES:
                for l in LANGUAGES:
                    for check in BROWSER:
                        result.append({"id":f"browser/{browser}/{p}/{t}/{l}/{check}","surface":"Independent React and standalone Web host","os":os,"assistiveTechnology":at})
    for check in SECURITY:
        result.append({"id":"security/"+check,"surface":"Owner/reviewer"})
    result.append({"id":"performance/approve-measured-budgets","surface":"Owner/reviewer"})
    return result
def template(summary_path,output):
    s=read(summary_path)
    require(s["status"]=="automated-matrix-passed" and s["publicationAllowed"] is False,"Not an unsigned candidate summary")
    records=[{**c,"status":"NOT RUN","tester":"","date":"","environment":"","notes":"","evidence":[]} for c in cases()]
    result={"sourceCommit":s["sourceCommit"],"githubRunId":s["githubRunId"],"githubRunAttempt":s["githubRunAttempt"],
            "candidateManifestSha256":s["candidateManifestSha256"],"canonicalPackages":s["canonicalPackages"],
            "automatedSummarySha256":sha(summary_path.read_bytes()),"manualAcceptance":"pending","publicationAllowed":False,
            "records":records}
    output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"manualAcceptance":"pending","cases":len(records),"notRun":len(records),"publicationAllowed":False}))
def verify_manual(summary_path,record_path,evidence_root):
    s=read(summary_path);m=read(record_path)
    require(s["status"]=="automated-matrix-passed" and s["publicationAllowed"] is False,"Not an unsigned candidate summary")
    require(all(m[k]==s[k] for k in ("sourceCommit","githubRunId","githubRunAttempt","candidateManifestSha256","canonicalPackages")),"Manual candidate identity mismatch")
    require(m["automatedSummarySha256"]==sha(summary_path.read_bytes()) and m["publicationAllowed"] is False,"Manual summary mismatch")
    expected={c["id"]:c for c in cases()}
    records=m["records"];seen=set()
    for r in records:
        key=r["id"]
        require(key in expected and key not in seen,"Missing, duplicate or unknown manual case")
        seen.add(key)
        require(r["status"]=="PASS" and all(isinstance(r[k],str) and r[k].strip() for k in ("tester","date","environment","notes")),"Incomplete manual case: "+key)
        require(isinstance(r["evidence"],list) and r["evidence"],"Missing evidence: "+key)
        for e in r["evidence"]:
            p=safe_path(evidence_root,e["file"])
            require(sha(p.read_bytes())==e["sha256"],"Manual evidence digest mismatch: "+key)
    require(seen==set(expected),"Incomplete manual matrix")
    print(json.dumps({"manualEvidence":"structurally-complete-review-required","cases":len(seen),"publicationAllowed":False}))
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("summary",type=Path);p.add_argument("record",type=Path);p.add_argument("--evidence-root",type=Path)
    a=p.parse_args()
    if a.evidence_root:verify_manual(a.summary,a.record,a.evidence_root)
    else:template(a.summary,a.record)
