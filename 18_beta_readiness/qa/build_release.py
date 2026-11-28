#!/usr/bin/env python3
"""Alpha.3 gated archive, per-file SHA256 manifest and explicit limitations."""
import hashlib,json,os,subprocess,sys,zipfile
from pathlib import Path
root=Path(__file__).resolve().parents[2]
manifest_path=root/'PACKAGE-MANIFEST-ALPHA3.json'
validation_path=root/'VALIDATION-ALPHA3.json'
archive=root.parent/(root.name+'.zip')
qa=root/'18_beta_readiness/qa'
def cmd(*args):
    subprocess.run(list(args),cwd=root,check=True,timeout=90)
cmd(sys.executable,'17_packages/qa/validate_static.py')
cmd(sys.executable,'17_packages/qa/test_web.py')
cmd(sys.executable,'18_beta_readiness/qa/test_alpha3.py')
cmd(sys.executable,'18_beta_readiness/qa/verify_install.py')
checks={
 'static':json.loads((root/'17_packages/qa/static-qa.json').read_text()),
 'chromium_base':json.loads((root/'17_packages/qa/browser-qa.json').read_text()),
 'chromium_extended':json.loads((qa/'browser-extended.json').read_text()),
 'npm_offline':json.loads((qa/'offline-package-check.json').read_text())
}
assert checks['static']['failed']==0 and checks['chromium_base']['failed']==0 and checks['chromium_extended']['failed']==0
assert checks['npm_offline']['status']=='PASS'
freeze=json.loads((root/'16_quality/BRAND-FREEZE-v3.3.json').read_text())
assert freeze['count']==248
sha=lambda b:hashlib.sha256(b).hexdigest()
# Manifest itself and validation are generated separately. Old historical manifests are retained for comparison.
files=[]
for p in sorted(root.rglob('*')):
    if not p.is_file() or p in (manifest_path,validation_path):continue
    if '__pycache__' in p.parts or 'node_modules' in p.parts or '.npm-cache' in p.parts:continue
    rel=p.relative_to(root).as_posix()
    files.append({'path':rel,'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())})
manifest={'package':'Taktera Design System v4.0 Alpha.3','created':'2026-11-22','status':'beta readiness milestone, NOT beta release',
          'file_count_excluding_manifest_and_validation':len(files),'files':files}
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
validation={'version':'4.0-alpha.3','release_status':'DEVELOPMENT ALPHA / NOT BETA / NOT PRODUCTION',
            'approved_brand_assets_sha256_frozen':248,
            'chromium_base_passed':checks['chromium_base']['passed'],
            'chromium_extended_passed':checks['chromium_extended']['passed'],
            'static_passed':checks['static']['passed'],
            'npm_offline_pack_install_esm':'PASS',
            'web_core_typescript_public_contract':'tsc strict test PASS (global tsc)',
            'react':'source only: TSX syntax transpile passed; npm registry unavailable: no actual React build/typecheck',
            'avalonia':'source only: XAML XML/resource check passed; no .NET SDK/native compile',
            'unverified':['GitHub Actions CI not executed','NVDA/VoiceOver/axe-core not run','No real OS native app test','WCAG 2.2 certification not claimed','Icon A/B approval pending'],
            'manifest_sha256':sha(manifest_path.read_bytes())}
validation_path.write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n')
# Stable member ordering; preserve single common root to make extraction safe.
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=7) as z:
    for item in files+[{'path':manifest_path.name},{'path':validation_path.name}]:
        p=root/item['path'];rel=f'{root.name}/{item["path"]}'
        info=zipfile.ZipInfo(rel,date_time=(2026,11,22,12,0,0))
        info.compress_type=zipfile.ZIP_DEFLATED
        info.external_attr=(0o100644<<16)
        z.writestr(info,p.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=7)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for item in files:
        assert sha(z.read(root.name+'/'+item['path']))==item['sha256']
    assert sha(z.read(root.name+'/'+manifest_path.name))==validation['manifest_sha256']
    assert len(z.namelist())==len(files)+2
print('RELEASE',archive)
print('Files:',len(files)+2,'ZIP bytes:',archive.stat().st_size,'SHA256:',sha(archive.read_bytes()))
