#!/usr/bin/env python3
"""Read-only loopback protocol fixture for canonical SDK transport. Never publish."""
import argparse
import base64
import hashlib
import hmac
import json
import os
import secrets
import shutil
import subprocess
import tempfile
import threading
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from verify_candidate_download import verify, require, read, sha, safe_path
from product_sbom import archive_files

ROOT=Path(__file__).resolve().parents[2]
PUBLIC_NPM="https://registry.npmjs.org/"
PUBLIC_NUGET="https://api.nuget.org/v3/index.json"

def npm_config(endpoint,token_variable):
    u=urlsplit(endpoint)
    require(u.scheme in ("http","https") and u.netloc and not u.username and not u.password
            and not u.query and not u.fragment and endpoint.endswith("/"),"Invalid npm endpoint")
    require(u.scheme=="https" or u.hostname=="127.0.0.1","HTTP is loopback-only")
    return ("registry="+PUBLIC_NPM+"\n@taktera:registry="+endpoint+"\n//"+u.netloc+u.path+
            ":_authToken="+chr(36)+"{"+token_variable+"}\nignore-scripts=true\n")

def nuget_config(endpoint,public_names,loopback=False):
    u=urlsplit(endpoint)
    require(u.scheme=="https" or (loopback and u.scheme=="http" and u.hostname=="127.0.0.1"),
            "Insecure NuGet source")
    require(u.netloc and not u.username and not u.password and not u.query and not u.fragment,"Invalid NuGet endpoint")
    root=ET.Element("configuration")
    sources=ET.SubElement(root,"packageSources")
    ET.SubElement(sources,"clear")
    attrs={"key":"TakteraPrivate","value":endpoint}
    if loopback: attrs["allowInsecureConnections"]="true"
    ET.SubElement(sources,"add",attrs)
    ET.SubElement(sources,"add",{"key":"nuget.org","value":PUBLIC_NUGET})
    mapping=ET.SubElement(root,"packageSourceMapping")
    ET.SubElement(mapping,"clear")
    private=ET.SubElement(mapping,"packageSource",{"key":"TakteraPrivate"})
    ET.SubElement(private,"package",{"pattern":"Taktera.UI.Avalonia"})
    public=ET.SubElement(mapping,"packageSource",{"key":"nuget.org"})
    for name in sorted(public_names):
        require(not name.lower().startswith("taktera.") and "*" not in name,"Unsafe public mapping")
        ET.SubElement(public,"package",{"pattern":name})
    audit=ET.SubElement(root,"auditSources")
    ET.SubElement(audit,"clear")
    ET.SubElement(audit,"add",{"key":"nuget.org","value":PUBLIC_NUGET})
    return ET.tostring(root,encoding="unicode")

def serve(packages):
    token=secrets.token_urlsafe(32)
    password=secrets.token_urlsafe(32)
    basic="Basic "+base64.b64encode(("fixture:"+password).encode()).decode()
    bearer="Bearer "+token
    stats={"authorized":0,"denied":0,"writesDenied":0,"unknownDenied":0}
    routes={}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def reply(self,code,data=b"",kind="application/json",challenge=False):
            self.send_response(code)
            if challenge: self.send_header("WWW-Authenticate",'Basic realm="Taktera loopback fixture"')
            self.send_header("Content-Type",kind)
            self.send_header("Content-Length",str(len(data)))
            self.end_headers()
            if self.command!="HEAD": self.wfile.write(data)
        def do_GET(self):
            path=unquote(urlsplit(self.path).path)
            is_npm=path.startswith("/npm/")
            expected=bearer if is_npm else basic
            if not hmac.compare_digest(self.headers.get("Authorization",""),expected):
                stats["denied"]+=1
                return self.reply(401,challenge=not is_npm)
            if path not in routes:
                stats["unknownDenied"]+=1
                return self.reply(404)
            stats["authorized"]+=1
            data,kind=routes[path]
            self.reply(200,data,kind)
        do_HEAD=do_GET
        def deny(self):
            stats["writesDenied"]+=1
            self.reply(405)
        do_PUT=do_POST=do_DELETE=do_PATCH=deny
    server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
    origin="http://127.0.0.1:"+str(server.server_port)
    def add_json(path,obj):
        routes[path]=(json.dumps(obj).encode(),"application/json")
    npm=[]
    native=None
    for path in packages:
        files=archive_files(path)
        data=path.read_bytes()
        if path.suffix==".tgz":
            meta=json.loads(files["package/package.json"])
            require(meta["name"] in ("@taktera/ui-core","@taktera/ui-react") and meta["private"] is True,
                    "Expected protected private npm package")
            name,version=meta["name"],meta["version"]
            route="/npm/"+name+"/-/"+path.name
            meta=dict(meta,dist={"tarball":origin+route,"shasum":hashlib.sha1(data).hexdigest(),
                      "integrity":"sha512-"+base64.b64encode(hashlib.sha512(data).digest()).decode()})
            add_json("/npm/"+name,{"name":name,"dist-tags":{"latest":version},"versions":{version:meta}})
            routes[route]=(data,"application/octet-stream")
            npm.append((name,version,path.name,route))
        else:
            manifests=[n for n in files if n.endswith(".nuspec")]
            require(len(manifests)==1,"Missing nuspec")
            nuspec=files[manifests[0]]
            xml=ET.fromstring(nuspec)
            for element in xml.iter(): element.tag=element.tag.rsplit("}",1)[-1]
            name=xml.findtext("metadata/id")
            version=xml.findtext("metadata/version")
            require(name=="Taktera.UI.Avalonia","Unexpected native identity")
            lower=name.lower(); ver=version.lower()
            prefix="/flat/"+lower+"/"+ver+"/"
            route=prefix+lower+"."+ver+".nupkg"
            add_json("/flat/"+lower+"/index.json",{"versions":[ver]})
            routes[route]=(data,"application/octet-stream")
            routes[prefix+lower+".nuspec"]=(nuspec,"application/xml")
            routes[route+".sha512"]=(base64.b64encode(hashlib.sha512(data).digest()),"text/plain")
            native=(name,version,path.name,route)
    require(len(npm)==2 and native is not None,"Unexpected SDK set")
    add_json("/nuget/v3/index.json",{"version":"3.0.0","resources":[{"@id":origin+"/flat/","@type":"PackageBaseAddress/3.0.0"}]})
    thread=threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    return server,thread,origin,token,password,bearer,basic,stats,npm,native

def request_status(url,auth=None,method="GET"):
    req=Request(url,headers={"Authorization":auth} if auth else {},method=method)
    try:
        with urlopen(req,timeout=20) as response: return response.status,response.read()
    except HTTPError as e: return e.code,e.read()

def run(args,work,env):
    # Never log environment or credentials; tool output is retained only on failures.
    result=subprocess.run(args,cwd=work,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if result.returncode:
        output=result.stdout
        for key in ("TAKTERA_FIXTURE_TOKEN","NuGetPackageSourceCredentials_TakteraPrivate"):
            if env.get(key): output=output.replace(env[key],"[redacted]")
        raise RuntimeError("Client failed: "+args[0]+" "+args[1]+"\n"+output[-5000:])
    return result.stdout.strip()

def main(candidate,canonical,out):
    source=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
    require(source==os.environ["GITHUB_SHA"],"Checkout differs")
    verified=verify(candidate,canonical,source,os.environ["GITHUB_RUN_ID"],os.environ["GITHUB_RUN_ATTEMPT"])
    build=read(candidate/"build-evidence.json")
    paths=[safe_path(candidate,p["file"]) for p in build["packages"]]
    expected={p.name:sha(p.read_bytes()) for p in paths}
    lock=read(canonical/"packages.lock.json")
    public_names=list(lock["dependencies"]["net10.0"])
    s,t,origin,token,password,bearer,basic,stats,npm,native=serve(paths)
    checks=[]
    def check(label,ok):
        require(ok,label)
        checks.append(label)
        print(label+": PASS")
    try:
        for _,_,filename,route in npm+[native]:
            auth=bearer if route.startswith("/npm/") else basic
            check(filename+" anonymous denied",request_status(origin+route)[0]==401)
            check(filename+" wrong credential denied",request_status(origin+route,"Bearer invalid")[0]==401)
            code,data=request_status(origin+route,auth)
            check(filename+" authenticated raw bytes",code==200 and sha(data)==expected[filename])
            check(filename+" overwrite denied",request_status(origin+route,auth,"PUT")[0]==405)
            check(filename+" deletion denied",request_status(origin+route,auth,"DELETE")[0]==405)
        for route,auth in [("/npm/@taktera/unknown",bearer),("/flat/taktera.unknown/index.json",basic)]:
            check("unknown private package rejected "+route,request_status(origin+route,auth)[0]==404)
        check("anonymous npm metadata denied",request_status(origin+"/npm/"+npm[0][0])[0]==401)
        check("anonymous NuGet index denied",request_status(origin+"/nuget/v3/index.json")[0]==401)
        with tempfile.TemporaryDirectory(prefix="taktera-registry-fixture-") as tmp:
            work=Path(tmp)
            home=work/"home";home.mkdir()
            npmrc=work/".npmrc";npmrc.write_text(npm_config(origin+"/npm/","TAKTERA_FIXTURE_TOKEN"))
            globalrc=work/"global.npmrc";globalrc.write_text("")
            env=dict(os.environ,HOME=str(home),NPM_CONFIG_USERCONFIG=str(npmrc),NPM_CONFIG_GLOBALCONFIG=str(globalrc),
                     NPM_CONFIG_CACHE=str(work/"npm-cache"),TAKTERA_FIXTURE_TOKEN=token,
                     DOTNET_CLI_HOME=str(home),NUGET_PACKAGES=str(work/"nuget-cache"),
                     NUGET_HTTP_CACHE_PATH=str(work/"nuget-http"),DOTNET_CLI_TELEMETRY_OPTOUT="1",
                     AVALONIA_TELEMETRY_OPTOUT="1",NO_PROXY="127.0.0.1,localhost",
                     NuGetPackageSourceCredentials_TakteraPrivate="Username=fixture;Password="+password+";ValidAuthenticationTypes=Basic")
            check("pinned Node",run(["node","--version"],work,env)=="v26.13.1")
            check("pinned npm",run(["npm","--version"],work,env)=="11.20.0")
            shutil.copyfile(ROOT/"global.json",work/"global.json")
            check("pinned .NET",run(["dotnet","--version"],work,env)=="10.0.404")
            for name,version,filename,_ in npm:
                run(["npm","pack",name+"@"+version,"--ignore-scripts","--json"],work,env)
                check("npm CLI fetched exact "+name,(work/filename).is_file() and sha((work/filename).read_bytes())==expected[filename])
            name,version,filename,_=native
            cfg=work/"NuGet.Config"
            cfg.write_text(nuget_config(origin+"/nuget/v3/index.json",public_names,loopback=True),encoding="utf-8")
            proj=work/"RegistryConsumer.csproj"
            proj.write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework></PropertyGroup><ItemGroup><PackageReference Include="'+name+'" Version="['+version+']"/></ItemGroup></Project>',encoding="utf-8")
            run(["dotnet","restore",str(proj),"--configfile",str(cfg),"-p:NuGetAudit=true",
                 "-p:NuGetAuditMode=all","-warnaserror:NU1900,NU1903,NU1904,NU1905"],work,env)
            restored=work/"nuget-cache"/name.lower()/version.lower()/(name.lower()+"."+version.lower()+".nupkg")
            check("NuGet CLI restored exact canonical archive",restored.is_file() and sha(restored.read_bytes())==expected[filename])
            metadata=read(restored.parent/".nupkg.metadata")
            check("NuGet private source identity",metadata["source"].rstrip("/")== (origin+"/nuget/v3/index.json").rstrip("/"))
            for dep in public_names:
                ver=lock["dependencies"]["net10.0"][dep]["resolved"]
                dep_meta=read(work/"nuget-cache"/dep.lower()/ver.lower()/".nupkg.metadata")
                check("NuGet public mapping "+dep,dep_meta["source"].rstrip("/")==PUBLIC_NUGET.rstrip("/"))
        check("fixture has no write implementation",stats["writesDenied"]==6)
    finally:
        s.shutdown();s.server_close();t.join(timeout=5)
    report={"status":"passed","sourceCommit":source,"githubRunId":verified["githubRunId"],
            "candidateManifestSha256":verified["candidateManifestSha256"],"canonicalPackages":expected,
            "checks":checks,"requestCounts":stats,"scope":"isolated loopback read-only protocol fixture; npm pack and NuGet restore",
            "realRegistryTested":False,"registryPublished":False,"signed":False,"licenseReview":"pending"}
    out.mkdir(parents=True,exist_ok=True)
    (out/"registry-fixture-report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"registryFixture":{"checks":len(checks),"realRegistryTested":False,"published":False}},sort_keys=True))

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("candidate","canonical","output"): p.add_argument(name,type=Path)
    a=p.parse_args()
    main(a.candidate,a.canonical,a.output)
