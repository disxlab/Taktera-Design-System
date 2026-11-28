#!/usr/bin/env python3
"""Review evidence for shipped/inline assets and exact-version upstream licenses.

This audit never infers authorship or approves redistribution from a pattern match.
"""
import hashlib
import json
import re
from pathlib import Path
from urllib.request import urlopen
from product_sbom import archive_files

ROOT=Path(__file__).resolve().parents[2]
ASSET_EXTENSIONS={".ttf",".otf",".woff",".woff2",".eot",".svg",".png",".jpg",".jpeg",".gif",".webp",".ico",".avif",".bmp",".pdf"}
TEXT_EXTENSIONS={".css",".js",".mjs",".cjs",".jsx",".tsx",".ts",".json",".axaml",".xaml",".html",".md",".xml"}
PATTERNS={
    "font-face":re.compile(r"@font-face\b",re.I),
    "font-reference":re.compile(r"font-family\s*:[^;{}\n]{1,180}|FontFamily\s*=\s*['\"][^'\"]{1,180}['\"]|fontFamily\s*:\s*['\"][^'\"]{1,180}['\"]",re.I),
    "css-url":re.compile(r"url\s*\(\s*[^)\n]{1,240}\)",re.I),
    "data-uri":re.compile(r"data:(?:image|font|application/font)[^;,\s'\"]{0,100}",re.I),
    "inline-svg":re.compile(r"<svg\b|(?:jsx|jsxs|createElement)\s*\(\s*['\"]svg['\"]",re.I),
    "svg-path":re.compile(r"<path\b|(?:jsx|jsxs|createElement)\s*\(\s*['\"]path['\"]",re.I),
    "xaml-geometry":re.compile(r"<(?:Path|PathIcon|StreamGeometry|GeometryDrawing|DrawingImage|Image)\b|\b(?:Data|Geometry|Source|FontFamily)\s*=\s*['\"][^'\"]{1,120}['\"]",re.I),
    "asset-reference":re.compile(r"(?:avares://|resm:|https?://)[^\s\"'<>]{1,240}|[\w./-]+\.(?:woff2?|ttf|otf|svg|png|webp|jpe?g)\b",re.I),
    "attribution-marker":re.compile(r"\b(?:Lucide|Inter|JetBrains Mono|copyright|SPDX-License-Identifier|third.party|attribution)\b",re.I),
}
UPSTREAM={
    ("Avalonia.BuildServices","11.3.2"):("AvaloniaUI/Avalonia.BuildServices","777f975b0a0cecf0311273711d56697212c558c0","LICENSE","4a02b0b2ea96f3a8b9cb88af64a3c061c6ef4426"),
    ("MicroCom.Runtime","0.11.0"):("kekekeks/MicroCom","918f1a7d13193beda39b78d70a99ee4c7b188f8b","LICENSE","6bcf96f0b4029b873c3d9b55d4c1117bbd157e28"),
    ("Avalonia","11.3.22"):("AvaloniaUI/Avalonia","627ae9ef921621e27e7aa58df2796fbadb50af88","licence.md","41951805ac6a5cdb91373db7725fbaa9c004d912"),
    ("Avalonia.Remote.Protocol","11.3.22"):("AvaloniaUI/Avalonia","627ae9ef921621e27e7aa58df2796fbadb50af88","licence.md","41951805ac6a5cdb91373db7725fbaa9c004d912"),
}

def require(ok,message):
    if not ok:
        raise ValueError(message)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")

def scan(name,data,scope):
    suffix=Path(name).suffix.lower()
    result={"path":name,"scope":scope,"sha256":sha(data),"bytes":len(data),
            "binaryAssetExtension":suffix in ASSET_EXTENSIONS,"markers":{},"reviewStatus":"pending"}
    if suffix in TEXT_EXTENSIONS:
        text=data.decode("utf-8-sig",errors="replace")
        for key,pattern in PATTERNS.items():
            matches=list(pattern.finditer(text))
            if matches:
                result["markers"][key]={"count":len(matches),"examples":[
                    {"line":text.count("\n",0,m.start())+1,"match":m.group(0)[:200]} for m in matches[:10]]}
    return result

def pinned_blob(repo,commit,path,blob):
    url="https://raw.githubusercontent.com/"+repo+"/"+commit+"/"+path
    with urlopen(url,timeout=60) as response:
        data=response.read(2_000_001)
    require(len(data)<=2_000_000,"Oversized upstream evidence")
    actual=hashlib.sha1(b"blob "+str(len(data)).encode("ascii")+b"\0"+data).hexdigest()
    require(actual==blob,"Pinned upstream Git blob mismatch: "+url)
    return url,data

def upstream_license(out,record):
    key=(record["name"],record["version"])
    if key not in UPSTREAM:
        return None
    repo,commit,path,blob=UPSTREAM[key]
    url,data=pinned_blob(repo,commit,path,blob)
    dest=out/"licenses"/"upstream"/(sha(record["ref"].encode("utf-8"))[:20]+".txt")
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_bytes(data)
    metadata=record["metadata"].get("repository") or {}
    normalized=metadata.get("url","").lower().rstrip("/").removesuffix(".git")
    identity_match=normalized in ("https://github.com/"+repo.lower(),"http://github.com/"+repo.lower())
    commit_match=metadata.get("commit","").lower()==commit
    association="package-repository-and-commit-match" if identity_match and commit_match else "unconfirmed-package-source"
    version_evidence=None
    if key==("MicroCom.Runtime","0.11.0"):
        props_blob="29b9d47e15b0bfab6161871ed4ff8bca5e1053ff"
        props_url,props=pinned_blob(repo,commit,"Directory.Build.props",props_blob)
        import xml.etree.ElementTree as ET
        parsed=ET.fromstring(props)
        require(parsed.findtext(".//Version")==record["version"] and parsed.findtext(".//PackageLicenseExpression")=="MIT",
                "Historical MicroCom version evidence differs")
        evidence_path=dest.with_suffix(".props")
        evidence_path.write_bytes(props)
        version_evidence={"source":props_url,"gitBlobSha1":props_blob,"sha256":sha(props),
                          "file":evidence_path.relative_to(out).as_posix(),"declaredVersion":record["version"],
                          "licenseExpression":"MIT"}
        if identity_match and not metadata.get("commit"):
            association="repository-and-historical-version-match-only"
    require(identity_match,"Package repository differs from pinned upstream: "+record["ref"])
    if key!=("MicroCom.Runtime","0.11.0"):
        require(commit_match,"Package commit differs from pinned upstream: "+record["ref"])
    return {"ref":record["ref"],"repository":repo,"commit":commit,"source":url,"gitBlobSha1":blob,
            "sha256":sha(data),"file":dest.relative_to(out).as_posix(),
            "packageRepositoryMatches":identity_match,"packageCommitMatches":commit_match,
            "association":association,"versionEvidence":version_evidence,"reviewStatus":"pending",
            "note":"Historical source license evidence, not a grant or verification of binary-to-source provenance."}

def build(out,packages,source):
    inventory=read(out/"sbom/product-file-inventory.json")
    actual=[]
    for pkg in packages:
        path=out/pkg["file"]
        require(sha(path.read_bytes())==pkg["sha256"],"Archive changed before asset audit")
        for member,data in sorted(archive_files(path).items()):
            actual.append(scan(pkg["file"]+"!"+member,data,"shipped archive member"))
    expected={f["archive"]+"!"+f["member"]:f["sha256"] for f in inventory["files"]}
    require(len(actual)==len(expected) and {f["path"]:f["sha256"] for f in actual}==expected,
            "Asset audit and archive inventory differ")
    embedded=[]
    for entry in inventory["embeddedSourceResources"]:
        path=ROOT/entry["source"]
        data=path.read_bytes()
        require(sha(data)==entry["sha256"],"Embedded resource source changed")
        embedded.append(scan(entry["source"],data,"compiled XAML source"))
    license_evidence=read(out/"licenses/dependency-license-evidence.json")
    upstream=[]
    for record in license_evidence["components"]:
        if not record["texts"]:
            entry=upstream_license(out,record)
            if entry:
                upstream.append(entry)
    missing=[r["ref"] for r in license_evidence["components"] if not r["texts"] and not any(u["ref"]==r["ref"] for u in upstream)]
    flagged=[f for f in actual+embedded if f["binaryAssetExtension"] or f["markers"]]
    for item in flagged:
        print(json.dumps({"assetReviewMarker":{"path":item["path"],"sha256":item["sha256"],"markers":item["markers"],"binaryAssetExtension":item["binaryAssetExtension"]}},sort_keys=True))
    for item in upstream:
        print(json.dumps({"upstreamLicenseAssociation":{"ref":item["ref"],"association":item["association"],"commit":item["commit"],"sha256":item["sha256"]}},sort_keys=True))
    report={"source":source,"status":"pending","releaseApproval":False,
            "shippedArchiveMembers":actual,"embeddedXamlSources":embedded,
            "upstreamLicenseEvidence":upstream,"missingEmbeddedOrPinnedUpstreamText":missing,
            "limitations":["Pattern audit is not a complete asset provenance or legal review.",
                           "Compiled DLL contents are represented by verified XAML source evidence; no claim of exhaustive binary reverse engineering.",
                           "Font family references do not prove fonts are bundled.",
                           "Upstream license at an exact release commit is not automatic package attribution or approval."]}
    write(out/"licenses/asset-attribution-review.json",report)
    write(out/"licenses/upstream-license-evidence.json",{"status":"pending","releaseApproval":False,
            "sources":upstream,"missingEmbeddedOrPinnedUpstreamText":missing})
    draft=out/"licenses/THIRD-PARTY-NOTICES.draft.txt"
    with draft.open("a",encoding="utf-8") as f:
        f.write("\nPINNED UPSTREAM SOURCE EVIDENCE — REVIEW ONLY\n")
        for item in upstream:
            data=(out/item["file"]).read_bytes()
            require(sha(data)==item["sha256"],"Upstream evidence changed")
            f.write("\n"+item["ref"]+"\n"+item["source"]+"\nSHA-256: "+item["sha256"]+
                    "\nPackage source association: pending review\n"+data.decode("utf-8-sig",errors="replace")+"\n")
        f.write("\nAsset attribution review: licenses/asset-attribution-review.json\n")
    stats={"archiveMembers":len(actual),"embeddedSources":len(embedded),"markerFiles":len(flagged),
           "directAssetFiles":sum(f["binaryAssetExtension"] for f in actual),
           "pinnedUpstreamTexts":len(upstream),"stillMissingText":len(missing),
           "unconfirmedBinarySourceAssociations":sum(not u["packageCommitMatches"] for u in upstream),"review":"pending"}
    print(json.dumps({"assetAttribution":stats},sort_keys=True))
    return stats
