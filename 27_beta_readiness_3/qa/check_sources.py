#!/usr/bin/env python3
"""Offline release preflight; static only (not compiler, renderer or accessibility audit)."""
from pathlib import Path
import json, re, sys, xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
failures=[]; checks=[]
def check(ok, message):
    checks.append({'name':message,'passed':bool(ok)})
    if not ok: failures.append(message)
react=ROOT/'17_packages/react'
pkg=json.loads((react/'package.json').read_text(encoding='utf-8'))
check(pkg.get('private') is True,'React package remains private until release approval')
check('tsx' in pkg.get('devDependencies',{}),'React smoke test runner dependency declared')
check('smoke' in pkg.get('scripts',{}),'React SSR smoke script available')
check((react/'qa/smoke.tsx').exists(),'React SSR test source exists')
check((react/'src/index.tsx').exists(),'React source entrypoint exists')
ava=ROOT/'17_packages/avalonia/sample'
check((ava/'TakteraUiAvalonia.Sample.csproj').exists(),'Avalonia sample csproj exists')
check((ava/'Program.cs').exists(),'Avalonia application code exists')
check((ava/'App.axaml').exists() and (ava/'MainWindow.axaml').exists(),'Avalonia application XAML exists')
# Generated dictionaries and all referenced brushes must be coherent
resources=ROOT/'25_internal_completion/generated/avalonia'
dictionaries=sorted(resources.glob('Taktera.*.axaml'))
check(len(dictionaries)==12,'Exactly 12 product/theme resource dictionaries generated')
ns='{http://schemas.microsoft.com/winfx/2006/xaml}Key'
all_keys=[]
for file in dictionaries:
    try:
        xml=ET.parse(file).getroot()
        keys=[e.attrib[ns] for e in xml.iter() if ns in e.attrib]
        check(len(keys)==len(set(keys)),f'No duplicate resource keys: {file.name}')
        check('TknBrandAccentBrush' in keys,f'Canonical accent brush exists: {file.name}')
        all_keys.append(set(keys))
    except Exception as e:check(False,f'Invalid Avalonia dictionary {file.name}: {e}')
for rel in ['App.axaml','MainWindow.axaml','Assets/TkControls.axaml','Assets/TkFieldStyles.axaml','Assets/Taktera.Clinic.Light.axaml']:
    try:ET.parse(ava/rel);check(True,f'Well-formed Avalonia XAML: {rel}')
    except Exception as e:check(False,f'Invalid Avalonia XAML: {rel}: {e}')
# Ensure every theme contains resource names used by base control templates
required=set()
for rel in ['Assets/TkControls.axaml','Assets/TkFieldStyles.axaml','App.axaml','MainWindow.axaml']:
    txt=(ava/rel).read_text(encoding='utf-8')
    required.update(re.findall(r'\{(?:DynamicResource|StaticResource)\s+(Tk\w+Brush)\}',txt))
compat=ROOT/'27_beta_readiness_3/avalonia_compat'
compat_files=sorted(compat.glob('Taktera.*.axaml'))
check(len(compat_files)==12,'12 backwards-compatible resource dictionaries generated')
for file in compat_files:
    try:
        keys={e.attrib[ns] for e in ET.parse(file).getroot().iter() if ns in e.attrib}
        missing=required-keys
        check(not missing,f'Legacy Tk* brush coverage in {file.name}: {sorted(missing)}')
    except Exception as e:check(False,f'Compatibility XML invalid: {file.name}: {e}')
# verify sample local snapshot of theme keys
sample=ET.parse(ava/'Assets/Taktera.Clinic.Light.axaml').getroot()
sample_keys={e.attrib[ns] for e in sample.iter() if ns in e.attrib}
check(not(required-sample_keys),'Sample resources cover every referenced Tk*Brush')
workflow=ROOT/'.github/workflows/taktera-beta-readiness.yml'
check(workflow.exists(),'GitHub Actions workflow is included (not yet executed)')
result={'checks':len(checks),'passed':sum(x['passed'] for x in checks),'failed':failures,'items':checks,'limitations':['Static XML check is not an Avalonia build','No npm dependencies fetched in offline environment','Workflow not run on GitHub Actions']}
out=ROOT/'27_beta_readiness_3/qa/preflight.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'Static preflight: {result["passed"]}/{result["checks"]} PASS')
for f in failures:print('FAIL:',f)
sys.exit(1 if failures else 0)
