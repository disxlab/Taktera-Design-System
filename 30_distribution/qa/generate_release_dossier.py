#!/usr/bin/env python3
"""Generate a run-bound draft release dossier; no release or publication."""
import argparse
import copy
import json
import os
import shutil
import subprocess
from pathlib import Path
from verify_candidate_download import verify, require, read, sha, safe_path
from verify_version_policy import inventory
from release_preflight import BLOCKERS, check_identity

ROOT=Path(__file__).resolve().parents[2]
ROLLBACK_NEG={"unknown snapshot","untrusted historical manifest","modified recovery archive","missing recovery archive","unexpected recovery file"}
ROLLBACK_CONSUMERS={"fresh-react-install","npm-lock-and-installed-bytes","react-typescript-build","react-ssr",
                    "fresh-avalonia-restore","nuget-archive-and-dll-bytes","historical-native-dependency-graph","avalonia-release-build"}
VERSION_NEG={"invalid SemVer "+v for v in ("04.0.0","4.0","4.0.0-beta.01","4.0.0-","4.0.0-beta..1")}
VERSION_NEG.update(("mixed candidate versions cannot promote","incomplete promotion","metadata version workaround","unknown promotion stage","published version byte replacement"))
PLAN_NEG={"publish requested","publication override","unverified owner approval","unapproved registry destination",
          "wrong registry run","wrong registry attempt","missing registry check","registry package mismatch",
          "uncommitted validator lock","modified wheel hash","modified requirements"}

def exact_controls(values,expected):
    require(len(values)==len(expected) and set(values)==expected,"Missing or duplicate evidence checks")

def validate_reports(actual,packages,plan,rollback,versions,baseline):
    for record in (plan,rollback,versions):
        check_identity(record,actual)
        require(record.get("publicationAllowed") is False,"Unexpected publication permission")
    require(plan["status"]=="preflight-passed" and plan["mode"]=="plan-only" and
            plan["canonicalPackages"]==actual["canonicalPackages"] and
            plan["candidateManifestSha256"]==actual["candidateManifestSha256"] and
            plan["signed"] is False and plan["licenseReview"]=="pending" and plan["registryPublished"] is False,
            "Release plan differs")
    exact_controls(plan["blockers"],set(BLOCKERS))
    exact_controls(plan["negativeControls"],PLAN_NEG)
    require(rollback["status"]=="passed" and rollback["currentPackages"]==actual["canonicalPackages"]
            and rollback["historicalPackages"]==baseline["canonicalPackages"]
            and rollback["historicalSourceCommit"]==baseline["sourceCommit"]
            and rollback["historicalRunId"]==baseline["githubRunId"]
            and rollback["productionRollbackTested"] is False and rollback["registryOverwriteAllowed"] is False,
            "Rollback evidence differs")
    exact_controls(rollback["negativeControls"],ROLLBACK_NEG)
    exact_controls(rollback["restoredConsumerChecks"],ROLLBACK_CONSUMERS)
    conflicts=sorted(n for n,d in actual["canonicalPackages"].items()
                     if n in baseline["canonicalPackages"] and baseline["canonicalPackages"][n]!=d)
    require(rollback["sameVersionDifferentBytes"]==conflicts,"Rollback collision mismatch")
    require(versions["status"]=="passed" and versions["canonicalPackages"]==actual["canonicalPackages"] and
            versions["candidateManifestSha256"]==actual["candidateManifestSha256"] and
            versions["historicalSourceCommit"]==baseline["sourceCommit"] and versions["apiDifferences"]=={} and
            versions["promotionAllowed"] is False and versions["signed"] is False,
            "Version evidence differs")
    require(versions["versions"]=={k:v["version"] for k,v in packages.items()} and
            versions["apiContracts"]=={k:v["api"] for k,v in packages.items()},"Version archive contracts differ")
    require(sorted(versions["sameVersionDifferentBytes"])==sorted(k+"@"+v["version"] for k,v in packages.items()
            if v["filename"] in conflicts),"Version collision mismatch")
    exact_controls(versions["negativeControls"],VERSION_NEG)

def negative_controls(actual,packages,plan,rollback,versions,baseline):
    labels=[]
    for label,which,key,value in (
        ("publication claim",0,"publicationAllowed",True),
        ("wrong source",0,"sourceCommit","0"*40),
        ("wrong run attempt",1,"githubRunAttempt","0"),
        ("production recovery claim",1,"productionRollbackTested",True),
        ("missing recovery control",1,"negativeControls",[]),
        ("promotion claim",2,"promotionAllowed",True),
        ("changed API evidence",2,"apiContracts",{})):
        records=copy.deepcopy([plan,rollback,versions])
        records[which][key]=value
        try: validate_reports(actual,packages,*records,baseline)
        except ValueError: labels.append(label);print(label+": rejected")
        else: raise ValueError("Invalid dossier accepted: "+label)
    return labels

def main(candidate,canonical,preflight,recovery,version_dir,out):
    source=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
    require(source==os.environ["GITHUB_SHA"],"Unexpected checkout")
    actual=verify(candidate,canonical,source,os.environ["GITHUB_RUN_ID"],os.environ["GITHUB_RUN_ATTEMPT"])
    packages=inventory(canonical,actual["canonicalPackages"])
    plan_path=safe_path(preflight,"release-preflight.json")
    rollback_path=safe_path(recovery,"rollback-rehearsal.json")
    version_path=safe_path(version_dir,"version-policy.json")
    plan,rollback,versions=map(read,(plan_path,rollback_path,version_path))
    baseline=read(ROOT/"30_distribution/recovery/historical-candidate.json")
    validate_reports(actual,packages,plan,rollback,versions,baseline)
    build=read(candidate/"build-evidence.json")
    require(build["manualAndStagingAcceptance"]=="pending","Unexpected manual acceptance claim")
    product=read(candidate/"sbom/product-summary.json")
    asset=read(candidate/"licenses/asset-attribution-review.json")
    licenses=read(candidate/"licenses/dependency-license-evidence.json")
    upstream=read(candidate/"licenses/upstream-license-evidence.json")
    require(product["schemaValidation"]=="passed" and product["licenseReview"]=="pending","Product review status differs")
    require(licenses["releaseApproval"] is False and upstream["releaseApproval"] is False and asset["releaseApproval"] is False,
            "Unexpected license approval")
    missing=upstream["missingEmbeddedOrPinnedUpstreamText"]
    require(not missing,"Missing license text evidence")
    negative=negative_controls(actual,packages,plan,rollback,versions,baseline)
    out.mkdir(parents=True,exist_ok=False)
    guide=ROOT/"30_distribution/docs/CANDIDATE_RELEASE_GUIDE.md"
    shutil.copyfile(guide,out/"CANDIDATE_RELEASE_GUIDE.md")
    report={"schemaVersion":1,"status":"draft-evidence-only","sourceCommit":source,"githubRunId":actual["githubRunId"],
            "githubRunAttempt":actual["githubRunAttempt"],"candidateManifestSha256":actual["candidateManifestSha256"],
            "packages":{k:{f:v[f] for f in ("version","filename","sha256")} for k,v in packages.items()},
            "productSummary":product,"verifiedFiles":actual["hashedFiles"],"schemaDocuments":actual["schemaDocuments"],
            "externalLicenseComponents":len(licenses["components"]),"missingLicenseTexts":missing,
            "unconfirmedSourceAssociations":[x["ref"] for x in upstream["sources"] if not x["packageCommitMatches"]],
            "rollbackDurationSeconds":rollback["elapsedSeconds"],"historicalRunId":rollback["historicalRunId"],
            "apiDifferences":versions["apiDifferences"],"versionPrecedenceWarning":versions["versionPrecedenceWarning"],
            "sameVersionDifferentBytes":versions["sameVersionDifferentBytes"],"blockers":plan["blockers"],
            "negativeControls":negative,"signed":False,"publicationAllowed":False,"registryPublished":False,
            "promotionAllowed":False,"productionRollbackTested":False,"ownerApproved":False,
            "licenseReview":"pending","manualAndStagingAcceptance":"pending","platformIntegration":"post-stable-only",
            "evidenceSha256":{"releasePreflight":sha(plan_path.read_bytes()),"rollback":sha(rollback_path.read_bytes()),
                             "versionPolicy":sha(version_path.read_bytes()),"guide":sha(guide.read_bytes())}}
    (out/"release-dossier.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    lines=["# Taktera Design System — Candidate release dossier","",
           "**DRAFT — NOT APPROVED FOR DISTRIBUTION.**","",
           "Source commit: "+source,"Run ID / attempt: "+actual["githubRunId"]+" / "+actual["githubRunAttempt"],
           "Candidate SHA256SUMS digest: "+actual["candidateManifestSha256"],"",
           "## Exact SDK package identities","","| SDK | Version | Archive SHA-256 |","|---|---|---|"]
    for k,v in sorted(packages.items()):
        lines.append("| "+k+" | "+v["version"]+" | "+v["sha256"]+" |")
    lines+=["","## Evidence","",f"- Verified candidate files: {actual['hashedFiles']}",
            f"- Schema-validated SBOMs: {actual['schemaDocuments']}",
            f"- External license components: {len(licenses['components'])}; legal review pending.",
            f"- Local historical recovery rehearsal: {rollback['elapsedSeconds']} seconds; not production RTO/RPO.",
            "- Archive API comparison: no differences in checked fields; not full ABI or behavioral proof.",
            "- "+versions["versionPrecedenceWarning"],"",
            "## Publication blockers",""]
    lines+=["- "+x for x in plan["blockers"]]
    lines+=["","No release approved. Taktera Platform integration only after Stable.",
            "See CANDIDATE_RELEASE_GUIDE.md and release-dossier.json for instructions and machine-readable evidence."]
    (out/"RELEASE_NOTES.draft.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    sums={p.name:sha(p.read_bytes()) for p in out.iterdir() if p.is_file()}
    (out/"SHA256SUMS.txt").write_text("".join(d+"  "+n+"\n" for n,d in sorted(sums.items())),encoding="utf-8")
    print(json.dumps({"releaseDocumentation":{"status":"draft-evidence-only","files":len(sums)+1,
                     "negativeControls":len(negative),"publicationAllowed":False,"ownerApproved":False}},sort_keys=True))

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("candidate","canonical","preflight","recovery","version_dir","output"):p.add_argument(name,type=Path)
    a=p.parse_args()
    main(a.candidate,a.canonical,a.preflight,a.recovery,a.version_dir,a.output)
