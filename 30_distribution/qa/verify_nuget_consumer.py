#!/usr/bin/env python3
"""Pack compiled Avalonia library, build and headless-test a clean package-only consumer."""
import hashlib, json, os, shutil, subprocess, tempfile, zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'30_distribution/reference-dotnet'
OUT=ROOT/'30_distribution/qa/results/nuget'
OUT.mkdir(parents=True,exist_ok=True)
report={'checks':[],'errors':[],'package':None}
def check(name,ok):
    report['checks'].append({'name':name,'ok':bool(ok)})
    if not ok: raise AssertionError(name)
def run(args,cwd,env):
    subprocess.run(args,cwd=cwd,env=env,check=True)
try:
    with tempfile.TemporaryDirectory(prefix='taktera-nuget-') as tmp:
        tmp=Path(tmp); feed=tmp/'feed'; feed.mkdir()
        env=dict(os.environ,NUGET_PACKAGES=str(tmp/'packages'),DOTNET_CLI_TELEMETRY_OPTOUT='1')
        lib=tmp/'library'; shutil.copytree(ROOT/'17_packages/avalonia/library',lib,ignore=shutil.ignore_patterns('bin','obj','Assets'))
        assets=lib/'Assets'; assets.mkdir()
        canonical=ROOT/'17_packages/avalonia'
        compat=ROOT/'27_beta_readiness_3/avalonia_compat'
        names=[f'Taktera.{product}.{theme}.axaml' for product in ('Platform','Clinic','Beauty','Spa','Fitness','Travel') for theme in ('Light','Dark')]
        sources=[canonical/'TkControls.axaml',canonical/'TkFieldStyles.axaml']+[compat/n for n in names]
        for source in sources:
            dest=assets/source.name; shutil.copy2(source,dest)
            check('unchanged '+source.name,dest.read_bytes()==source.read_bytes())
        check('all resource files',len(list(assets.glob('*.axaml')))==14)
        project=lib/'Taktera.UI.Avalonia.csproj'
        config=ET.Element('configuration'); sources=ET.SubElement(config,'packageSources');ET.SubElement(sources,'clear');ET.SubElement(sources,'add',key='local',value=str(feed));ET.SubElement(sources,'add',key='nuget.org',value='https://api.nuget.org/v3/index.json')
        mapping=ET.SubElement(config,'packageSourceMapping');local=ET.SubElement(mapping,'packageSource',key='local');ET.SubElement(local,'package',pattern='Taktera.UI.Avalonia');remote=ET.SubElement(mapping,'packageSource',key='nuget.org');ET.SubElement(remote,'package',pattern='*')
        cfg=tmp/'NuGet.Config';ET.ElementTree(config).write(cfg,encoding='utf-8',xml_declaration=True)
        audit=['-p:NuGetAudit=true','-p:NuGetAuditMode=all','-warnaserror:NU1900,NU1903,NU1904,NU1905']
        run(['dotnet','restore',str(project),'--configfile',str(cfg),*audit],lib,env)
        run(['dotnet','pack',str(project),'-c','Release','--no-restore','-o',str(feed),'-warnaserror'],lib,env)
        package,=feed.glob('*.nupkg')
        with zipfile.ZipFile(package) as z:
            entries=z.namelist()
            check('compiled package assembly','lib/net10.0/Taktera.UI.Avalonia.dll' in entries)
            check('XML API docs','lib/net10.0/Taktera.UI.Avalonia.xml' in entries)
            check('no sample or source in package',not any('/sample/' in n or n.endswith(('.cs','.csproj','.axaml')) for n in entries))
        report['package']={'name':package.name,'sha256':hashlib.sha256(package.read_bytes()).hexdigest(),'entries':entries}
        shutil.copy2(package,OUT/package.name)
        host=tmp/'consumer';shutil.copytree(SOURCE,host,ignore=shutil.ignore_patterns('bin','obj'))
        app=host/'app/Taktera.Reference.csproj';tests=host/'tests/Taktera.Reference.Tests.csproj'
        check('consumer has no library project reference',not ET.parse(app).findall('.//ProjectReference'))
        for p in (app,tests):
            run(['dotnet','restore',str(p),'--configfile',str(cfg),*audit],host,env)
        assets_json=json.loads((app.parent/'obj/project.assets.json').read_text(encoding='utf-8'))
        selected=[v for k,v in assets_json['libraries'].items() if k.lower().startswith('taktera.ui.avalonia/')]
        check('resolved library is NuGet package',len(selected)==1 and selected[0]['type']=='package')
        run(['dotnet','build',str(app),'-c','Release','--no-restore','-warnaserror'],host,env)
        check('independent desktop compilation',True)
        run(['dotnet','test',str(tests),'-c','Release','--no-restore','--logger','trx;LogFileName=consumer.trx','--results-directory',str(OUT)],host,env)
        check('packaged runtime resource and interaction tests',True)
        shutil.copy2(app.parent/'obj/project.assets.json',OUT/'consumer-project.assets.json')
except Exception as e:
    report['errors'].append(str(e))
finally:
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'nugetConsumerChecks':len(report['checks']),'passed':sum(c['ok'] for c in report['checks']),'errors':report['errors']}))
if report['errors']: raise SystemExit(1)
