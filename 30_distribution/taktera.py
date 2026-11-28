#!/usr/bin/env python3
"""Offline scaffolding from explicitly supplied, already verified local candidate packages."""
import argparse,hashlib,json,re,shutil,tarfile,tempfile,zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parent
def read_npm(path):
    with tarfile.open(path,'r:gz') as z:
        member=z.getmember('package/package.json')
        if not member.isfile() or member.size>1024*1024:raise ValueError('Invalid manifest')
        return json.load(z.extractfile(member))
def read_nuget(path):
    with zipfile.ZipFile(path) as z:
        names=[n for n in z.namelist() if '/' not in n and n.endswith('.nuspec')]
        if len(names)!=1 or z.getinfo(names[0]).file_size>1024*1024:raise ValueError('Invalid nuspec')
        root=ET.fromstring(z.read(names[0]))
        metadata=root.find('{*}metadata')
        return {'name':metadata.findtext('{*}id'),'version':metadata.findtext('{*}version')}
def init(target,packages,output):
    expected={'react':['@taktera/ui-react','@taktera/ui-core'],'web':['@taktera/ui-core'],'avalonia':['Taktera.UI.Avalonia']}[target]
    found={}
    for p in sorted(packages.iterdir()):
        if not p.is_file() or p.suffix not in ('.tgz','.nupkg'):continue
        if p.suffix!=('.nupkg' if target=='avalonia' else '.tgz'):continue
        meta=read_nuget(p) if p.suffix=='.nupkg' else read_npm(p)
        if meta['name'] not in expected:continue
        if meta['name'] in found:raise ValueError('Duplicate package: '+meta['name'])
        if not re.fullmatch(r'[A-Za-z0-9._-]+',p.name):raise ValueError('Unsafe archive filename')
        found[meta['name']]=(p,meta)
    if set(found)!=set(expected):raise ValueError('Missing required local packages: '+str(set(expected)-set(found)))
    if output.exists():raise FileExistsError('Refusing to overwrite existing destination')
    if not output.parent.is_dir():raise ValueError('Destination parent must exist')
    with tempfile.TemporaryDirectory(prefix='.taktera-init-',dir=output.parent) as temp:
        stage=Path(temp)/'app';stage.mkdir();vendor=stage/'vendor';vendor.mkdir()
        inventory=[]
        for name,(path,meta) in found.items():
            shutil.copy2(path,vendor/path.name);inventory.append({'name':name,'version':meta['version'],'file':'vendor/'+path.name,'sha256':hashlib.sha256((vendor/path.name).read_bytes()).hexdigest()})
        if target=='avalonia':
            shutil.copytree(ROOT/'reference-dotnet/app',stage,dirs_exist_ok=True,ignore=shutil.ignore_patterns('bin','obj'))
            proj=stage/'Taktera.Reference.csproj';doc=ET.parse(proj)
            for p in doc.findall('.//PackageReference'):
                if p.attrib['Include']=='Taktera.UI.Avalonia':p.set('Version','['+found['Taktera.UI.Avalonia'][1]['version']+']')
            doc.write(proj,encoding='utf-8',xml_declaration=True)
            (stage/'NuGet.Config').write_text('<?xml version="1.0"?><configuration><packageSources><clear/><add key="local" value="vendor"/><add key="nuget.org" value="https://api.nuget.org/v3/index.json"/></packageSources><packageSourceMapping><packageSource key="local"><package pattern="Taktera.UI.Avalonia"/></packageSource><packageSource key="nuget.org"><package pattern="*"/></packageSource></packageSourceMapping></configuration>\n',encoding='utf-8')
            quick='dotnet restore --configfile NuGet.Config\ndotnet run --no-restore'
        else:
            deps={name:'file:vendor/'+p.name for name,(p,meta) in found.items()}
            dev={}
            if target=='react':
                lock=json.loads((REPO/'17_packages/react/package-lock.json').read_text(encoding='utf-8'))
                def version(n):return lock['packages']['node_modules/'+n]['version']
                deps.update({n:version(n) for n in ('react','react-dom')})
                dev={n:version(n) for n in ('typescript','@types/react','@types/react-dom','esbuild')}
                for file in ('App.tsx','client.tsx','tsconfig.json','LocalizedTransport.tsx','LocalizedOperations.tsx','synthetic-transport.d.mts','build.mjs'):
                    shutil.copy2(ROOT/'reference-react'/file,stage/file)
                shutil.copy2(ROOT/'acceptance/transport/synthetic-transport.mjs',stage/'synthetic-transport.mjs')
                shutil.copy2(ROOT/'templates/react/serve.mjs',stage/'serve.mjs')
                scripts={'build':'node build.mjs','start':'node serve.mjs'}
                quick='npm install --package-lock-only\nnpm ci\nnpm run build\nnpm start'
            else:
                for file in ('index.html','app.js','serve.mjs'):
                    shutil.copy2(ROOT/'templates/web'/file,stage/file)
                scripts={'start':'node serve.mjs'}
                quick='npm install --package-lock-only\nnpm ci\nnpm start'
            (stage/'package.json').write_text(json.dumps({'name':'taktera-starter','version':'0.0.0','private':True,'type':'module','dependencies':deps,'devDependencies':dev,'scripts':scripts},indent=2)+'\n',encoding='utf-8')
        (stage/'package-inventory.json').write_text(json.dumps(inventory,indent=2)+'\n',encoding='utf-8')
        (stage/'.gitignore').write_text('node_modules/\ndist/\nbin/\nobj/\n',encoding='utf-8')
        (stage/'README.md').write_text('# Taktera '+target+' starter\n\nSynthetic pre-release example. Do not distribute without approval. Verify archive hashes against trusted CI evidence. Keep generated lockfiles. Host owns production data, authorization and persistence.\n\nRun:\n\n```sh\n'+quick+'\n```\n',encoding='utf-8')
        stage.rename(output)
    return inventory
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    p=commands.add_parser('init');p.add_argument('target',choices=('react','web','avalonia'));p.add_argument('--packages',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    a=parser.parse_args()
    try:
        result=init(a.target,a.packages.resolve(),a.output.absolute())
    except (OSError,ValueError,KeyError,tarfile.TarError,zipfile.BadZipFile,ET.ParseError) as e:
        parser.exit(1,f'Taktera CLI: {e}\n')
    print(json.dumps({'target':a.target,'output':str(a.output),'packages':result},indent=2))
if __name__=='__main__':main()
