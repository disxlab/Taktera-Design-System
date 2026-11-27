#!/usr/bin/env python3
"""Generate 12 Avalonia color/brush resource dictionaries from the canonical JSON tokens.
IMPORTANT: resources are a starting point, not a tested control theme."""
from pathlib import Path
import json,sys,argparse,re
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'04_tokens/taktera.tokens.json').read_text(encoding='utf8'))
OUT=Path(__file__).resolve().parent/'avalonia'
D=DATA

def mix(x,y,p):
 a=[int(x[i:i+2],16) for i in (1,3,5)];b=[int(y[i:i+2],16) for i in (1,3,5)];return '#'+''.join(f'{round(n*(1-p/100)+m*p/100):02X}' for n,m in zip(a,b))
def values(p,theme):
 n=D['neutral'];a=D['products'][p];s=D['semantic'][theme];l=theme=='light';tail='Light' if l else 'Dark'
 accent=a['accent'+tail];on=a['onAccent'+tail];t=a['uiText'+tail];paper=a.get('uiTextCanvasLight',t) if l else t
 v={
 'Mark':n['markLight' if l else 'markDark'],'Canvas':n['canvas' if l else 'darkCanvas'],'Surface':n['surface' if l else 'surfaceDark'],'Text':n['ink' if l else 'textDark'],
 'Muted':n['mutedLight' if l else 'mutedDark'],'Border':n['borderLight' if l else 'borderDark'],'ControlBorder':n['controlBorderLight' if l else 'controlBorderDark'],
 'DisabledBg':n['disabledBgLight' if l else 'disabledBgDark'],'DisabledText':n['disabledFgLight' if l else 'disabledFgDark'],
 'Accent':accent,'OnAccent':on,'AccentText':t,'AccentTextCanvas':paper,
 'AccentHover':mix(accent,D['ui']['states']['primaryHoverMix'][theme]['with'],D['ui']['states']['primaryHoverMix'][theme]['percent']),
 'AccentPressed':mix(accent,D['ui']['states']['primaryPressedMix'][theme]['with'],D['ui']['states']['primaryPressedMix'][theme]['percent']),
 'FocusRing':paper if l else t}
 for status,attrs in s.items():
  v['Status'+status.capitalize()+'Text']=attrs['foreground'];v['Status'+status.capitalize()+'Bg']=attrs['background']
 return v

def content(p,theme):
 v=values(p,theme)
 lines=['<?xml version="1.0" encoding="utf-8"?>',
 '<!-- Generated from v3.3 canonical JSON. Do not hand-edit; not a full Avalonia control theme. -->',
 '<ResourceDictionary xmlns="https://github.com/avaloniaui" xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">']
 for k,val in v.items():lines.append(f'  <Color x:Key="Tk{k}Color">{val}</Color>')
 for k,val in v.items():lines.append(f'  <SolidColorBrush x:Key="Tk{k}Brush" Color="{val}"/>')
 lines.append('</ResourceDictionary>');return '\n'.join(lines)+'\n'

def main():
 a=argparse.ArgumentParser();a.add_argument('--check',action='store_true');args=a.parse_args();OUT.mkdir(parents=True,exist_ok=True)
 for p in D['products']:
  for theme in ('light','dark'):
   dest=OUT/f'Taktera.{p.capitalize()}.{theme.capitalize()}.axaml';src=content(p,theme)
   if args.check:
    if not dest.exists() or dest.read_text(encoding='utf8')!=src:raise ValueError('outdated '+str(dest))
   else:dest.write_text(src,encoding='utf8')
   ET.fromstring(src)
 print('OK Avalonia token dictionaries: 12 variations / 6 products / 2 themes')
if __name__=='__main__':main()
