#!/usr/bin/env python3
"""Rebuild npm tarball, install it offline into a temporary clean consumer, verify the public ESM surface."""
from pathlib import Path
import json, os, shutil, subprocess, sys, tempfile
root=Path(__file__).resolve().parents[2]
core=root/'17_packages/web-core'
result={'version':'4.0-alpha.3','checks':[]}
def step(name,command,cwd,env=None):
    p=subprocess.run(command,cwd=cwd,text=True,capture_output=True,env=env,timeout=70)
    result['checks'].append({'name':name,'ok':p.returncode==0,'stdout':p.stdout[-450:],'stderr':p.stderr[-450:]})
    if p.returncode:raise RuntimeError(f'{name} failed: {p.stderr[-450:]}')
    return p
try:
    step('npm core source + strict TypeScript declarations', ['npm','test'],core)
    with tempfile.TemporaryDirectory(prefix='taktera-core-test-') as temp:
        p=Path(temp)
        report=step('npm pack offline', ['npm','pack','--json','--pack-destination',str(p),'--offline'],core)
        tar=p/json.loads(report.stdout)[0]['filename']
        consumer=p/'consumer';consumer.mkdir()
        (consumer/'package.json').write_text('{"name":"taktera-clean-consumer","private":true,"type":"module"}\n')
        env={**os.environ,'npm_config_cache':str(p/'npm-cache')}
        step('npm clean consumer install without registry', ['npm','install','--offline','--ignore-scripts','--no-audit','--no-fund',str(tar)],consumer,env)
        (consumer/'smoke.mjs').write_text("""import {PRODUCTS,THEMES,button,field,table} from '@taktera/ui-core';
if (PRODUCTS.length!==6||THEMES.length!==2||[button,field,table].some(x=>typeof x!=='function')) throw Error('ESM API mismatch');
console.log('Installed package API: 6 products, 2 themes, required functions');
""")
        step('Node ESM named import from installed package', ['node','smoke.mjs'],consumer)
    result['status']='PASS'
except Exception as error:
    result['status']='FAIL';result['error']=str(error)
out=root/'18_beta_readiness/qa/offline-package-check.json'
out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
print('Offline package verification:',result['status'],'/ steps',len(result['checks']))
sys.exit(0 if result['status']=='PASS' else 1)
