#!/usr/bin/env python3
"""Alpha.2 package reproducibility and SHA-256 manifest. Run from any directory."""
import hashlib,json,os,subprocess,sys,zipfile
from pathlib import Path
root=Path(__file__).resolve().parents[2]
manifest_path=root/'PACKAGE-MANIFEST-ALPHA2.json'
validation_path=root/'VALIDATION-ALPHA2.json'
archive=root.parent/(root.name+'.zip')
# Release gated by automatic checks generated in this same package.
for task in ['validate_static.py']:
    subprocess.run([sys.executable,str(Path(__file__).resolve().parent/task)],check=True)
static=json.loads((root/'17_packages/qa/static-qa.json').read_text())
browser=json.loads((root/'17_packages/qa/browser-qa.json').read_text())
assert static['failed']==0 and browser['failed']==0, 'Test failures must block release'
freeze=json.loads((root/'16_quality/BRAND-FREEZE-v3.3.json').read_text())
assert freeze['count']==248
# Preserve complete layout; manifest cannot include its own hash.
items=[]
for p in sorted(root.rglob('*')):
    if not p.is_file() or p in (manifest_path,validation_path) or '__pycache__' in p.parts:
        continue
    relative=p.relative_to(root).as_posix();raw=p.read_bytes()
    items.append({'path':relative,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
manifest={'package':'Taktera Design System v4.0 Alpha.2','date':'2026-11-22','source':'Alpha.1 extension (approved brand frozen)',
          'asset_count_excluding_manifest_and_validation':len(items),'assets':items}
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
validation={'status':'ALPHA.2 — development preview, not production',
  'browser_checks':browser['passed'],'browser_failed':browser['failed'],
  'static_checks':static['passed'],'static_failed':static['failed'],
  'approved_brand_assets_frozen':freeze['count'],
  'web_core':'executed in Chromium + DOM injected source due to navigation restrictions',
  'react':'TSX parsed via TypeScript transpileModule; npm install/full typecheck/build NOT executed',
  'avalonia':'XAML XML/resource keys checked; native dotnet build NOT executed',
  'limitations':['npm registry unavailable','dotnet SDK missing','real OS/screen readers not tested','icon proposals not approved','not a WCAG certification'],
  'manifest_sha256':hashlib.sha256(manifest_path.read_bytes()).hexdigest()}
validation_path.write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=7) as z:
    for p in sorted(root.rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts:
            z.write(p,arcname=f'{root.name}/{p.relative_to(root).as_posix()}')
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None,'Archive has bad CRC'
    internal=set(z.namelist())
    for f in items:
        assert f'{root.name}/{f["path"]}' in internal
    assert f'{root.name}/{manifest_path.name}' in internal
print(f'PACKAGE: {archive}\nFiles (manifest excludes 2 generated): {len(items)}; ZIP bytes: {archive.stat().st_size}; CRC: OK')
