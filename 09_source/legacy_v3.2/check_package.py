from pathlib import Path
import json, re, hashlib, zipfile
from PIL import Image
from pypdf import PdfReader

root=Path('C:/Users/sgkomc/Documents/Persona/output/Taktera_Brand_Package_v3.2')
qa=Path('C:/Users/sgkomc/Documents/Persona/work/brand-v3.2/qa')
for p in ['platform','clinic','beauty','spa','fitness','travel']:
    for theme in ['light','dark']:
        im=Image.open(root/f'03_icons/app/png/{p}-{theme}-256.png')
        import struct
        sizes=[16,24,32,48,64,128,256]
        blobs=[(root/f'03_icons/app/png/{p}-{theme}-{s}.png').read_bytes() for s in sizes]
        offset=6+16*len(sizes); entries=[]
        for size,blob in zip(sizes,blobs):
            entries.append(struct.pack('<BBBBHHII',size%256,size%256,0,0,1,32,len(blob),offset));offset+=len(blob)
        (root/f'03_icons/app/{p}-{theme}.ico').write_bytes(struct.pack('<HHH',0,1,len(sizes))+b''.join(entries)+b''.join(blobs))

book=(root/'Taktera-brandbook-v3.2.html').read_text(encoding='utf-8')
links=re.findall(r'(?:src|href)="([^"]+)"',book)
missing=[x for x in links if not x.startswith(('#','http')) and not (root/x).exists()]
assert not missing,missing
tokens=json.loads((root/'04_tokens/taktera.tokens.json').read_text(encoding='utf-8'))
assert tokens['products']['fitness']['accentLight']=='#D52B35'
assert tokens['products']['travel']['accentLight']=='#D4A600'
assert tokens['products']['travel']['onAccentLight']=='#151719'
assert tokens['products']['travel']['uiTextLight']=='#806300'
assert list(tokens['localization']['ru'].values())==['платформа','клиника','красота','спа','фитнес','путешествия']
assert len(set(tokens['localization']['appCodes'].values()))==6
for product,code in tokens['localization']['appCodes'].items():
    for theme in ['light','dark']:
        icon=(root/f'03_icons/app/svg/{product}-{theme}.svg').read_text(encoding='utf-8')
        assert f' / {code}</title>' in icon and '<text' not in icon
        assert (root/f'02_logos/products/ru/svg/{product}-ru-{theme}.svg').exists()
        for size in [16,24,32,48,64,128,256,512,1024]:
            assert Image.open(root/f'03_icons/app/png/{product}-{theme}-{size}.png').size==(size,size)
        ico=Image.open(root/f'03_icons/app/{product}-{theme}.ico')
        assert len(ico.ico.sizes())==7
logos=list((root/'02_logos').rglob('*.svg'))
assert all('<text' not in p.read_text(encoding='utf-8') for p in logos),'Logo letters must be paths'
pngs=list((root/'02_logos').rglob('*.png'))
assert all(Image.open(p).mode=='RGBA' and Image.open(p).getextrema()[3][0]==0 for p in pngs),'Transparent PNG check'
layout=json.loads((qa/'layout-check.json').read_text())
assert not layout['images'] and not layout['errors']
assert all(p['contentBottom']+10<p['footerTop'] for p in layout['pages']),layout['pages']
pdf=PdfReader(root/'01_brandbook/Taktera-brandbook-v3.2.pdf')
assert len(pdf.pages)==14,len(pdf.pages)
assert all((p.extract_text() or '').strip() for p in pdf.pages),'Blank PDF page'
report={'date':'2026-10-18','pages':14,'htmlReferences':'all local links exist','svgLogoCount':len(logos),'pngLogoCount':len(pngs),'svgText':'all logo letters outlined','pngTransparency':'all logos contain alpha transparency','htmlImages':'all loaded','browserErrors':[],'layout':'all content clears footers by at least 10px','font':'local Inter loaded','mobile':'390px viewport without horizontal overflow','pdf':'14 non-empty pages; visual review rendered separately','reference':'final-selected-concept.png / exec-2c59ddad','limitations':['Optical vector reconstruction from raster, not an exact automatic trace','Application code unchanged','Trademark clearance not performed','Only documented color pairs tested']}
report['localization']='6 Russian product names; 12 RU SVG and PNG lockups'
report['appLabels']='PL CL BE SP FI TR; outlined labels; 16/24px micro variants; 7 ICO layers; PNG sizes verified'
(root/'VALIDATION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
files=[p for p in root.rglob('*') if p.is_file() and p.name!='PACKAGE-MANIFEST.json']
manifest={'name':'Taktera Brand Package','version':'3.2','date':'2026-10-18','files':[{'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)]}
(root/'PACKAGE-MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
archive=root.parent/(root.name+'.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in root.rglob('*'):
        if p.is_file(): z.write(p,p.relative_to(root.parent))
with zipfile.ZipFile(archive) as z: assert z.testzip() is None
print(json.dumps({'fileCount':len(files)+1,'archive':str(archive),'bytes':archive.stat().st_size,'validation':report},ensure_ascii=False))
