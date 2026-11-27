#!/usr/bin/env python3
"""Taktera deterministic Chromium visual-regression runner.
Usage: python visual_regression.py capture --out /tmp/current
       python visual_regression.py compare --reference ../25_internal_completion/qa/baselines --out /tmp/report
       python visual_regression.py selftest --out /tmp/check
No network; Chromium + playwright + Pillow + numpy.
"""
from __future__ import annotations
import argparse, hashlib, html, json, os, re, sys, time
from pathlib import Path
from io import BytesIO
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/'25_internal_completion'
BASELINE=MODULE/'qa'/'baselines'
PRODUCTS=('platform','clinic','beauty','spa','fitness','travel')
THEMES=('light','dark')
DENSITIES=('comfortable','compact')
LOCALES=('ru-RU','en-US')

def matrix():
    for product in PRODUCTS:
        for theme in THEMES:
            for density in DENSITIES:
                for locale in LOCALES:
                    yield {'product':product,'theme':theme,'density':density,'locale':locale,
                           'id':f'{product}-{theme}-{density}-{locale[:2]}'}

def page_source():
    document=(MODULE/'index.html').read_text(encoding='utf-8')
    old=(ROOT/'04_tokens/taktera.tokens.css').read_text(encoding='utf-8')
    generated=(MODULE/'generated/tokens.web.css').read_text(encoding='utf-8')
    fmt=(MODULE/'src/formatters.mjs').read_text(encoding='utf-8')
    document=document.replace('<link rel="stylesheet" href="../04_tokens/taktera.tokens.css">',f'<style>{old}</style>')
    document=document.replace('<link rel="stylesheet" href="generated/tokens.web.css">',f'<style>{generated}</style>')
    document=document.replace("import {formatDate,formatCurrency,formatPercent,pluralize,t} from './src/formatters.mjs';",fmt.replace('export const ','const ').replace('export function ','function '))
    document=document.replace('<script type="module">','<script>')
    assert '<link rel="stylesheet"' not in document and 'import {formatDate' not in document
    return document

def capture(out:Path, intentional_css:str='', only=None):
    out.mkdir(parents=True,exist_ok=True)
    document=page_source()
    if intentional_css:
        document=document.replace('</head>',f'<style>{intentional_css}</style></head>')
    results=[]; faults=[]
    with sync_playwright() as pl:
        browser=pl.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':1280,'height':840},device_scale_factor=1,reduced_motion='reduce',locale='ru-RU',timezone_id='UTC')
        page.on('pageerror',lambda e:faults.append(str(e)))
        page.set_content(document,wait_until='load')
        page.evaluate('document.fonts.ready')
        for item in matrix():
            if only and item['id'] not in only: continue
            for field in ('product','theme','density','locale'):
                page.select_option('#'+field,item[field])
            # No animations and no asynchronous page data; freeze at a fixed render state.
            page.evaluate('document.fonts.ready')
            page.screenshot(path=str(out/(item['id']+'.png')),full_page=True,animations='disabled')
            state=page.evaluate("""() => ({lang:document.documentElement.lang, theme:document.body.dataset.theme,product:document.body.dataset.product,density:document.body.dataset.density,row:getComputedStyle(document.body).getPropertyValue('--tkn-row-height').trim(),overflow:document.documentElement.scrollWidth>innerWidth})""")
            if state['overflow'] or state['row']!=('36px' if item['density']=='compact' else '44px'):
                faults.append(f"Incorrect layout state {item['id']}: {state}")
            results.append({'id':item['id'],**state})
        browser.close()
    if faults:raise RuntimeError('; '.join(faults[:4]))
    (out/'capture-manifest.json').write_text(json.dumps({'browser':'Chromium','viewport':[1280,840],'deviceScaleFactor':1,'configs':results,'captureCount':len(results)},ensure_ascii=False,indent=2),encoding='utf-8')
    return results

def compare(reference:Path,current:Path,out:Path,threshold:float=0.005,delta:int=16):
    """Fail when > threshold fraction pixels differ by > delta in any RGB channel."""
    out.mkdir(parents=True,exist_ok=True)
    (out/'diffs').mkdir(exist_ok=True)
    rows=[]
    for x in matrix():
        key=x['id']; rp=reference/(key+'.png');cp=current/(key+'.png')
        result={'id':key,'status':'missing','changed_ratio':None,'max_channel_delta':None,'reference':str(rp),'current':str(cp)}
        if rp.is_file() and cp.is_file():
            a=np.array(Image.open(rp).convert('RGB'),dtype=np.int16)
            b=np.array(Image.open(cp).convert('RGB'),dtype=np.int16)
            result['reference_size']=[int(a.shape[1]),int(a.shape[0])]
            result['current_size']=[int(b.shape[1]),int(b.shape[0])]
            if a.shape!=b.shape:
                result['status']='dimension_mismatch'
                result['changed_ratio']=1.0
            else:
                distance=np.abs(a-b)
                mask=np.max(distance,axis=2)>delta
                ratio=float(mask.mean())
                result['changed_ratio']=round(ratio,8)
                result['max_channel_delta']=int(distance.max())
                result['status']='pass' if ratio<=threshold else 'fail'
                if mask.any():
                    # Visible diff: red for mismatched pixels; pale grayscale unchanged.
                    under=(a.astype(np.float32)*0.22+230*0.78).clip(0,255).astype(np.uint8)
                    under[mask]=[222,54,64]
                    Image.fromarray(under).save(out/'diffs'/(key+'.png'))
        rows.append(result)
    failures=[r for r in rows if r['status']!='pass']
    summary={'tool':'Taktera visual regression','browser':'Chromium','matrixCount':len(rows),'passed':len(rows)-len(failures),'failed':len(failures),'threshold':threshold,'channelDelta':delta,'status':'pass' if not failures else 'fail','results':rows}
    (out/'report.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    # HTML references absolute local file paths; open report from disk, same machine.
    cards=[]
    for row in rows:
        ref=os.path.relpath(row['reference'],out) if Path(row['reference']).is_file() else ''
        cur=os.path.relpath(row['current'],out) if Path(row['current']).is_file() else ''
        dif='diffs/'+row['id']+'.png' if (out/'diffs'/(row['id']+'.png')).is_file() else ''
        images=''.join(f'<figure><img loading="lazy" src="{url}"><figcaption>{lab}</figcaption></figure>' for lab,url in [('Эталон',ref),('Текущий',cur),('Разница',dif)] if url)
        cards.append(f'<article class="card"><h3>{html.escape(row["id"])} <span class="{row["status"]}">{row["status"]}</span></h3><p>Изменённых пикселей: {row["changed_ratio"] if row["changed_ratio"] is not None else "н/д"}</p><div class="images">{images}</div></article>')
    page="""<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Taktera Visual Regression</title><style>body{margin:0;background:#101318;color:#e9edf4;font:14px system-ui}header{position:sticky;top:0;background:#1e2430;padding:18px 24px;z-index:2}main{padding:24px;display:grid;gap:12px}.card{background:#1a2029;border:1px solid #414c5d;border-radius:12px;padding:14px}.card h3{margin:0}.images{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}figure{margin:0}img{display:block;width:100%;object-fit:contain;max-height:420px;background:#eee}figcaption{padding:6px}.pass{color:#79d5a3}.fail,.missing,.dimension_mismatch{color:#ff9090}@media(max-width:720px){.images{grid-template-columns:1fr}}</style><header><h1>Taktera — визуальная регрессия</h1><p>"""+f'{summary["passed"]}/{summary["matrixCount"]} пройдено · порог {threshold*100:.2f}% · отклонение RGB более {delta}</p></header><main>'+''.join(cards)+'</main></html>'
    (out/'report.html').write_text(page,encoding='utf-8')
    return summary

def main():
    p=argparse.ArgumentParser()
    p.add_argument('command',choices=('capture','compare','selftest'))
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--reference',type=Path,default=BASELINE)
    p.add_argument('--threshold',type=float,default=0.005)
    p.add_argument('--delta',type=int,default=16)
    args=p.parse_args()
    if not 0<=args.threshold<=1 or not 0<=args.delta<=255:p.error('Invalid thresholds')
    if args.command=='capture':
        rows=capture(args.out)
        print(f'Captured {len(rows)} configurations to {args.out}')
        return 0
    if args.command=='compare':
        current=args.out/'current'
        capture(current)
        result=compare(args.reference,current,args.out,args.threshold,args.delta)
        print(json.dumps({k:v for k,v in result.items() if k!='results'},ensure_ascii=False))
        return 0 if result['status']=='pass' else 1
    if args.command=='selftest':
        pos=args.out/'positive'; neg=args.out/'negative'
        capture(pos/'current')
        passed=compare(args.reference,pos/'current',pos,args.threshold,args.delta)
        # Intentional visible regression. Must be detected (not ignored).
        capture(neg/'current',intentional_css='.card{background:#ff00ff!important}',only={'clinic-light-comfortable-ru'})
        # Compare single scenario separately, so ungenerated scenarios do not inflate failures.
        ref=Image.open(args.reference/'clinic-light-comfortable-ru.png').convert('RGB')
        cur=Image.open(neg/'current'/'clinic-light-comfortable-ru.png').convert('RGB')
        a=np.array(ref,dtype=np.int16);b=np.array(cur,dtype=np.int16)
        ratio=float((np.max(np.abs(a-b),axis=2)>args.delta).mean()) if a.shape==b.shape else 1.0
        caught=ratio>args.threshold
        result={'positive':{'passed':passed['passed'],'failed':passed['failed']},'negative':{'changed_ratio':ratio,'regression_detected':caught},'status':'pass' if not passed['failed'] and caught else 'fail'}
        (args.out/'selftest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(result,ensure_ascii=False))
        return 0 if result['status']=='pass' else 1

if __name__=='__main__':sys.exit(main())
