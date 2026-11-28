#!/usr/bin/env python3
"""Optional: generate v3.3 addendum HTML and PDF from maintained Markdown chapters.
Requires: pip install mistune weasyprint
"""
from pathlib import Path
import mistune
from weasyprint import HTML
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'11_design_system/Taktera-v3.3-implementation-guide'
chapters=['00-STATUS-AND-SCOPE.md','01-TOKENS-AND-COLOR.md','02-COMPONENT-SPEC.md','03-PLATFORM-IMPLEMENTATION.md','04-QA-CHECKLIST.md','05-ROADMAP-V4.md']
markdown=mistune.create_markdown(plugins=['table','strikethrough','url'])
sections=[]
for path in chapters:
    f=ROOT/'11_design_system'/path
    sections.append('<section class="chapter">'+markdown(f.read_text(encoding='utf-8'))+'</section>')
html='''<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>Taktera Brand · Дополнение v3.3</title>
<style>
@font-face{font-family:Inter;src:url('../05_typography/Inter-Regular.ttf')}@font-face{font-family:Inter;src:url('../05_typography/Inter-SemiBold.ttf');font-weight:600}@font-face{font-family:Inter;src:url('../05_typography/Inter-Bold.ttf');font-weight:700}
@page{size:A4;margin:20mm 17mm 19mm}@page:first{@top-right{content:none}}
@page{@top-right{content:"TAKTERA / DESIGN SYSTEM · 3.3";font:9px Inter,sans-serif;color:#6B6F7D;letter-spacing:.1em}@bottom-left{content:"22 ноября 2026 · инженерное дополнение";font:9px Inter,sans-serif;color:#62676E}@bottom-right{content:counter(page);font:11px Inter,sans-serif;color:#50556B}}
*{box-sizing:border-box}body{font:11px/1.6 Inter,Arial,sans-serif;color:#22262B;background:#fff}a{color:#50556B;text-decoration:none;overflow-wrap:anywhere}h1,h2,h3{line-height:1.25;break-after:avoid}h1{font-size:25px;letter-spacing:-.035em;margin:0 0 12px}h2{font-size:15px;letter-spacing:-.012em;margin:22px 0 8px}h3{font-size:12px;margin:16px 0 7px}p{margin:0 0 10px}li{margin:4px 0}ul,ol{padding-left:21px;margin:7px 0 13px}code{font-family:monospace;font-size:9.2px;background:#F4F3EF;border-radius:3px;padding:1px 3px;overflow-wrap:anywhere}pre{font:9.2px/1.35 monospace;background:#F4F3EF;padding:11px;border-radius:8px;white-space:pre-wrap;overflow-wrap:anywhere}pre code{background:transparent}table{width:100%;border-collapse:collapse;margin:9px 0 13px;table-layout:auto;font-size:9.7px}th{color:#50556B;background:#F4F3EF}th,td{text-align:left;vertical-align:top;border-bottom:1px solid #D9DCDF;padding:6px 6px;overflow-wrap:anywhere}thead{display:table-header-group}tr{break-inside:avoid}section.chapter{break-before:page}section.chapter:nth-of-type(2){break-before:page}section.chapter h1{border-left:4px solid #50556B;padding-left:13px}strong{font-weight:600}.cover{min-height:248mm;position:relative;padding-top:32mm}.cover img{width:150px;height:auto}.cover h1{font-size:39px;letter-spacing:-.04em;margin-top:35mm;line-height:1.08}.cover p{font-size:15px;color:#62676E;max-width:130mm}.eyebrow{font-size:11px;color:#50556B;font-weight:600;letter-spacing:.12em;margin-top:12mm}.cover-meta{position:static;margin-top:65mm;font-size:10px;border-top:1px solid #D9DCDF;padding-top:12px;width:100%}.cover-shape{position:absolute;top:4mm;right:0;width:75mm;height:65mm;border-radius:28px;background:#F4F3EF}.cover-shape::after{content:'';position:absolute;background:#50556B;border-radius:99px;width:13mm;height:13mm;right:15mm;top:11mm}
</style></head><body><section class="cover"><div class="cover-shape"></div><img src="../02_logos/master/svg/taktera-light.svg" alt="Taktera"><div class="eyebrow">BRAND SYSTEM / IMPLEMENTATION</div><h1>Дизайн-система<br>Taktera · v3.3</h1><p>Расширение фирменного стиля до инженерных интерфейсных токенов, прототипов компонентов и процедур контроля качества.</p><div class="cover-meta"><strong>Техническая редакция</strong> · 22 ноября 2026<br>Опирается на утверждённый визуальный бренд v3.2. Не заменяет брендбук v3.2.</div></section>''' + '\n'.join(sections) + '</body></html>'
Path(str(DEST)+'.html').write_text(html,encoding='utf-8')
HTML(string=html,base_url=str(ROOT/'11_design_system')).write_pdf(Path(str(DEST)+'.pdf'))
print('Generated:',Path(str(DEST)+'.html').name,Path(str(DEST)+'.pdf').name)
