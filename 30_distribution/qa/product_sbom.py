#!/usr/bin/env python3
"""Product-scoped archive inventory and resolved dependency graph; not license approval."""
import base64
import datetime
import hashlib
import json
import re
import tarfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]

def require(ok, message):
    if not ok:
        raise ValueError(message)

def digest(data, algorithm="sha256"):
    return hashlib.new(algorithm, data).hexdigest()

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)+"\n", encoding="utf-8")

def safe_member(name):
    p = PurePosixPath(name)
    require(name and not name.startswith("/") and "\\" not in name
            and not any(v in ("", ".", "..") for v in name.split("/"))
            and not p.is_absolute(), "Unsafe archive entry: "+name)
    return name

def archive_files(path):
    files = {}
    def add(name, data):
        safe_member(name)
        require(name not in files, "Duplicate archive member: "+name)
        files[name] = data
    if path.suffix == ".tgz":
        with tarfile.open(path, "r:gz") as z:
            for member in z.getmembers():
                if member.isdir():
                    continue
                require(member.isfile(), "Non-regular tar member: "+member.name)
                add(member.name, z.extractfile(member).read())
    elif path.suffix == ".nupkg":
        with zipfile.ZipFile(path) as z:
            for item in z.infolist():
                if item.is_dir():
                    continue
                require((item.external_attr >> 16) & 0o170000 != 0o120000, "ZIP symlink")
                add(item.filename, z.read(item))
    else:
        raise ValueError("Unknown package format")
    require(files, "Empty package")
    return files

def integrity(value):
    if value.startswith("sha512-"):
        value = value[7:]
    raw = base64.b64decode(value, validate=True)
    require(len(raw) == 64, "Expected SHA-512 integrity")
    return raw.hex()

def package_ref(ecosystem, name, version):
    return "pkg:"+ecosystem+"/"+quote(name, safe="/")+"@"+quote(version, safe="")

def npm_resolve(packages, parent, name):
    # Node lookup starts in the requesting package, then each ancestor node_modules.
    path = parent
    while True:
        candidate = (path+"/" if path else "")+"node_modules/"+name
        if candidate in packages:
            return candidate
        if not path:
            raise ValueError("Unresolved npm dependency: "+parent+" -> "+name)
        if "/node_modules/" in path:
            path = path.rsplit("/node_modules/", 1)[0]
        else:
            path = ""

def npm_dependencies(meta):
    merged = {}
    for field in ("dependencies", "optionalDependencies", "peerDependencies"):
        for name, version in meta.get(field, {}).items():
            require(name not in merged or merged[name] == version, "Conflicting npm constraints")
            merged[name] = version
    return merged

def license_value(value):
    # Only an explicitly declared identifier, never a legal conclusion.
    return value if isinstance(value, str) and value in ("MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "MPL-2.0") else "NOASSERTION"

def build(out, packages, source, npm_lock, native_lock):
    require(npm_lock["lockfileVersion"] == 3, "Expected consumer npm lock v3")
    npm = npm_lock["packages"]
    nodes, edges, shipped, inventory = {}, set(), [], []
    def add(ref, name, version, ecosystem, scope, hashes, declared=None):
        item = {"ref":ref,"name":name,"version":version,"ecosystem":ecosystem,"scope":scope,
                "hashes":hashes,"declaredLicense":declared or "NOASSERTION"}
        if ref in nodes:
            require(nodes[ref]==item, "Conflicting component identity: "+ref)
        nodes[ref]=item
        return ref
    def link(parent, child, constraint, kind):
        edges.add((parent, child, constraint, kind))
    def visit_npm(parent, name, constraint, ancestor, kind):
        path = npm_resolve(npm, ancestor, name)
        item = npm[path]
        require(not item.get("link") and item.get("version") and item.get("integrity"), "Unresolved npm component")
        ref = package_ref("npm", item.get("name", name), item["version"])
        new = ref not in nodes
        add(ref,item.get("name",name),item["version"],"npm","reference-host dependency (not bundled)",
            {"SHA-512":integrity(item["integrity"])}, item.get("license"))
        link(parent, ref, constraint, kind)
        if new:
            for dep, requested in npm_dependencies(item).items():
                visit_npm(ref,dep,requested,path,"resolved host dependency")
    require(set(native_lock["dependencies"])=={"net10.0"}, "Unexpected native target framework")
    net = native_lock["dependencies"]["net10.0"]
    nuget_refs = {}
    for name, entry in sorted(net.items()):
        require(entry["type"] in ("Direct","Transitive") and entry["resolved"], "Unexpected NuGet lock entry")
        ref=package_ref("nuget",name,entry["resolved"])
        nuget_refs[name.lower()]=add(ref,name,entry["resolved"],"nuget",
            "resolved library restore dependency (may include build assets; not bundled)",
            {"SHA-512":integrity(entry["contentHash"])})
    for name, entry in net.items():
        for dep, requested in entry.get("dependencies",{}).items():
            require(dep.lower() in nuget_refs, "Missing NuGet transitive dependency")
            link(nuget_refs[name.lower()],nuget_refs[dep.lower()],requested,"library restore")
    for pkg in packages:
        path=out/pkg["file"]
        require(digest(path.read_bytes())==pkg["sha256"],"Product archive hash mismatch")
        files=archive_files(path)
        if path.suffix==".tgz":
            meta=json.loads(files["package/package.json"])
            name,version=meta["name"],meta["version"]
            require(name==pkg["name"] and version==pkg["version"],"npm identity mismatch")
            ref=add(package_ref("npm",name,version),name,version,"npm","shipped package",
                    {"SHA-256":pkg["sha256"]},meta.get("license"))
            require(not meta.get("bundledDependencies") and not meta.get("bundleDependencies"),"Unexpected bundled npm dependencies")
            require(not any("/node_modules/" in f for f in files),"Unexpected bundled node_modules")
            for dep, requested in npm_dependencies(meta).items():
                visit_npm(ref,dep,requested,"node_modules/"+name,
                          "peer" if dep in meta.get("peerDependencies",{}) else "runtime")
        else:
            names=[n for n in files if n.endswith(".nuspec")]
            require(len(names)==1,"Expected one NuGet manifest")
            meta=ET.fromstring(files[names[0]])
            ns={"n":meta.tag.split("}")[0].strip("{")} if "}" in meta.tag else {}
            def q(name): return "n:"+name if ns else name
            m=meta.find(q("metadata"),ns)
            name,version=m.findtext(q("id"),namespaces=ns),m.findtext(q("version"),namespaces=ns)
            require(name==pkg["name"],"NuGet identity mismatch")
            license_node=m.find(q("license"),ns)
            declared=license_node.text if license_node is not None and license_node.get("type")=="expression" else None
            ref=add(package_ref("nuget",name,version),name,version,"nuget","shipped package",{"SHA-256":pkg["sha256"]},declared)
            deps={d.get("id").lower():d.get("version") for d in m.iterfind(".//"+q("dependency"),ns)}
            direct={n.lower() for n,e in net.items() if e["type"]=="Direct"}
            require(set(deps)==direct,"NuGet manifest and lock direct dependencies differ")
            for dep, requested in deps.items():
                link(ref,nuget_refs[dep],requested,"library restore")
        shipped.append(ref)
        for name,data in sorted(files.items()):
            inventory.append({"package":ref,"archive":pkg["file"],"member":name,"size":len(data),
                              "sha256":digest(data),"sha1":digest(data,"sha1")})
    require(len(shipped)==3 and len(set(shipped))==3,"Expected three product packages")
    # Source-level embedded-resource evidence; these XAML files are compiled into the DLL,
    # not additional files in the product archive.
    sources=[ROOT/"17_packages/avalonia"/n for n in ("TkControls.axaml","TkFieldStyles.axaml")]
    sources+=sorted((ROOT/"27_beta_readiness_3/avalonia_compat").glob("Taktera.*.axaml"))
    require(len(sources)==14,"Unexpected compiled resource source set")
    assets=[{"source":p.relative_to(ROOT).as_posix(),"sha256":digest(p.read_bytes()),
             "compiledInto":"lib/net10.0/Taktera.UI.Avalonia.dll","licenseReview":"pending"} for p in sources]
    root="taktera:canonical-sdk:"+source
    by_package={r:[f for f in inventory if f["package"]==r] for r in shipped}
    def cdx_hashes(values):
        return [{"alg":k,"content":v} for k,v in sorted(values.items())]
    def cdx_file(f):
        return {"type":"file","name":f["member"],"bom-ref":"file:"+f["archive"]+"!"+f["member"],
                "hashes":cdx_hashes({"SHA-256":f["sha256"],"SHA-1":f["sha1"]})}
    components=[]
    for ref,n in sorted(nodes.items()):
        component={"type":"library","bom-ref":ref,"name":n["name"],"version":n["version"],
                   "purl":ref,"hashes":cdx_hashes(n["hashes"]),
                   "properties":[{"name":"taktera:scope","value":n["scope"]},
                                 {"name":"taktera:declaredLicense","value":n["declaredLicense"]}]}
        if n["ecosystem"]=="nuget" and n["scope"]!="shipped package":
            # NuGet contentHash is not necessarily a digest of the downloaded signed archive.
            component.pop("hashes")
            component["properties"].append({"name":"taktera:nugetContentHashSha512","value":n["hashes"]["SHA-512"]})
        if license_value(n["declaredLicense"])!="NOASSERTION":
            component["licenses"]=[{"license":{"id":license_value(n["declaredLicense"])}}]
        if ref in by_package:
            component["components"]=[cdx_file(f) for f in by_package[ref]]
        components.append(component)
    dependencies=[{"ref":root,"dependsOn":sorted(shipped)}]
    for ref in sorted(nodes):
        dependencies.append({"ref":ref,"dependsOn":sorted({b for a,b,_,_ in edges if a==ref})})
    cdx={"bomFormat":"CycloneDX","specVersion":"1.6","version":1,
         "metadata":{"component":{"type":"application","name":"Taktera Design System canonical SDK","bom-ref":root},
                     "properties":[{"name":"taktera:source","value":source},
                                   {"name":"taktera:licenseReview","value":"pending"},
                                   {"name":"taktera:dependencyScope","value":"resolved reference-host npm peer closure and NuGet library restore closure; not all allowed host versions"}]},
         "components":components,"dependencies":dependencies}
    ids={ref:"SPDXRef-Package-"+str(i+1) for i,ref in enumerate(sorted(nodes))}
    spdx_packages=[];spdx_files=[];relationships=[]
    for ref,n in sorted(nodes.items()):
        files=by_package.get(ref,[])
        p={"SPDXID":ids[ref],"name":n["name"],"versionInfo":n["version"],
           "downloadLocation":"NOASSERTION","filesAnalyzed":bool(files),
           "licenseConcluded":"NOASSERTION","licenseDeclared":license_value(n["declaredLicense"]),
           "copyrightText":"NOASSERTION","checksums":[{"algorithm":k.replace("-",""),"checksumValue":v} for k,v in sorted(n["hashes"].items())],
           "externalRefs":[{"referenceCategory":"PACKAGE-MANAGER","referenceType":"purl","referenceLocator":ref}],
           "comment":n["scope"]}
        if n["ecosystem"]=="nuget" and n["scope"]!="shipped package":
            p.pop("checksums")
            p["comment"]+="; NuGet lock contentHash SHA-512 (not raw archive hash): "+n["hashes"]["SHA-512"]
        if files:
            verification=digest("".join(sorted(f["sha1"] for f in files)).encode("ascii"),"sha1")
            p["packageVerificationCode"]={"packageVerificationCodeValue":verification}
            p["licenseInfoFromFiles"]=["NOASSERTION"]
            relationships.append({"spdxElementId":"SPDXRef-DOCUMENT","relationshipType":"DESCRIBES","relatedSpdxElement":ids[ref]})
        spdx_packages.append(p)
    for i,f in enumerate(inventory,1):
        fid="SPDXRef-File-"+str(i)
        spdx_files.append({"SPDXID":fid,"fileName":"./"+f["archive"]+"/"+f["member"],
                           "checksums":[{"algorithm":"SHA1","checksumValue":f["sha1"]},{"algorithm":"SHA256","checksumValue":f["sha256"]}],
                           "licenseConcluded":"NOASSERTION","licenseInfoInFiles":["NOASSERTION"],"copyrightText":"NOASSERTION"})
        relationships.append({"spdxElementId":ids[f["package"]],"relationshipType":"CONTAINS","relatedSpdxElement":fid})
    for a,b,requested,kind in sorted(edges):
        relationships.append({"spdxElementId":ids[a],"relationshipType":"DEPENDS_ON","relatedSpdxElement":ids[b],
                              "comment":kind+": "+requested})
    spdx={"spdxVersion":"SPDX-2.3","dataLicense":"CC0-1.0","SPDXID":"SPDXRef-DOCUMENT",
          "name":"Taktera Design System canonical SDK","documentNamespace":"https://github.com/disxlab/Taktera-Design-System/sbom/"+source,
          "creationInfo":{"created":datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),"creators":["Tool: Taktera-Product-Inventory-1"]},
          "packages":spdx_packages,"files":spdx_files,"relationships":relationships,
          "documentDescribes":[ids[r] for r in sorted(shipped)]}
    require(all(a in nodes and b in nodes for a,b,_,_ in edges),"Dangling dependency")
    require(len(spdx_files)==sum(len(v) for v in by_package.values())==len(inventory),"Incomplete file inventory")
    require(len({f["SPDXID"] for f in spdx_files}|set(ids.values()))==len(spdx_files)+len(ids),"Duplicate SPDX ID")
    external=[n for n in nodes.values() if n["scope"]!="shipped package"]
    review={"status":"pending","releaseApproval":False,"source":source,"components":sorted(nodes.values(),key=lambda n:n["ref"]),
            "unresolvedLicenseConclusions":sorted(nodes),"embeddedSourceResources":assets,
            "limitations":["Declared license metadata is not verified license text or redistribution approval.",
                           "External dependency closure describes tested npm peer versions and NuGet library restore; not every compatible deployment.",
                           "Compiled XAML source inventory is not a complete attribution analysis of embedded or inline assets."]}
    write(out/"sbom/product.cyclonedx.json",cdx)
    write(out/"sbom/product.spdx.json",spdx)
    write(out/"sbom/product-file-inventory.json",{"source":source,"files":inventory,"embeddedSourceResources":assets})
    write(out/"sbom/third-party-review.json",review)
    stats={"shippedPackages":len(shipped),"externalComponents":len(external),"archiveMembers":len(inventory),
           "embeddedXamlSources":len(assets),"dependencyEdges":len(edges),"licenseReview":"pending","schemaValidation":"pending"}
    write(out/"sbom/product-summary.json",stats)
    print(json.dumps({"productSBOM":stats},sort_keys=True))
    return stats
