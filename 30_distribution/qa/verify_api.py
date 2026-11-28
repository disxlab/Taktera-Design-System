#!/usr/bin/env python3
"""Strict candidate API comparison against a known passing source revision."""
import hashlib,json,subprocess,tempfile,tarfile,io
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
REACT=ROOT/'17_packages/react'
OUT=ROOT/'30_distribution/qa/results/npm';OUT.mkdir(parents=True,exist_ok=True)
BASE='e2937521f8a6adb90aaccc09841bbd208b0a687a' # Run 24
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def digest(data):return hashlib.sha256(data.replace(b'\r\n',b'\n')).hexdigest()
def declarations(path):return {str(p.relative_to(path)).replace('\\','/'):digest(p.read_bytes()) for p in sorted(path.rglob('*.d.ts'))}
with tempfile.TemporaryDirectory(prefix='.api-baseline-',dir=REACT) as temp:
    work=Path(temp)
    with tarfile.open(fileobj=io.BytesIO(git('archive','--format=tar',BASE,'17_packages/react/src','17_packages/react/tsconfig.json'))) as archive:
        archive.extractall(work,filter='data')
    baseline=work/'17_packages/react'
    subprocess.run(['node',str(REACT/'node_modules/typescript/bin/tsc'),'-p',str(baseline/'tsconfig.json')],check=True,cwd=REACT)
    expected=declarations(baseline/'dist');actual=declarations(REACT/'dist')
    if not expected or expected!=actual:
        raise AssertionError('React declarations changed; review public API and update approved baseline intentionally: '+str(sorted(k for k in expected.keys()|actual.keys() if expected.get(k)!=actual.get(k))))
web={}
for path in ('17_packages/web-core/index.d.mts','17_packages/web-core/index.d.ts'):
    old=digest(git('show',BASE+':'+path));new=digest((ROOT/path).read_bytes())
    if old!=new:raise AssertionError('Web Core declaration changed: '+path)
    web[Path(path).name]=new
for name in ('react','web-core'):
    path=f'17_packages/{name}/package.json'
    old=json.loads(git('show',BASE+':'+path));new=json.loads((ROOT/path).read_text(encoding='utf-8'))
    for key in ('name','type','exports','types','peerDependencies','engines'):
        if old.get(key)!=new.get(key):raise AssertionError(f'Public package contract changed: {name}/{key}')
report={'baseline':BASE,'source':git('rev-parse','HEAD').decode().strip(),'reactDeclarations':actual,'webDeclarations':web,'policy':'Strict declaration equality; additions and breaking changes require review, not a full semantic compatibility proof.'}
(OUT/'api-contract.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(f'API contract: {len(actual)} React and {len(web)} Web declaration files match {BASE[:12]}')
