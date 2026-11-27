#!/usr/bin/env python3
"""Portable token compiler (stdlib-only): legacy JSON -> CSS, DTCG, WCAG report."""
import argparse, json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'04_tokens/taktera.tokens.json'
CSS = ROOT/'04_tokens/taktera.tokens.css'
DTCG = ROOT/'04_tokens/taktera.tokens.dtcg.json'
REPORT = ROOT/'10_documentation/COLOR-CONTRAST-v3.3.json'

def rgb(value):
    assert re.fullmatch(r'#[0-9A-Fa-f]{6}', value), value
    return [int(value[i:i+2],16) for i in (1,3,5)]

def luminance(value):
    c = [v/255 for v in rgb(value)]
    return sum((v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4)*weight for v,weight in zip(c,(.2126,.7152,.0722)))

def contrast(a,b):
    x,y=sorted((luminance(a),luminance(b)),reverse=True)
    return round((x+.05)/(y+.05),3)

def mix(hex1,hex2,pct):
    a,b=rgb(hex1),rgb(hex2);q=pct/100
    return '#'+''.join(f'{round(x*(1-q)+y*q):02X}' for x,y in zip(a,b))

def css_declarations(mapping):
    return ' '.join(f'--tk-{k}:{v};' for k,v in mapping.items())

def token_color(value, description=''):
    d={'$type':'color','$value':{'colorSpace':'srgb','components':[round(v/255,8) for v in rgb(value)],'hex':value}}
    if description:d['$description']=description
    return d

def build():
    t=json.loads(SOURCE.read_text(encoding='utf-8'))
    p=t['products']; n=t['neutral'];s=t['semantic']
    assert set(p)==set(t['localization']['ru'])=={'platform','clinic','beauty','spa','fitness','travel'}
    roots={
      'light':{'mark':n['markLight'],'canvas':n['canvas'],'surface':n['surface'],'text':n['ink'],'muted':n['mutedLight'],'border':n['borderLight'],'control-border':n['controlBorderLight'],'disabled-bg':n['disabledBgLight'],'disabled-text':n['disabledFgLight']},
      'dark':{'mark':n['markDark'],'canvas':n['darkCanvas'],'surface':n['surfaceDark'],'text':n['textDark'],'muted':n['mutedDark'],'border':n['borderDark'],'control-border':n['controlBorderDark'],'disabled-bg':n['disabledBgDark'],'disabled-text':n['disabledFgDark']}}
    def productmap(product, theme):
        entry=p[product];is_light=theme=='light';suffix='Light' if is_light else 'Dark'
        accent=entry['accent'+suffix];on=entry['onAccent'+suffix]
        tcolor=entry['uiText'+suffix]
        paper=entry.get('uiTextCanvasLight',tcolor) if is_light else tcolor
        return {'accent':accent,'on-accent':on,'accent-text':tcolor,'accent-text-canvas':paper,
                'accent-hover':mix(accent,t['ui']['states']['primaryHoverMix'][theme]['with'],t['ui']['states']['primaryHoverMix'][theme]['percent']),
                'accent-pressed':mix(accent,t['ui']['states']['primaryPressedMix'][theme]['with'],t['ui']['states']['primaryPressedMix'][theme]['percent']),
                'focus-ring':paper if is_light else tcolor}
    def semmap(theme):
        out={}
        for key,val in s[theme].items():
            out['status-'+key+'-text']=val['foreground'];out['status-'+key+'-bg']=val['background']
        return out
    lines=['/* Taktera v3.3. GENERATED: python 09_source/generate_tokens.py. Do not hand edit. */',
           '/* --tk-border is decorative; use --tk-control-border for essential boundaries. */',
           ':root { '+css_declarations({**roots['light'],**productmap('platform','light'),**semmap('light'),
            'font':'Inter,"Segoe UI",Arial,sans-serif','space-unit':'4px','radius-xs':'4px',
            'radius-sm':'6px','radius-md':'8px','radius-lg':'12px','radius-xl':'16px',
            'motion-fast':'150ms','motion-base':'250ms','motion-slow':'400ms'})+' }',
           '[data-theme="dark"] { '+css_declarations({**roots['dark'],**productmap('platform','dark'),**semmap('dark')})+' }']
    for product in p:
        if product=='platform':
            # still emit platform selectors for scoped elements nested under another product
            pass
        light=f'[data-product="{product}"]'
        dark=f'[data-theme="dark"][data-product="{product}"], [data-theme="dark"] [data-product="{product}"], [data-product="{product}"] [data-theme="dark"]'
        lines.append(light+' { '+css_declarations(productmap(product,'light'))+' }')
        lines.append(dark+' { '+css_declarations(productmap(product,'dark'))+' }')
    lines += ['/* Brand colors are never used as semantic error/success colors. */',
      '.tk-brand-mark { color:var(--tk-mark); }',
      '.tk-brand-dot, .tk-product-name { color:var(--tk-accent); }',
      '.tk-primary { background:var(--tk-accent);color:var(--tk-on-accent); }',
      '.tk-accent-text { color:var(--tk-accent-text); }',
      '.tk-accent-text-on-canvas { color:var(--tk-accent-text-canvas); }',
      '.tk-focus:focus-visible { outline:3px solid var(--tk-focus-ring);outline-offset:3px; }',
      '@media (prefers-reduced-motion:reduce) { :root { --tk-motion-fast:0ms;--tk-motion-base:0ms;--tk-motion-slow:0ms; } }']
    css='\n'.join(lines)+'\n'
    dtcg={'$schema':'https://www.designtokens.org/schemas/2025.10/format.json','$description':'Taktera v3.3 derived from taktera.tokens.json. Brand colors and UI semantic roles are separate.',
           'brand': {'color':{}},'semantic':{'color':{}},'foundation':{'color':{}}}
    for product in p:
        dtcg['brand']['color'][product]={}
        for theme in ('light','dark'):
            dtcg['brand']['color'][product][theme]={k:token_color(v) for k,v in productmap(product,theme).items()}
    for theme in ('light','dark'):
        dtcg['semantic']['color'][theme]={status: {role:token_color(value) for role,value in attrs.items()} for status,attrs in s[theme].items()}
        dtcg['foundation']['color'][theme]={k:token_color(v) for k,v in roots[theme].items()}
    dtcg['foundation']['dimension']={str(r):{'$type':'dimension','$value':{'value':r,'unit':'px'}} for r in t['ui']['radii']}
    results=[]
    def record(group,theme,product,role,a,b,limit):
        value=contrast(a,b)
        results.append({'group':group,'theme':theme,'product':product,'role':role,'foreground':a,'background':b,'ratio':value,'minimum':limit,'pass':value>=limit})
    for theme in ('light','dark'):
        root=roots[theme]
        for product in p:
            pm=productmap(product,theme)
            record('button',theme,product,'primary-default',pm['on-accent'],pm['accent'],4.5)
            record('button',theme,product,'primary-hover',pm['on-accent'],pm['accent-hover'],4.5)
            record('button',theme,product,'primary-pressed',pm['on-accent'],pm['accent-pressed'],4.5)
            for bg in ['canvas','surface']:
                record('text',theme,product,'accent-text-'+bg,pm['accent-text-canvas'] if bg=='canvas' else pm['accent-text'],root[bg],4.5)
        for bg in ['canvas','surface']:
            record('border',theme,None,'control-'+bg,root['control-border'],root[bg],3)
            record('text',theme,None,'body-'+bg,root['text'],root[bg],4.5)
        for status,attrs in s[theme].items():
            record('status',theme,None,status,attrs['foreground'],attrs['background'],4.5)
    failures=[x for x in results if not x['pass']]
    if failures:raise ValueError('Contrast checks failed: '+json.dumps(failures,ensure_ascii=False,indent=2))
    report={'version':'3.3','method':'WCAG 2.2 sRGB relative luminance; test only these solid opaque pairs','status':'all proposed token pairs pass automated thresholds','tests':len(results),'failed':len(failures),'results':results,'limitations':['Contrast alone does not establish WCAG conformance','Disabled controls are excluded from contrast acceptance testing','Real screens, component borders, focus visibility and text scaling require visual/functional QA','No automatic approval of any particular product UI']}
    return {CSS:css,DTCG:json.dumps(dtcg,ensure_ascii=False,indent=2)+'\n',REPORT:json.dumps(report,ensure_ascii=False,indent=2)+'\n'}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true',help='Compare generated artifacts to committed files')
    args=parser.parse_args()
    outputs=build()
    for path,content in outputs.items():
        if args.check:
            if not path.exists() or path.read_text(encoding='utf-8')!=content:
                raise SystemExit('OUT OF DATE: '+str(path.relative_to(ROOT)))
        else:path.write_text(content,encoding='utf-8')
    print(f'OK: {"up-to-date" if args.check else "generated"} 3 artifacts; 6 products × 2 themes; 0 contrast failures')
if __name__=='__main__':main()
