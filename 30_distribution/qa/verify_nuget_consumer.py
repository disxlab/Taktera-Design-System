#!/usr/bin/env python3
"""Pack compiled Avalonia library, build and headless-test a clean package-only consumer."""
import hashlib, json, os, shutil, subprocess, tempfile, zipfile, time, sys, re
from contextlib import contextmanager
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
@contextmanager
def isolated_workspace():
    tmp=Path(tempfile.mkdtemp(prefix='taktera-nuget-')).resolve()
    env=dict(os.environ,NUGET_PACKAGES=str(tmp/'packages'),DOTNET_CLI_TELEMETRY_OPTOUT='1',MSBUILDDISABLENODEREUSE='1',DOTNET_CLI_USE_MSBUILD_SERVER='0',AVALONIA_TELEMETRY_OPTOUT='1')
    try:
        # SDK discovery starts from the working directory, which is outside the repo.
        shutil.copyfile(ROOT/"global.json", tmp/"global.json")
        expected=json.loads((tmp/"global.json").read_text(encoding="utf-8"))["sdk"]["version"]
        actual=subprocess.check_output(["dotnet","--version"],cwd=tmp,env=env,text=True).strip()
        if actual != expected: raise RuntimeError(f"Expected .NET SDK {expected}, got {actual}")
        report["dotnetSdk"]=actual
        yield tmp,env
    finally:
        # Build task assemblies may be held by reusable MSBuild processes on Windows.
        # Avalonia's documented build-time telemetry opt-out avoids a separate collector
        # process holding the isolated package cache. No runtime/test gate is disabled.
        # https://github.com/AvaloniaUI/Avalonia.BuildServices#opting-out
        subprocess.run(['dotnet','build-server','shutdown'],cwd=tmp,env=env,check=True,timeout=60)
        for attempt in range(6):
            try:
                shutil.rmtree(tmp)
                break
            except PermissionError:
                if attempt==5: raise
                time.sleep(1)
try:
    with isolated_workspace() as (tmp,env):
        feed=tmp/'feed'; feed.mkdir()
        canonical_input=os.environ.get('TAKTERA_CANONICAL_INPUT')
        report['mode']='canonical' if canonical_input else 'independent-build'
        if not canonical_input:
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
        if canonical_input:
            incoming=(ROOT/canonical_input).resolve()
            manifest=json.loads((incoming/'canonical.json').read_text(encoding='utf-8'))
            source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
            check('canonical source checkout',manifest['source']==source and manifest['published'] is False)
            check('independent runner agreement',manifest['independentRunnerJobs']==2 and manifest['cleanBuilds']==4)
            name,=[n for n in manifest['packages'] if n.endswith('.nupkg')]
            check('safe canonical package name',bool(re.fullmatch(r'[A-Za-z0-9._-]+\.nupkg',name)))
            package=incoming/name
            check('canonical package hash',hashlib.sha256(package.read_bytes()).hexdigest()==manifest['packages'][name])
            shutil.copyfile(package,feed/name)
            report['canonicalSource']=source
        else:
            run(['dotnet','restore',str(project),'--configfile',str(cfg),'--locked-mode',*audit],lib,env)
            run(['dotnet','pack',str(project),'-c','Release','--no-restore','--disable-build-servers','-o',str(feed),'-warnaserror'],lib,env)
        package,=feed.glob('*.nupkg')
        with zipfile.ZipFile(package) as z:
            entries=z.namelist()
            check('compiled package assembly','lib/net10.0/Taktera.UI.Avalonia.dll' in entries)
            check('XML API docs','lib/net10.0/Taktera.UI.Avalonia.xml' in entries)
            check('no sample or source in package',not any('/sample/' in n or n.endswith(('.cs','.csproj','.axaml')) for n in entries))
        report['package']={'name':package.name,'sha256':hashlib.sha256(package.read_bytes()).hexdigest(),'entries':entries}
        shutil.copy2(package,OUT/package.name)
        host=tmp/'consumer';host.mkdir()
        run([sys.executable,str(ROOT/'30_distribution/taktera.py'),'init','avalonia','--packages',str(feed),'--output',str(host/'app')],ROOT,env)
        check('Avalonia CLI creates verified local package inventory',json.loads((host/'app/package-inventory.json').read_text(encoding='utf-8'))[0]['sha256']==report['package']['sha256'])
        shutil.copytree(SOURCE/'tests',host/'tests',ignore=shutil.ignore_patterns('bin','obj'))
        app=host/'app/Taktera.Reference.csproj';tests=host/'tests/Taktera.Reference.Tests.csproj'
        check('consumer has no library project reference',not ET.parse(app).findall('.//ProjectReference'))
        for p in (app,tests):
            run(['dotnet','restore',str(p),'--configfile',str(app.parent/'NuGet.Config' if p==app else cfg),*audit],host,env)
        assets_json=json.loads((app.parent/'obj/project.assets.json').read_text(encoding='utf-8'))
        for p in (app,tests):
            resolved=json.loads((p.parent/'obj/project.assets.json').read_text(encoding='utf-8'))
            selected=[v for k,v in resolved['libraries'].items() if k.lower().startswith('taktera.ui.avalonia/')]
            check(p.stem+' resolved library is NuGet package',len(selected)==1 and selected[0]['type']=='package')
            if canonical_input:
                installed=tmp/'packages'/selected[0]['path']/package.name.lower()
                check(p.stem+' restored exact canonical archive',installed.is_file() and hashlib.sha256(installed.read_bytes()).hexdigest()==report['package']['sha256'])
                with zipfile.ZipFile(package) as z:
                    installed_dll=tmp/'packages'/selected[0]['path']/'lib/net10.0/Taktera.UI.Avalonia.dll'
                    check(p.stem+' restored exact canonical DLL',installed_dll.read_bytes()==z.read('lib/net10.0/Taktera.UI.Avalonia.dll'))
            check(p.stem+' has compiled package reference',any('lib/net10.0/Taktera.UI.Avalonia.dll' in item.get('compile',{}) for target in resolved['targets'].values() for key,item in target.items() if key.lower().startswith('taktera.ui.avalonia/')))
        run(['dotnet','build',str(app),'-c','Release','--no-restore','--disable-build-servers','-warnaserror'],host,env)
        check('independent desktop compilation',True)
        run(['dotnet','test',str(tests),'-c','Release','--no-restore','--disable-build-servers','--logger','trx;LogFileName=consumer.trx','--results-directory',str(OUT)],host,env)
        check('packaged runtime resource and interaction tests',True)
        shutil.copy2(app.parent/'obj/project.assets.json',OUT/'consumer-project.assets.json')
except Exception as e:
    report['errors'].append(str(e))
finally:
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'nugetConsumerChecks':len(report['checks']),'passed':sum(c['ok'] for c in report['checks']),'errors':report['errors']}))
if report['errors']: raise SystemExit(1)
