#!/usr/bin/env python3
"""Collect successful CI outputs into a non-published candidate evidence bundle."""
import argparse,base64,hashlib,json,os,re,shutil,subprocess,tarfile
from pathlib import Path
from urllib.parse import quote
from product_sbom import build as build_product_sbom
from validate_sbom import validate as validate_product_sboms
from dependency_licenses import build as build_license_evidence
def require(ok,message):
    if not ok:raise AssertionError(message)
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def write(path,data):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def copy(source,out):
    out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,out)
def safe_name(name):
    require(isinstance(name,str) and re.fullmatch(r'[A-Za-z0-9._-]+',name) and name not in ('.','..'),'Unsafe artifact filename')
    return name
def passed(report):
    require(report.get('errors')==[] and report.get('checks') and all(c.get('ok') is True for c in report['checks']),'Consumer report is not passing')
def bom(name,components,scope):
    refs=[c['bom-ref'] for c in components];require(len(refs)==len(set(refs)),'Duplicate SBOM reference')
    return {'bomFormat':'CycloneDX','specVersion':'1.6','version':1,'metadata':{'component':{'type':'application','name':name},'properties':[{'name':'taktera:inventoryScope','value':scope},{'name':'taktera:licenseReview','value':'pending'}]},'components':sorted(components,key=lambda c:c['bom-ref'])}
def hash512(integrity):
    if not isinstance(integrity,str):return []
    for value in integrity.split():
        if value.startswith('sha512-'):value=value[7:]
        try:
            raw=base64.b64decode(value,validate=True)
            if len(raw)==64:return [{'alg':'SHA-512','content':raw.hex()}]
        except ValueError:pass
    return []
def npm_bom(lock):
    require(lock.get('lockfileVersion')==3 and isinstance(lock.get('packages'),dict),'Expected actual npm lock v3')
    components=[]
    for path,item in lock['packages'].items():
        if not path:continue
        require(not item.get('link'),'Unresolved link in consumer inventory')
        name=item.get('name') or path.rsplit('node_modules/',1)[-1];version=item.get('version')
        require(name and version and not name.startswith('.'),'Unresolved npm package')
        purl='pkg:npm/'+quote(name,safe='/')+'@'+quote(version,safe='')
        c={'type':'library','name':name,'version':version,'purl':purl,'bom-ref':'npm:'+path,'properties':[{'name':'taktera:devDependency','value':str(bool(item.get('dev'))).lower()},{'name':'taktera:lockPath','value':path}]}
        hashes=hash512(item.get('integrity'))
        if hashes:c['hashes']=hashes
        components.append(c)
    require(components,'Empty npm inventory')
    return bom('Taktera npm reference consumer',components,'Actual consumer lock including tooling; not a complete shipped-product SBOM.')
def nuget_bom(assets,platform):
    components=[]
    for key,item in assets['libraries'].items():
        if item.get('type')!='package':continue
        name,version=key.rsplit('/',1)
        c={'type':'library','name':name,'version':version,'purl':'pkg:nuget/'+quote(name,safe='')+'@'+quote(version,safe=''),'bom-ref':'nuget:'+key}
        hashes=hash512(item.get('sha512'))
        if hashes:c['hashes']=hashes
        components.append(c)
    require(any(c['name'].lower()=='taktera.ui.avalonia' for c in components),'Missing native package from resolved dependencies')
    return bom('Taktera Avalonia consumer '+platform,components,'Actual desktop consumer resolved packages, including build dependencies; not a complete shipped-product SBOM.')
def normalized_digest(data):return hashlib.sha256(data.replace(b'\r\n',b'\n')).hexdigest()
def main(inp,out):
    require(not out.exists(),'Refusing to overwrite candidate output')
    out.mkdir(parents=True)
    npm=inp/'npm';report=read(npm/'report.json');passed(report)
    api=read(npm/'api-contract.json')
    source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    require(api['source']==source,'API evidence belongs to a different checkout')
    canonical=inp/'canonical';manifest=read(canonical/'canonical.json')
    require(manifest['source']==source and manifest['published'] is False and manifest['independentRunnerJobs']==2 and manifest['cleanBuilds']==4,'Invalid canonical evidence')
    require(sha(canonical/'packages.lock.json')==manifest['nugetLockSha256'],'Canonical lock checksum mismatch')
    for file in ('canonical.json','packages.lock.json','repro-primary.json','repro-secondary.json'):copy(canonical/file,out/'evidence/reproducibility'/file)
    packages=[]
    require({p['name'] for p in report['packages']}=={'@taktera/ui-react','@taktera/ui-core'} and len(report['packages'])==2,'Unexpected npm package set')
    for p in report['packages']:
        filename=safe_name(p['filename']);src=npm/filename;require(sha(src)==p['sha256'],'npm checksum mismatch '+filename)
        with tarfile.open(src,'r:gz') as archive:
            expected=api['reactDeclarations'] if p['name']=='@taktera/ui-react' else api['webDeclarations']
            require(expected,'Empty declaration baseline')
            prefix='package/dist/' if p['name']=='@taktera/ui-react' else 'package/'
            names={m.name for m in archive.getmembers() if m.isfile() and m.name.startswith(prefix) and (m.name.endswith('.d.ts') or m.name.endswith('.d.mts'))}
            require(names=={prefix+k for k in expected},'Packaged declaration set differs from baseline')
            for key,digest in expected.items():require(normalized_digest(archive.extractfile(prefix+key).read())==digest,'Packaged declaration mismatch '+key)
        require(sha(src)==manifest['packages'][filename]==sha(canonical/filename),'Tested npm package differs from reproducible canonical archive')
        dest=out/'packages/npm'/filename;copy(canonical/filename,dest);packages.append({'name':p['name'],'version':p['version'],'file':dest.relative_to(out).as_posix(),'sha256':sha(dest)})
    for file in ('report.json','api-contract.json','consumer-package-lock.json'):copy(npm/file,out/'evidence/npm'/file)
    write(out/'sbom/npm-consumer.cdx.json',npm_bom(read(npm/'consumer-package-lock.json')))
    for platform in ('windows','macos'):
        native=inp/('nuget-'+platform);report=read(native/'report.json');passed(report);p=report['package']
        filename=safe_name(p['name']);src=native/filename;require(sha(src)==p['sha256'],'NuGet checksum mismatch '+platform)
        require(report.get('mode')=='canonical' and report.get('canonicalSource')==source,'Expected canonical consumer evidence '+platform)
        require(sha(src)==manifest['packages'][filename]==sha(canonical/filename),'Canonical NuGet differs '+platform)
        dest=out/'packages'/'nuget'/filename
        if platform=='windows':
            copy(canonical/filename,dest);packages.append({'name':'Taktera.UI.Avalonia','file':dest.relative_to(out).as_posix(),'platforms':['windows','macos'],'sha256':sha(dest)})
        else:require(sha(dest)==sha(src),'Cross-OS package mismatch')
        for file in ('report.json','consumer-project.assets.json','consumer.trx'):copy(native/file,out/'evidence'/('nuget-'+platform)/file)
        write(out/'sbom'/('nuget-'+platform+'-consumer.cdx.json'),nuget_bom(read(native/'consumer-project.assets.json'),platform))
    require(len(packages)==3 and {Path(p['file']).name:p['sha256'] for p in packages}==manifest['packages'],'Candidate does not equal canonical set')
    for file in ('npm-audit.json','nuget-audit.json'):
        read(inp/'audit'/file);copy(inp/'audit'/file,out/'evidence/audit'/file)
    product_stats=build_product_sbom(out,packages,source,read(npm/'consumer-package-lock.json'),read(canonical/'packages.lock.json'))
    product_stats=validate_product_sboms(out)
    license_stats=build_license_evidence(out,read(npm/'consumer-package-lock.json'),read(canonical/'packages.lock.json'))
    write(out/'build-evidence.json',{'sourceCommit':source,'githubRunId':os.environ.get('GITHUB_RUN_ID'),'githubRunAttempt':os.environ.get('GITHUB_RUN_ATTEMPT'),'workflowRef':os.environ.get('GITHUB_WORKFLOW_REF'),'packages':packages,'apiBaseline':api['baseline'],'status':'automated candidate evidence only','signed':False,'registryPublished':False,'licenseReview':'pending','manualAndStagingAcceptance':'pending'})
    sums={p.relative_to(out).as_posix():sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
    (out/'SHA256SUMS.txt').write_text(''.join(d+'  '+name+'\n' for name,d in sorted(sums.items())),encoding='utf-8')
    require(all(sha(out/name)==d for name,d in sums.items()),'Candidate evidence changed during assembly')
    print(json.dumps({'candidatePackages':len(packages),'sbomInventories':5,'productInventory':product_stats,'licenseEvidence':license_stats,'hashedFiles':len(sums),'source':source,'published':False}))
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('input',type=Path);parser.add_argument('output',type=Path);args=parser.parse_args();main(args.input,args.output)
