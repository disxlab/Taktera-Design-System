#!/usr/bin/env python3
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
root=Path(__file__).resolve().parents[1];folder=root/'16_quality/screenshots'
fontfile=root/'05_typography/Inter-SemiBold.ttf'
f=ImageFont.truetype(str(fontfile),18);big=ImageFont.truetype(str(fontfile),26)
products=['platform','clinic','beauty','spa','fitness','travel']
for theme in ['light','dark']:
 cardw,cardh=405,420
 sheet=Image.new('RGB',(3*cardw+48,2*cardh+108),'#F4F3EF')
 dr=ImageDraw.Draw(sheet)
 dr.text((24,15),f'Taktera v4.0 alpha · {theme} mode',font=big,fill='#22262B')
 dr.text((24,54),'Six real rendered UI scenarios · fictional data',font=f,fill='#62676E')
 for i,p in enumerate(products):
  src=Image.open(folder/f'{p}-{theme}.png').convert('RGB')
  src.thumbnail((cardw-20,cardh-38),Image.Resampling.LANCZOS)
  x=24+(i%3)*cardw;y=91+(i//3)*cardh
  dr.rounded_rectangle((x,y,x+cardw-13,y+cardh-11),radius=12,fill='#FFFFFF',outline='#D9DCDF',width=1)
  dr.text((x+14,y+10),p.capitalize(),font=f,fill='#22262B')
  sheet.paste(src,(x+7,y+39))
 sheet.save(folder/f'overview-{theme}-contact.png',optimize=True)
print('OK 2 overview contact sheets')
