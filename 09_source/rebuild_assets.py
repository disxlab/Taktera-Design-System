#!/usr/bin/env python3
"""Re-export supplied SVG masters to PNG/ICO without any absolute paths.

Exports to a separate directory by default, so source assets stay byte-identical.
Dependencies: pip install cairosvg pillow; optional fonttools[brotli] for WOFF2.
"""
import argparse, io, struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PRODUCTS=('platform','clinic','beauty','spa','fitness','travel')
SIZES=(16,24,32,48,64,128,256,512,1024)
ICO_SIZES=(16,24,32,48,64,128,256)

def export(out):
    import cairosvg
    from PIL import Image
    targets=[]
    for src in (ROOT/'02_logos').rglob('*.svg'):
        rel=Path(src.relative_to(ROOT).as_posix().replace('/svg/','/png/')).with_suffix('.png')
        current=ROOT/rel
        if not current.exists(): raise FileNotFoundError('Original PNG required for export dimensions: '+str(rel))
        w,h=Image.open(current).size
        targets.append((src,rel,(w,h)))
    for src in (ROOT/'06_templates').glob('*.svg'):
        rel=src.relative_to(ROOT).with_suffix('.png')
        w,h=Image.open(ROOT/rel).size
        targets.append((src,rel,(w,h)))
    for p in PRODUCTS:
        for theme in ('light','dark'):
            for size in SIZES:
                source=ROOT/f'03_icons/app/{"micro/" if size in (16,24) else ""}svg/{p}-{theme}.svg'
                rel=Path(f'03_icons/app/png/{p}-{theme}-{size}.png')
                targets.append((source,rel,(size,size)))
    for src,rel,(w,h) in targets:
        dest=out/rel
        dest.parent.mkdir(parents=True,exist_ok=True)
        cairosvg.svg2png(url=str(src),write_to=str(dest),output_width=w,output_height=h)
    for p in PRODUCTS:
        for theme in ('light','dark'):
            blobs=[(out/f'03_icons/app/png/{p}-{theme}-{s}.png').read_bytes() for s in ICO_SIZES]
            offset=6+16*len(ICO_SIZES)
            entries=[]
            for size,blob in zip(ICO_SIZES,blobs):
                entries.append(struct.pack('<BBBBHHII',size%256,size%256,0,0,1,32,len(blob),offset));offset+=len(blob)
            dest=out/f'03_icons/app/{p}-{theme}.ico';dest.parent.mkdir(exist_ok=True,parents=True)
            dest.write_bytes(struct.pack('<HHH',0,1,len(ICO_SIZES))+b''.join(entries)+b''.join(blobs))
    print(f'Re-exported {len(targets)} PNG and {len(PRODUCTS)*2} ICO files to {out}. Source remains unchanged.')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,default=ROOT.parent/'Taktera_v3.3_reexports',help='Independent target directory; refuses to overwrite source package')
    a=ap.parse_args();out=a.output.resolve()
    if out==ROOT or ROOT in out.parents:raise SystemExit('Output MUST be outside the source package')
    export(out)
if __name__=='__main__':main()
