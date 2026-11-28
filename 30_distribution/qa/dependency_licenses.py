#!/usr/bin/env python3
"""Capture original third-party license/notice evidence from exact dependency packages.

This is a review draft, never a redistribution approval or a claim of complete attribution.
"""
import base64
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit
from urllib.request import urlopen

ROOT=Path(__file__).resolve().parents[2]

def require(ok,message):
    if not ok:
        raise ValueError(message)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def text_path(name):
    lower=PurePosixPath(name).name.lower()
    return bool(re.match(r"^(license|licence|copying|copyright|notice|third[-_ ]?party)",lower)
                or any(p.lower() in ("licenses","licences") for p in PurePosixPath(name).parts[:-1]))

def read_nuspec(data):
    root=ET.fromstring(data)
    for element in root.iter():
        element.tag=element.tag.rsplit("}",1)[-1]
    meta=root.find("metadata")
    require(meta is not None,"Missing NuGet metadata")
    element=meta.find("license")
    repository=meta.find("repository")
    return {"name":meta.findtext("id"),"version":meta.findtext("version"),
            "licenseType":element.get("type") if element is not None else None,
            "license":element.text if element is not None else None,
            "licenseUrl":meta.findtext("licenseUrl"),"copyright":meta.findtext("copyright"),
            "repository":dict(repository.attrib) if repository is not None else None}

def capture(out, component, archive, metadata, entries, provenance):
    slug=sha(component["ref"].encode("utf-8"))[:20]
    dest=out/"licenses"/"evidence"/slug
    dest.mkdir(parents=True,exist_ok=False)
    files=[]
    for i,(name,data) in enumerate(sorted(entries),1):
        require(len(data)<=2_000_000,"Oversized license evidence: "+name)
        path=dest/("text-%03d.txt"%i)
        path.write_bytes(data)
        files.append({"sourceMember":name,"file":path.relative_to(out).as_posix(),"sha256":sha(data),"bytes":len(data)})
    return {"ref":component["ref"],"name":component["name"],"version":component["version"],
            "scope":component["scope"],"archiveSha256":sha(archive),"provenance":provenance,
            "metadata":metadata,"texts":files,
            "reviewStatus":"pending" if files else "missing-embedded-license-text"}

def npm_evidence(out, component, lock):
    candidates=[]
    for path,item in lock["packages"].items():
        if not path or not item.get("version"):
            continue
        name=item.get("name") or path.rsplit("node_modules/",1)[-1]
        if name==component["name"] and item["version"]==component["version"]:
            candidates.append(item)
    require(candidates,"Missing npm lock evidence")
    item=candidates[0]
    require(all(x.get("integrity")==item.get("integrity") and x.get("resolved")==item.get("resolved") for x in candidates),
            "Ambiguous npm dependency archive")
    url=item["resolved"]
    u=urlsplit(url)
    require(u.scheme=="https" and u.netloc=="registry.npmjs.org" and not u.query and not u.fragment,
            "Unexpected npm registry URL")
    with urlopen(url,timeout=60) as response:
        actual=urlsplit(response.geturl())
        require(actual.scheme=="https" and actual.netloc=="registry.npmjs.org","Unexpected npm redirect")
        archive=response.read(64_000_001)
    require(len(archive)<=64_000_000,"Oversized npm dependency")
    expected=component["hashes"]["SHA-512"]
    require(hashlib.sha512(archive).hexdigest()==expected,"npm integrity mismatch")
    files=[]
    with tarfile.open(fileobj=io.BytesIO(archive),mode="r:gz") as z:
        meta=json.load(z.extractfile("package/package.json"))
        require(meta["name"]==component["name"] and meta["version"]==component["version"],"npm metadata mismatch")
        for member in z.getmembers():
            if member.isfile() and text_path(member.name):
                require(member.size<=2_000_000,"Oversized npm license")
                files.append((member.name,z.extractfile(member).read()))
    return capture(out,component,archive,{"license":meta.get("license"),"author":meta.get("author")},
                   files,{"kind":"npm locked registry tarball","url":url,"sha512":expected})

def verify_nuget_hashes(archive, raw_sidecar, metadata, locked, sbom_hash, identity):
    """NuGet's raw archive hash and unsigned-content hash are distinct for signed packages."""
    raw=base64.b64decode(raw_sidecar,validate=True)
    require(len(raw)==64 and hashlib.sha512(archive).digest()==raw,
            "NuGet raw archive SHA-512 mismatch: "+identity)
    content=metadata.get("contentHash")
    require(isinstance(content,str) and content==locked,
            "NuGet locked content hash mismatch: "+identity)
    content_bytes=base64.b64decode(content,validate=True)
    require(len(content_bytes)==64 and content_bytes.hex()==sbom_hash,
            "NuGet SBOM content hash mismatch: "+identity)
    return {"contentHash":content,"rawArchiveSha512":raw.hex(),
            "contentHashMatchesRawArchive":content_bytes==raw}

def nuget_evidence(out, component, cache, lock):
    name,version=component["name"],component["version"]
    entry=lock["dependencies"]["net10.0"][name]
    require(entry["resolved"]==version,"Native lock version mismatch")
    folder=cache/name.lower()/version.lower()
    package=folder/(name.lower()+"."+version.lower()+".nupkg")
    sidecar=folder/(package.name+".sha512")
    raw_sidecar=sidecar.read_text(encoding="utf-8-sig").strip()
    metadata=json.loads((folder/".nupkg.metadata").read_text(encoding="utf-8-sig"))
    archive=package.read_bytes()
    hashes=verify_nuget_hashes(archive,raw_sidecar,metadata,entry["contentHash"],
                              component["hashes"]["SHA-512"],name+"/"+version)
    print(json.dumps({"nugetLicenseIntegrity":{"name":name,"version":version,**hashes}},sort_keys=True))
    files=[]
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        manifests=[n for n in z.namelist() if n.endswith(".nuspec")]
        require(len(manifests)==1,"Unexpected NuGet manifest count")
        meta=read_nuspec(z.read(manifests[0]))
        require(meta["name"].lower()==name.lower() and meta["version"]==version,"NuGet identity mismatch")
        declared=meta["license"] if meta["licenseType"]=="file" else None
        for member in z.infolist():
            if not member.is_dir() and (text_path(member.filename) or member.filename==declared):
                require(member.file_size<=2_000_000,"Oversized NuGet license")
                files.append((member.filename,z.read(member)))
    return capture(out,component,archive,meta,files,
                   {"kind":"locked NuGet restore cache",**hashes,
                    "note":"Lock-verified contentHash from .nupkg.metadata; raw archive SHA-512 independently matches .nupkg.sha512."})

def build(out,npm_lock,native_lock):
    review=json.loads((out/"sbom/third-party-review.json").read_text(encoding="utf-8"))
    external=[c for c in review["components"] if c["scope"]!="shipped package"]
    native=[c for c in external if c["ecosystem"]=="nuget"]
    records=[]
    with tempfile.TemporaryDirectory(prefix="taktera-license-") as tmp:
        work=Path(tmp)
        cache=work/"packages"
        project=work/"library"
        shutil.copytree(ROOT/"17_packages/avalonia/library",project,ignore=shutil.ignore_patterns("bin","obj","Assets"))
        shutil.copyfile(ROOT/"global.json",work/"global.json")
        cfg=work/"NuGet.Config"
        cfg.write_text('<?xml version="1.0" encoding="utf-8"?><configuration><packageSources><clear/><add key="nuget.org" value="https://api.nuget.org/v3/index.json"/></packageSources></configuration>',encoding="utf-8")
        env=dict(os.environ,NUGET_PACKAGES=str(cache),DOTNET_CLI_HOME=str(work/"dotnet-home"),
                 DOTNET_CLI_TELEMETRY_OPTOUT="1",AVALONIA_TELEMETRY_OPTOUT="1")
        require(subprocess.check_output(["dotnet","--version"],cwd=work,env=env,text=True).strip()=="10.0.404","Unexpected SDK")
        subprocess.run(["dotnet","restore",str(project/"Taktera.UI.Avalonia.csproj"),"--locked-mode",
                        "--configfile",str(cfg),"-p:NuGetAudit=true","-p:NuGetAuditMode=all",
                        "-warnaserror:NU1900,NU1903,NU1904,NU1905"],cwd=work,env=env,check=True)
        require(json.loads((project/"packages.lock.json").read_text(encoding="utf-8"))==native_lock,"License restore lock changed")
        for component in native:
            records.append(nuget_evidence(out,component,cache,native_lock))
        for component in external:
            if component["ecosystem"]=="npm":
                records.append(npm_evidence(out,component,npm_lock))
    require({r["ref"] for r in records}=={c["ref"] for c in external},"Missing external license evidence")
    records.sort(key=lambda r:r["ref"])
    for record in records:
        print(json.dumps({"licenseComponent":{"ref":record["ref"],"metadata":record["metadata"],"embeddedTexts":len(record["texts"])}},sort_keys=True))
    license_dir=out/"licenses"
    license_dir.mkdir(parents=True,exist_ok=True)
    report={"status":"pending","releaseApproval":False,"components":records,
            "unresolved":[r["ref"] for r in records if not r["texts"]],
            "limitations":["No license conclusion or redistribution authorization.",
                           "External dependency evidence only; SDK-owned, inline, font, icon and embedded asset attribution needs separate review.",
                           "Expression-only packages may require authoritative upstream license texts."]}
    (license_dir/"dependency-license-evidence.json").write_text(json.dumps(report,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    lines=["TAKTERA THIRD-PARTY NOTICES — REVIEW DRAFT","NOT APPROVED FOR REDISTRIBUTION","",
           "Evidence from exact resolved dependency packages. All license conclusions remain pending.",""]
    for record in records:
        lines.extend([record["name"]+" "+record["version"],"Scope: "+record["scope"],
                      "Metadata: "+json.dumps(record["metadata"],ensure_ascii=False,sort_keys=True),
                      "Review: "+record["reviewStatus"]])
        for f in record["texts"]:
            data=(out/f["file"]).read_bytes()
            require(sha(data)==f["sha256"],"License evidence changed")
            lines.extend(["Source: "+f["sourceMember"],"SHA-256: "+f["sha256"],
                          data.decode("utf-8-sig",errors="replace"),""])
        if not record["texts"]:
            lines.append("No embedded text found; authoritative source must be reviewed.")
        lines.append("")
    (license_dir/"THIRD-PARTY-NOTICES.draft.txt").write_text("\n".join(lines)+"\n",encoding="utf-8")
    stats={"components":len(records),"originalTexts":sum(len(r["texts"]) for r in records),
           "missingEmbeddedText":len(report["unresolved"]),"review":"pending"}
    print(json.dumps({"licenseEvidence":stats},sort_keys=True))
    return stats
