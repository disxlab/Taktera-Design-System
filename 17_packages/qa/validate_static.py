#!/usr/bin/env python3
"""Verifiable static gates: original brand hashes, CSS generated parity, XAML XML/key usage, file links."""
import hashlib,json,re,sys,subprocess
from pathlib import Path
from lxml import etree
root=Path(__file__).resolve().parents[2]
new=root/'17_packages'
checks=[]
def test(name,valid):
    checks.append({'name':name,'ok':bool(valid)})
    if not valid:print('FAIL',name)
source=json.loads((root/'16_quality/BRAND-FREEZE-v3.3.json').read_text())
for item in source['files']:
    p=root/item['path'];test('brand original: '+item['path'],p.is_file() and p.stat().st_size==item['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'])
process=subprocess.run([sys.executable,str(new/'web-core/build.py'),'--check'],capture_output=True,text=True)
test('web bundled css synchronized',process.returncode==0)
test('react css equals web core css',(new/'react/styles.css').read_bytes()==(new/'web-core/taktera-ui.css').read_bytes())
for p in sorted((new/'avalonia').rglob('*.axaml')):
    try: etree.parse(str(p));test('valid Avalonia XAML XML: '+str(p.relative_to(new)),True)
    except Exception: test('valid Avalonia XAML XML: '+str(p.relative_to(new)),False)
# Verify every DynamicResource on toolkit is available in all 12 product palette dictionaries.
text='\n'.join(p.read_text() for p in (new/'avalonia').glob('*.axaml'))
keys=set(re.findall(r'\{DynamicResource (\w+)\}',text))
for p in sorted((root/'15_platform_adapters/avalonia').glob('*.axaml')):
    tree=etree.parse(str(p)); defined={v for e in tree.iter() for k,v in e.attrib.items() if k.endswith('}Key')}
    test('all ControlTheme colors in '+p.name, keys <= defined)
for p in [(new/'samples/index.html'),(new/'samples/demo.js'),(new/'web-core/taktera-ui.js'),(new/'react/package.json')]:
    test('nonempty source: '+p.name,p.is_file() and p.stat().st_size>100)
# Fail on hardcoded untrusted HTML injection in core library
js=(new/'web-core/taktera-ui.js').read_text()
test('core avoids innerHTML injection','.innerHTML' not in js and 'insertAdjacentHTML' not in js)
# No accidental replacement of the established logo and icon proposals
result={'version':'4.0-alpha.3','checks':len(checks),'passed':sum(c['ok'] for c in checks),'failed':sum(not c['ok'] for c in checks),'details':checks}
(new/'qa/static-qa.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(f"Static checks: {result['passed']}/{len(checks)}")
sys.exit(1 if result['failed'] else 0)
