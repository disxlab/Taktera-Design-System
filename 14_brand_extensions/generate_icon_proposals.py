#!/usr/bin/env python3
"""Generate two UNAPPROVED application icon proposals from canonical geometry and the preserved palette."""
from pathlib import Path
import sys,json,io
from xml.etree import ElementTree as ET
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from PIL import Image,ImageDraw,ImageFont
import cairosvg
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'04_tokens/taktera.tokens.json'
OUT=Path(__file__).resolve().parent/'icons_proposed'
t=json.loads(SRC.read_text(encoding='utf8'))
font=TTFont(ROOT/'05_typography/Inter-Bold.ttf')
gset=font.getGlyphSet(); cmap=font.getBestCmap();hmtx=font['hmtx'].metrics; upem=font['head'].unitsPerEm
PATH=t['geometry']['path'];stroke=t['geometry']['strokeWidth']
def glyphs(txt,x,y,size,color):
 scale=size/upem
 width=sum(hmtx[cmap[ord(c)]][0] for c in txt)*scale
 at=x-width/2
 parts=[]
 for ch in txt:
  gn=cmap[ord(ch)];pen=SVGPathPen(gset);gset[gn].draw(pen);d=pen.getCommands()
  parts.append(f'<path d="{d}" transform="translate({at:.3f} {y:.3f}) scale({scale:.6f} {-scale:.6f})" fill="{color}"/>')
  at+=hmtx[gn][0]*scale
 return ''.join(parts)
def svg(product,theme,concept,micro=False):
 p=t['products'][product];accent=p['accentLight' if theme=='light' else 'accentDark'];fg=t['neutral']['markLight' if theme=='light' else 'markDark'];on=p['onAccentLight' if theme=='light' else 'onAccentDark'];bg=t['neutral']['canvas' if theme=='light' else 'darkCanvas'];code=t['localization']['appCodes'][product]
 prefix=f'<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Taktera {product} proposed icon {concept} {theme}" width="128" height="128" viewBox="0 0 128 128"><defs><clipPath id="r"><rect width="128" height="128" rx="28"/></clipPath></defs><g clip-path="url(#r)"><rect width="128" height="128" fill="{bg}"/>'
 if micro:
  # No letterforms at 16/24; use a clear bottom accent line (separately proposed variation).
  prefix+=f'<rect y="121" width="128" height="7" fill="{accent}"/><g transform="translate(16 19) scale(1.12)"><path d="{PATH}" stroke="{fg}" stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round" fill="none"/><circle cx="75" cy="15" r="10" fill="{accent}"/></g>'
 elif concept=='A':
  prefix+=f'<rect x="0" y="93" width="128" height="35" fill="{accent}"/><g transform="translate(17 15) scale(.98)"><path d="{PATH}" stroke="{fg}" stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round" fill="none"/><circle cx="75" cy="15" r="10" fill="{accent}"/></g>'
  prefix+=glyphs(code,64,120,23,on)
 else:
  prefix+=f'<rect x="0" width="7" height="128" fill="{accent}"/><g transform="translate(15 19) scale(.8)"><path d="{PATH}" stroke="{fg}" stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round" fill="none"/><circle cx="75" cy="15" r="10" fill="{accent}"/></g>'
  prefix+=f'<rect x="67" y="68" width="48" height="38" rx="9" fill="{accent}"/>'
  prefix+=glyphs(code,91,96,21,on)
 return prefix+'</g></svg>'

def render():
 svgdir=OUT/'svg';png=OUT/'png';svgdir.mkdir(exist_ok=True,parents=True);png.mkdir(exist_ok=True)
 for product in t['products']:
  for theme in ('light','dark'):
   for concept in ('A','B'):
    for micro in (False,True):
     basename=f'{product}-{theme}-{concept}'+('-micro' if micro else '')
     markup=svg(product,theme,concept,micro)
     (svgdir/(basename+'.svg')).write_text(markup,encoding='utf8');ET.fromstring(markup)
    for size in (16,24,32,64,128,256):
     usemicro=size<=24
     source=(svgdir/f'{product}-{theme}-{concept}'+('-micro' if usemicro else '')+'.svg').read_bytes() if False else (svgdir/(f'{product}-{theme}-{concept}'+('-micro' if usemicro else '')+'.svg')).read_bytes()
     output=cairosvg.svg2png(bytestring=source,output_width=size,output_height=size)
     (png/f'{product}-{theme}-{concept}-{size}.png').write_bytes(output)
 # Build a clear visual comparison for approval; show original v3.3 + proposal A/B.
 from PIL import ImageOps
 cardw=225;cardh=168;left=150;w=left+cardw*6;h=96+6*cardh
 contact=Image.new('RGB',(w,h),'#F4F3EF');d=ImageDraw.Draw(contact)
 fpath=str(ROOT/'05_typography/Inter-SemiBold.ttf')
 big=ImageFont.truetype(fpath,20);small=ImageFont.truetype(fpath,14)
 d.text((25,20),'Taktera · candidate app icons',font=big,fill='#22262B');d.text((25,52),'Original v3.3 → A: label band → B: code chip (unapproved)',font=small,fill='#555A62')
 for j,concept in enumerate(['original-light','A-light','B-light','original-dark','A-dark','B-dark']):d.text((left+j*cardw+16,87),concept,font=small,fill='#555A62')
 for i,product in enumerate(t['products']):
  y=115+i*cardh;d.text((23,y+45),product.capitalize(),font=big,fill='#22262B')
  for j,(kind,theme) in enumerate([('original','light'),('A','light'),('B','light'),('original','dark'),('A','dark'),('B','dark')]):
   x=left+j*cardw+20
   original=ROOT/f'03_icons/app/png/{product}-{theme}-128.png';candidate=png/f'{product}-{theme}-{kind}-128.png';filename=original if kind=='original' else candidate
   im=Image.open(filename).convert('RGBA')
   contact.paste(im,(x,y),im)
 contact.save(OUT/'icon-comparison.png')
 print('icon candidates: 48 SVG + 144 PNG + comparison', (OUT/'icon-comparison.png'))
if __name__=='__main__':render()
