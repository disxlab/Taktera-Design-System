#!/usr/bin/env python3
"""Draft marketing background based on the approved bent-T curve. NOT a substitute for the logo."""
from pathlib import Path
import json
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
t=json.loads((ROOT/'04_tokens/taktera.tokens.json').read_text('utf8'))
out=Path(__file__).resolve().parent/'signature_patterns';out.mkdir(exist_ok=True)
path=t['geometry']['path']
for p,e in t['products'].items():
 for theme in ['light','dark']:
  bg=t['neutral']['canvas' if theme=='light' else 'darkCanvas'];base='#000000' if theme=='light' else '#FFFFFF'
  accent=e['accentLight' if theme=='light' else 'accentDark'];style='0.09' if theme=='light' else '0.12'
  svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630" role="img" aria-label="Experimental Taktera {p} Signature Pattern {theme}">
 <rect width="1200" height="630" fill="{bg}"/>
 <g opacity="{style}" stroke="{base}" stroke-linecap="round" stroke-linejoin="round" fill="none" stroke-width="20">
   <path d="{path}" transform="translate(615 -190) scale(9)"/>
   <path d="{path}" transform="translate(115 325) scale(5)"/>
 </g>
 <circle cx="1010" cy="163" r="39" fill="{accent}" opacity="0.42"/>
 <circle cx="368" cy="570" r="20" fill="{accent}" opacity="0.31"/>
 </svg>'''
  ET.fromstring(svg);(out/f'signature-{p}-{theme}.svg').write_text(svg,encoding='utf8')
print('OK: 12 experimental Signature backgrounds')
