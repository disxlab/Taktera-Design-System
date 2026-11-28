#!/usr/bin/env python3
"""Validate and package Taktera v3.3. Uses stdlib, Pillow, fonttools, and pypdf."""
from pathlib import Path
from html.parser import HTMLParser
from xml.etree import ElementTree as ET
from hashlib import sha256
import json, subprocess, sys, zipfile, re, tempfile
ROOT=Path(__file__).resolve().parents[1]
PRODUCTS=('platform','clinic','beauty','spa','fitness','travel')
class LinkParser(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        for key,val in attrs:
            if key in ('src','href') and val:self.links.append(val)

def main():
    from PIL import Image
    from pypdf import PdfReader
    from fontTools.ttLib import TTFont
    subprocess.run([sys.executable,str(ROOT/'09_source/generate_tokens.py'),'--check'],check=True)
    t=json.loads((ROOT/'04_tokens/taktera.tokens.json').read_text())
    assert t['version']=='3.3'
    assert t['products']['fitness']['accentLight']=='#D52B35'
    assert t['products']['travel']['accentLight']=='#D4A600'
    assert t['geometry']['path']=='M12 16H29Q49 16 49 36V58'
    assert t['products']['travel']['uiTextLight']=='#806300'
    checks={'version':'3.3','date':t['date'],'checks':{},'limitations':[]}
    for product in PRODUCTS:
        for theme in ('light','dark'):
            for rel in [f'02_logos/products/svg/{product}-{theme}.svg',f'02_logos/products/ru/svg/{product}-ru-{theme}.svg',f'03_icons/app/svg/{product}-{theme}.svg',f'03_icons/app/micro/svg/{product}-{theme}.svg']:
                f=ROOT/rel
                assert f.is_file(), rel
                ET.parse(f)
            for size in (16,24,32,48,64,128,256,512,1024):
                p=ROOT/f'03_icons/app/png/{product}-{theme}-{size}.png'
                assert Image.open(p).size==(size,size), p
            p=ROOT/f'03_icons/app/{product}-{theme}.ico'
            assert len(Image.open(p).ico.sizes())==7, p
    svgs=list(ROOT.rglob('*.svg'))
    for item in svgs:ET.parse(item)
    assert all('<text' not in f.read_text(encoding='utf-8') for f in (ROOT/'02_logos').rglob('*.svg'))
    checks['checks']['SVG']='Parsed all '+str(len(svgs))+' files; logo text remains outlined'
    checks['checks']['Icons']='12 theme/product combinations; 9 PNG sizes; 7 ICO layers'
    checks['checks']['Color contrast']=json.loads((ROOT/'10_documentation/COLOR-CONTRAST-v3.3.json').read_text())['tests']
    for f in sorted(ROOT.rglob('*.html')):
        parser=LinkParser();parser.feed(f.read_text(encoding='utf-8'))
        missing=[]
        for href in parser.links:
            if href.startswith(('#','https:','http:','data:','mailto:')):continue
            path=href.split('#')[0].split('?')[0]
            if path and not (f.parent/path).is_file() and not (f.parent==ROOT and path in ('VALIDATION.json','PACKAGE-MANIFEST.json')):missing.append(path)
        assert not missing,(f.relative_to(ROOT),missing)
    checks['checks']['HTML']='All local HTML src/href paths exist'
    for w in ['Regular','SemiBold','Bold']:
        f=TTFont(ROOT/f'05_typography/Inter-{w}.woff2')
        assert f.flavor=='woff2'
    assert (ROOT/'05_typography/OFL.txt').exists()
    checks['checks']['Typography']='3 WOFF2 fonts readable; OFL included'
    identity=json.loads((ROOT/'11_design_system/BRAND-ASSET-IDENTITY.json').read_text(encoding='utf-8'))
    assert identity['allUnchanged'] and identity['files']==245
    checks['checks']['Original asset compatibility']='245/245 original brand/graphics files are byte-identical'
    import shutil
    if shutil.which('node'):
        subprocess.run(['node',str(ROOT/'09_source/check_preview.cjs')],check=True)
        checks['checks']['Offline demo logic']='12 product/theme combinations and action handlers pass in Node (no browser)'
    else:checks['checks']['Offline demo logic']='Not tested: Node.js unavailable'
    pdf=PdfReader(ROOT/'01_brandbook/Taktera-brandbook-v3.2.pdf')
    assert len(pdf.pages)==14
    checks['checks']['Legacy brandbook']='v3.2, 14 pages; retained unchanged'
    addendum=ROOT/'11_design_system/Taktera-v3.3-implementation-guide.pdf'
    assert addendum.exists() and len(PdfReader(addendum).pages)>=3
    checks['checks']['Addendum PDF']=len(PdfReader(addendum).pages)
    checks['limitations']=['Legacy v3.2 production scripts are archived and still require adaptation for their original build environment; portable re-export script can recreate SVG-sourced PNG and ICO, not the vectorization of the reference raster.', 'Color contrast was validated for specified opaque token pairs, not full application screen WCAG conformance.', 'UI demonstration is static/offline prototype; no production application integration, native Avalonia controls, Figma, trademark or print prepress validation.', 'Brandbook v3.2 remains the normative baseline; v3.3 additions are a separate implementation guide.', 'Visual interactive-browser QA of the preview was not completed in this environment because Chromium navigation was blocked by administrator policy; verify using a normal local browser before integration.']
    (ROOT/'VALIDATION.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    files=sorted((p for p in ROOT.rglob('*') if p.is_file() and p.name!='PACKAGE-MANIFEST.json' and '__pycache__' not in p.parts and p.suffix!='.pyc'),key=lambda p:p.relative_to(ROOT).as_posix())
    manifest={'name':'Taktera Brand Package','version':'3.3','date':t['date'],'files':[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha256(p.read_bytes()).hexdigest()} for p in files]}
    (ROOT/'PACKAGE-MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    target=ROOT.parent/'Taktera_Brand_Package_v3.3.zip'
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(ROOT.rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':
                info=zipfile.ZipInfo(ROOT.name+'/'+p.relative_to(ROOT).as_posix(),date_time=(2026,11,22,0,0,0))
                info.compress_type=zipfile.ZIP_DEFLATED
                info.external_attr=(0o644 & 0xFFFF)<<16
                z.writestr(info,p.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        assert len(z.namelist())==len(files)+1
    print(json.dumps({'archive':str(target),'size':target.stat().st_size,'files':len(files)+1,'validation':checks['checks']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
