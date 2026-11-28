#!/usr/bin/env python3
"""Validate and package Taktera v4.0 alpha.1. Canonical brand asset freeze and offline UI QA."""
from pathlib import Path
from hashlib import sha256
from html.parser import HTMLParser
from xml.etree import ElementTree as ET
import json, zipfile, subprocess, sys, re
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[]
 def handle_starttag(self,tag,attrs):
  for k,v in attrs:
   if k in ('src','href') and v:self.links.append(v)
def main():
 subprocess.run([sys.executable,str(ROOT/'09_source/generate_tokens.py'),'--check'],check=True)
 subprocess.run([sys.executable,str(ROOT/'15_platform_adapters/generate_avalonia.py'),'--check'],check=True)
 if subprocess.run(['node','--version'],capture_output=True).returncode==0:
  for f in ['13_ui_kit/ui.js','13_ui_kit/data.js']:
   subprocess.run(['node','--check',str(ROOT/f)],check=True)
 checks={}
 freeze=json.loads((ROOT/'16_quality/BRAND-FREEZE-v3.3.json').read_text(encoding='utf8'))
 for entry in freeze['files']:
  f=ROOT/entry['path'];assert f.exists() and f.stat().st_size==entry['bytes'] and sha256(f.read_bytes()).hexdigest()==entry['sha256'],entry['path']
 assert len(freeze['files'])==248
 checks['Original brand files']='248/248 original v3.3 frozen assets byte-identical'
 original_token=json.loads((ROOT/'04_tokens/taktera.tokens.json').read_text('utf8'))
 assert original_token['version']=='3.3' and original_token['geometry']['path']=='M12 16H29Q49 16 49 36V58'
 checks['Tokens']='v3.3 compiler generated CSS, DTCG and contrast pairs unchanged'
 q=json.loads((ROOT/'16_quality/browser-qa.json').read_text('utf8'))
 assert len(q['checks'])>=42 and all(e['pass'] for e in q['checks']) and not q['page_errors'] and not q['console_errors']
 checks['Browser QA']=f"{len(q['checks'])}/{len(q['checks'])} browser assertions passed with inlined local assets"
 svgfiles=list(ROOT.rglob('*.svg'))
 for f in svgfiles:ET.parse(f)
 checks['SVG']=f'{len(svgfiles)} XML parse successes'
 iconbase=ROOT/'14_brand_extensions/icons_proposed'
 assert len(list((iconbase/'svg').glob('*.svg')))==48
 pngs=list((iconbase/'png').glob('*.png'));assert len(pngs)==144
 for f in pngs:
  size=int(f.stem.rsplit('-',1)[1]);im=Image.open(f);assert im.size==(size,size),str(f)
 checks['Icon proposals']='48 SVG / 144 PNG correct dimensions; isolated from approved masters'
 for p in ['platform','clinic','beauty','spa','fitness','travel']:
  for t in ['light','dark']:
   assert (ROOT/f'16_quality/screenshots/{p}-{t}.png').exists()
   assert (ROOT/f'15_platform_adapters/avalonia/Taktera.{p.capitalize()}.{t.capitalize()}.axaml').exists()
 assert len(list((ROOT/'14_brand_extensions/signature_patterns').glob('*.svg')))==12
 checks['Industry illustrations']='12 screenshot combinations, 12 Signature patterns, 12 Avalonia token dictionaries'
 html_count=0
 for f in ROOT.rglob('*.html'):
  html_count+=1;parser=Links();parser.feed(f.read_text('utf8'))
  for href in parser.links:
   if href.startswith(('#','http:','https:','data:','mailto:','javascript:')):continue
   local=href.split('?')[0].split('#')[0]
   if local:assert (f.parent/local).is_file(),f'{f.relative_to(ROOT)} -> missing {href}'
 checks['HTML']=f'{html_count} HTML files, all local linked assets present'
 report={'version':'4.0-alpha.1','date':'2026-11-22','status':'Design-system engineering alpha only, not stable product release','checks':checks,'limitations':['Web browser evaluation injected same local CSS/JS into about:blank due to administrator navigation restrictions. Normal file:// smoke test still required.','Not production React/Avalonia component controls.','New icon/pattern assets remain unapproved candidates.','Brandbook v3.2 and engineer addendum v3.3 remain canonical and unchanged.','No formal WCAG 2.2 certification, screen reader or OS high contrast audit.']}
 (ROOT/'VALIDATION-ALPHA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 files=sorted((p for p in ROOT.rglob('*') if p.is_file() and p.name!='PACKAGE-MANIFEST-ALPHA.json' and '__pycache__' not in p.parts and p.suffix!='.pyc'),key=lambda p:p.relative_to(ROOT).as_posix())
 manifest={'name':'Taktera Design System','version':'4.0-alpha.1','files':[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha256(p.read_bytes()).hexdigest()} for p in files]}
 (ROOT/'PACKAGE-MANIFEST-ALPHA.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 dest=ROOT.parent/(ROOT.name+'.zip')
 with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in sorted(ROOT.rglob('*')):
   if not p.is_file() or '__pycache__' in p.parts or p.suffix=='.pyc':continue
   name=ROOT.name+'/'+p.relative_to(ROOT).as_posix();info=zipfile.ZipInfo(name,date_time=(2026,11,22,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=(0o644 & 0xffff)<<16
   z.writestr(info,p.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
 with zipfile.ZipFile(dest) as z:
  assert z.testzip() is None
  assert len(z.namelist())==len(files)+1
 print(json.dumps({'archive':str(dest),'bytes':dest.stat().st_size,'file_count':len(files)+1,'checks':checks},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
