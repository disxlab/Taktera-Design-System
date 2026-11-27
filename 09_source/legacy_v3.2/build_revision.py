from pathlib import Path
import sys, shutil, json, re, math, html
sys.path.insert(0,'C:/Users/sgkomc/Documents/Persona/work/brand-v3/deps')
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

BASE=Path('C:/Users/sgkomc/Documents/Persona')
OLD=BASE/'output/Taktera_Brand_Package_v3.1'
ROOT=BASE/'output/Taktera_Brand_Package_v3.2'
WORK=BASE/'work/brand-v3.2'
WORK.mkdir(exist_ok=True,parents=True)
if not ROOT.exists():
    shutil.copytree(OLD,ROOT,ignore=shutil.ignore_patterns('09_source','PACKAGE-MANIFEST.json','VALIDATION.json','DOCUMENTATION-VALIDATION.json'))
(ROOT/'09_source').mkdir(exist_ok=True)
for directory in ['02_logos/products/ru/svg','02_logos/products/ru/png','03_icons/app/micro/svg']:
    (ROOT/directory).mkdir(parents=True,exist_ok=True)
RU={'platform':'платформа','clinic':'клиника','beauty':'красота','spa':'спа','fitness':'фитнес','travel':'путешествия'}
CODES=dict(zip(RU,['PL','CL','BE','SP','FI','TR']))
tokens=json.loads((OLD/'04_tokens/taktera.tokens.json').read_text(encoding='utf-8'))
tokens['version']='3.2'
tokens['localization']={'brand':'taktera','ru':RU,'appCodes':CODES,'labelMinRecommendedPx':64,'microSizesPx':[16,24]}
(ROOT/'04_tokens/taktera.tokens.json').write_text(json.dumps(tokens,ensure_ascii=False,indent=2),encoding='utf-8')
font=TTFont(ROOT/'05_typography/Inter-Bold.ttf');glyphs=font.getGlyphSet();cmap=font.getBestCmap();units=font['head'].unitsPerEm
def paths(text,color,size,x,y,tracking=-1.4):
    out=[];cursor=x
    for c in text:
        glyph=glyphs[cmap[ord(c)]];pen=SVGPathPen(glyphs);glyph.draw(pen)
        if pen.getCommands():out.append(f'<path transform="translate({cursor:.3f} {y}) scale({size/units:.6f} {-size/units:.6f})" d="{pen.getCommands()}" fill="{color}"/>')
        cursor+=glyph.width*size/units+tracking
    return ''.join(out),cursor
def svg(body,w,h,title):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img"><title>{html.escape(title)}</title>{body}</svg>'
def symbol(ink,accent):
    return f'<path d="M12 16H29Q49 16 49 36V58" fill="none" stroke="{ink}" stroke-width="20" stroke-linecap="round" stroke-linejoin="round"/><circle cx="75" cy="15" r="10" fill="{accent}"/>'
for key,ru in RU.items():
    for theme in ['light','dark']:
        ink='#000000' if theme=='light' else '#FFFFFF';accent=tokens['products'][key]['accent'+theme.title()]
        word,end=paths('taktera',ink,60,112,62)
        name,end=paths(ru,accent,60,end+24,62)
        (ROOT/f'02_logos/products/ru/svg/{key}-ru-{theme}.svg').write_text(svg('<g transform="translate(6 7)">'+symbol(ink,accent)+'</g>'+word+name,math.ceil(end+8),88,'taktera '+ru),encoding='utf-8')
        bg='#F4F3EF' if theme=='light' else '#151719'
        base=f'<rect width="128" height="128" rx="28" fill="{bg}"/><g transform="translate(20 27)">{symbol(ink,accent)}</g>'
        _,width=paths(CODES[key],accent,20,0,0,0)
        label,_=paths(CODES[key],accent,20,95-width/2,89,0)
        (ROOT/f'03_icons/app/svg/{key}-{theme}.svg').write_text(svg(base+label,128,128,'Taktera '+ru+' / '+CODES[key]),encoding='utf-8')
        (ROOT/f'03_icons/app/micro/svg/{key}-{theme}.svg').write_text(svg(base,128,128,'Taktera '+ru+' / favicon'),encoding='utf-8')

book=(OLD/'Taktera-brandbook-v3.1.html').read_text(encoding='utf-8').replace('3.1','3.2')
book=book.replace('TAKTERA / BRAND SYSTEM','TAKTERA / ФИРМЕННЫЙ СТИЛЬ')
book=book.replace('Цветовое обновление v3.0: Fitness - красный, Travel - жёлтый.','Русские подписи и метки направлений в иконках приложений.')
book=book.replace('Слово taktera между знаком и clinic не добавляется.','В английской краткой версии: clinic. Русская полная версия: taktera клиника; слово taktera чёрное или белое.')
book=book.replace('Редакция 3.2 обновляет цвета Fitness и Travel; геометрия v3.0 сохранена.','Редакция 3.2 добавляет русские подписи и метки в иконках; палитра и геометрия сохранены.')
book=book.replace('На нейтральной подложке - чёрный или белый знак и цветная точка.','На нейтральной подложке - чёрный или белый знак, цветная точка и цветная метка под ней.')
book=book.replace('Экспорты: 16 / 24 / 32 / 48 / 64 / 128 / 256 / 512 / 1024 px, светлая и тёмная версии.','Метки: PL / CL / BE / SP / FI / TR. От 64 px метка используется как дополнительное различие. В favicon 16 / 24 px метка убрана; в 32 / 48 px на неё нельзя полагаться без названия.')
for k in RU:
    book=book.replace(f'<b>{k.title()}</b></div>',f'<b>{RU[k].capitalize()} · {CODES[k]}</b></div>')

def page(n,title,lead,body):
    return f'<section class="page" id="p{n}"><header><span>TAKTERA / ФИРМЕННЫЙ СТИЛЬ</span><span>V3.2 · 18.10.2026</span></header><div class="content"><h1>{title}</h1><p class="lead">{lead}</p>{body}</div><footer><span>Taktera · Руководство по бренду</span><span>{n:02}</span></footer></section>'
def family(theme):
    return ''.join(f'<div class="ru-row"><img src="02_logos/products/ru/svg/{k}-ru-{theme}.svg" alt="taktera {v}"></div>' for k,v in RU.items())
ru_page=page(13,'Русская продуктовая семья','taktera сохраняет латинское написание. Направления получают русские названия.',f'<div class="cols"><div class="panel light ru-family">{family("light")}</div><div class="panel dark ru-family">{family("dark")}</div></div><p class="note">Знак и taktera - чёрные или белые. Точка и русское направление - одного продуктового цвета. Английская краткая семья сохраняется. Beauty: taktera красота. Для полной русской версии рекомендуем ширину от 280 px; в печати - от 55 мм.</p>')
rows=''
for k in RU:
    cells=''.join(f'<td><img src="03_icons/app/png/{k}-light-{s}.png" width="{s}" height="{s}" alt="{CODES[k]} {s}px"></td>' for s in [16,24,32,48,64,128])
    rows+=f'<tr><th>{RU[k].capitalize()}<br>{CODES[k]}</th>{cells}</tr>'
icon_page=page(14,'Метка под точкой','Иконки показаны в фактических размерах CSS px: без увеличения для демонстрации.',f'<table class="icon-sizes"><tr><th>Направление</th><th>16 px</th><th>24 px</th><th>32 px</th><th>48 px</th><th>64 px</th><th>128 px</th></tr>{rows}</table><p class="note">На 16 / 24 px используется микро-версия без букв. На 32 / 48 px метка не гарантирует различимость. От 64 px буквы помогают различать приложения; название в меню обязательно при любом размере. Дополнительно проверьте ярлыки в целевых ОС и при системном масштабировании.</p>')
# 128 px icons in all six rows cannot fit a page; show 96 px column rendered from 128 px source.
icon_page=icon_page.replace('<th>128 px</th>','<th>96 px</th>').replace('width="128" height="128"','width="96" height="96"').replace('128px"','96px"')
book=book.replace('</body>',ru_page+icon_page+'</body>')
book=book.replace('</style>','.ru-row{height:72px;display:flex;align-items:center}.ru-row img{width:100%;height:44px;object-fit:contain;object-position:left}.ru-family{padding:22px 24px}.icon-sizes td,.icon-sizes th{padding:0 8px;height:89px}.icon-sizes img{display:block;object-fit:contain}.icon-sizes tr:first-child th{height:24px}.icon-sizes td:last-child img{width:80px;height:80px}.icon-sizes th{font-size:10px}@media(max-width:650px){.icon-sizes{min-width:620px}#p14 .content{overflow-x:auto}}'+'</style>')
# Last column is physically 80px to keep the sheet within the landscape page.
book=book.replace('<th>96 px</th>','<th>80 px</th>').replace('96px"','80px"')
book=book.replace('height:89px','height:76px').replace('width:80px;height:80px','width:72px;height:72px').replace('<th>80 px</th>','<th>72 px</th>').replace('80px"','72px"')
book=book.replace('<a href="#p2">Семья</a>','<a href="#p2">EN</a><a href="#p13">RU</a><a href="#p14">Метки</a>')
(ROOT/'Taktera-brandbook-v3.2.html').write_text(book,encoding='utf-8')
# Old version files exist only as history outside this package; remove known copied files.
for relative in ['Taktera-brandbook-v3.1.html','01_brandbook/Taktera-brandbook-v3.1.pdf']:
    f=ROOT/relative
    if f.exists():f.unlink()

notes='''# Локализация и метки приложений · Taktera 3.2

## Русская продуктовая семья

| Продукт | Русская композиция | Метка |
|---|---|---|
'''+''.join(f'| {k} | taktera {v} | {CODES[k]} |\n' for k,v in RU.items())+'''
Русские полные версии добавлены к английским кратким версиям. В русской версии знак и слово taktera чёрные или белые; точка и русское название направления имеют продуктовый цвет. Так сохраняется связь компании и направления. В логотипе taktera остаётся латиницей. Названия направлений строчные, кроме интерфейсных подписей по правилам предложения.

Файлы: 02_logos/products/ru/svg/{product}-ru-{theme}.svg и соответствующие PNG. Буквы переведены в контуры, включая кириллицу. Русскую полную композицию рекомендуется использовать от 280 px по ширине или от 55 мм в печати; проверяйте читаемость самого длинного названия «путешествия». Краткие английские версии сохраняют минимум 180 px / 35 мм. Для компактной навигации используйте знак и отдельное текстовое название.

## Метка под точкой

Метка состоит из двух латинских прописных букв и одинакова для русского и английского интерфейса. Она центрирована по вертикальной оси точки: x=95 в иконке 128 × 128. Базовая линия y=89, Inter Bold 20, буквы в контурах. Метка имеет тот же акцент, что точка. Геометрия основного знака не меняется.

В 03_icons/app/svg находятся основные иконки с меткой. PNG 32–1024 px содержат метку; PNG 16/24 px и соответствующие слои ICO используют микро-версию без букв из 03_icons/app/micro/svg. Это адаптация к размеру, а не отдельный фирменный знак.

На 32/48 px буквы слишком малы, чтобы служить надёжным самостоятельным различием. От 64 px они используются как дополнительная подсказка. На всех размерах в меню выбора нужны полные названия. Для отдельно установленных приложений задайте локализованное имя ярлыка: «Taktera Клиника», «Taktera Фитнес» и т. д. Жёлтая метка Travel на светлой подложке имеет невысокий контраст: нельзя использовать её вместо названия.

Проверены растровые экспорты на размерной сетке в светлой и тёмной темах. Отдельно требуется проверка в целевых ОС, launcher-масках и системном масштабировании: настольные снимки документации не имитируют все эти условия.

## Внедрение

В manifest/настройках сборки задайте локализованные display name / short name; URL и внутренние product ID остаются platform, clinic, beauty, spa, fitness, travel. Локаль выбирает SVG подписи, тема выбирает light/dark. Цветовые токены не меняются. Не пытайтесь переводить SVG через CSS: выбирайте готовый русский ресурс.
'''
(ROOT/'10_documentation/09-localization-and-app-labels.md').write_text(notes,encoding='utf-8')
(ROOT/'03_icons/app/README.md').write_text(notes[notes.index('## Метка под точкой'):],encoding='utf-8')
(ROOT/'02_logos/products/ru/README.md').write_text(notes[:notes.index('## Метка под точкой')],encoding='utf-8')
(ROOT/'CHANGELOG.md').write_text('# 3.2 / 2026-10-18\n- Добавлены 12 русских композиций в SVG/PNG для двух тем.\n- Добавлены цветные метки PL, CL, BE, SP, FI, TR под точкой в иконках.\n- Добавлены микро-версии для favicon 16/24 px и размерная сетка.\n- Брендбук расширен до 14 страниц; документация содержит правила локализации.\n- Палитра и форма знака сохранены.\n\n'+(OLD/'CHANGELOG.md').read_text(encoding='utf-8'),encoding='utf-8')
for f in [ROOT/'04_tokens/taktera.tokens.css',ROOT/'01_brandbook/README.md',ROOT/'07_migration/IMPLEMENTATION-MAP.md']:
    f.write_text(f.read_text(encoding='utf-8').replace('3.1','3.2'),encoding='utf-8')

# Adapt the full-documentation builder; make current rules authoritative in all outputs.
doc=(BASE/'work/brand-v3.1/complete_documentation.py').read_text(encoding='utf-8').replace('3.1','3.2').replace('12-страничный','14-страничный').replace('12 страниц','14 страниц').replace('12 страницах','14 страницах').replace('12 страниц брендбука','14 страниц брендбука')
doc=doc.replace('Между знаком и продуктовой подписью не добавляют слово taktera.','Английская краткая версия содержит имя направления; русская полная версия содержит taktera и русское имя направления. В русской версии taktera чёрное или белое, направление цветное.')
doc=doc.replace('Написание: platform, clinic, beauty, spa, fitness, travel.','Английские подписи: platform, clinic, beauty, spa, fitness, travel. Русские: taktera платформа, taktera клиника, taktera красота, taktera спа, taktera фитнес, taktera путешествия.')
doc=doc.replace("['Продуктовый логотип','Фирменный знак + точка + строчное имя направления']","['Продуктовый логотип EN','Фирменный знак + точка + строчное имя направления'],['Продуктовый логотип RU','Фирменный знак + точка + taktera + русское имя направления']")
doc=doc.replace("['Полная композиция с подписью','180 px по ширине']","['Полная композиция EN','180 px по ширине'],['Полная композиция RU','280 px по ширине']").replace("['Полная композиция в печати','35 мм по ширине']","['Композиция EN в печати','35 мм по ширине'],['Композиция RU в печати','55 мм по ширине']")
doc=doc.replace('Полная редакция документации добавляет пояснения и каталог без изменения принятой геометрии и палитры.','Редакция 3.2 добавляет русские логотипы и метки в app icons без изменения геометрии знака и палитры.')
doc=doc.replace('Полная документация расширяет редакцию 3.2 без изменения палитры и геометрии.','Редакция 3.2 добавляет русские подписи и метки приложений, сохраняя палитру и геометрию.')
addition='''
c=Chapter('09-localization-and-app-labels','09. Русские подписи и метки приложений')
c.p('Русская полная композиция: знак + точка + taktera + русское название направления. Знак и taktera чёрные или белые; точка и направление имеют один продуктовый цвет. Английская краткая семья сохраняется.')
c.table(['ID продукта','Русская подпись','Метка'],[[k,'taktera '+v,tokens['localization']['appCodes'][k]] for k,v in tokens['localization']['ru'].items()])
c.p('Русские SVG и PNG: 02_logos/products/ru. Минимальная рекомендуемая ширина полной русской композиции — 280 px, в печати — 55 мм. В интерфейсе подписи локализуются; product ID и адреса ресурсов не переводятся.')
c.h('Иконки приложений')
c.p('Под точкой размещена цветная метка PL, CL, BE, SP, FI или TR. Центр по x=95, базовая линия y=89 в области 128 × 128; Inter Bold 20, буквы в контурах. Цвет совпадает с точкой. Метки латинские и одинаковые для обеих локалей.')
c.p('PNG 32–1024 px содержат метку. На 16/24 px и соответствующих слоях ICO используется микро-версия без букв. В 32/48 px метка не считается надёжным самостоятельным различием; от 64 px служит дополнительной подсказкой. В меню выбора полные названия обязательны при любом размере. Жёлтая метка Travel на светлом фоне имеет невысокий контраст и не заменяет название.')
c.p('В отдельно устанавливаемых приложениях задайте локализованные имена ярлыков: Taktera Клиника, Taktera Фитнес и т. д. Макеты проверены в растровых размерах; отдельно проверьте launcher-маски, ярлыки ОС и системное масштабирование в целевой среде.')
c.save()
'''
doc=doc.replace('# Inventory of distributable visual resources, excluding historical reference.',addition+'\n# Inventory of distributable visual resources, excluding historical reference.')
doc=doc.replace('Брендбук и полная документация</h1>','Брендбук RU / EN и документация</h1>')
doc=doc.replace('Цветные точка и название направления. Fitness — красный, Travel — жёлтый.','Цветные точка и название направления. Русские подписи и метки приложений. Fitness — красный, Travel — жёлтый.')
doc=doc.replace("src=\"02_logos/products/svg/{k}-light.svg\"", "src=\"02_logos/products/ru/svg/{k}-ru-light.svg\"")
doc=doc.replace("['02_logos/products','6 продуктов, 2 темы, полные композиции и знаки']","['02_logos/products','6 продуктов, 2 темы, английские и русские композиции и знаки']")
doc=doc.replace('1. build_brandbook.py — HTML, векторы, токены, базовая документация. Может перезаписывать файлы пакета.','1. build_revision.py — редакция 3.2 на основе сохранённого пакета 3.1 и его скриптов. Требует настройки BASE и путей к исходной редакции; создаёт векторы и HTML.')
doc=doc.replace('8 подробных разделов','9 подробных разделов').replace('Восемь разделов','Девять разделов')
(WORK/'complete_documentation.py').write_text(doc,encoding='utf-8')

render=(BASE/'work/brand-v3.1/render_brandbook.cjs').read_text(encoding='utf-8').replace('3.1','3.2')
render=render.replace("['master','products']","['master','products','products/ru']")
render=render.replace("sharp(path.join(root,'03_icons/app/svg',f),{density:576})","sharp(path.join(root,size<=24?'03_icons/app/micro/svg':'03_icons/app/svg',f),{density:576})")
render=render.replace('height:1272','height:Math.ceil(inspect.pages.length/3)*318')
render=render.replace("fs.copyFileSync(path.join(qa,'page-02.png'),path.join(root,'01_brandbook/product-family.png'));","fs.copyFileSync(path.join(qa,'page-02.png'),path.join(root,'01_brandbook/product-family.png'));\n  fs.copyFileSync(path.join(qa,'page-13.png'),path.join(root,'01_brandbook/product-family-ru.png'));\n  fs.copyFileSync(path.join(qa,'page-14.png'),path.join(root,'01_brandbook/app-icon-sizes.png'));")
(WORK/'render_brandbook.cjs').write_text(render,encoding='utf-8')
check=(BASE/'work/brand-v3.1/check_documentation.cjs').read_text(encoding='utf-8').replace('3.1','3.2').replace('state.chapters!==8','state.chapters!==9').replace('chapters:8','chapters:9')
(WORK/'check_documentation.cjs').write_text(check,encoding='utf-8')
check=(BASE/'work/brand-v3.1/check_package.py').read_text(encoding='utf-8').replace('3.1','3.2').replace('==12','==14').replace("'pages':12","'pages':14").replace('12 non-empty','14 non-empty')
check=check.replace("im.save(root/f'03_icons/app/{p}-{theme}.ico',format='ICO',sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])",'''import struct
        sizes=[16,24,32,48,64,128,256]
        blobs=[(root/f'03_icons/app/png/{p}-{theme}-{s}.png').read_bytes() for s in sizes]
        offset=6+16*len(sizes); entries=[]
        for size,blob in zip(sizes,blobs):
            entries.append(struct.pack('<BBBBHHII',size%256,size%256,0,0,1,32,len(blob),offset));offset+=len(blob)
        (root/f'03_icons/app/{p}-{theme}.ico').write_bytes(struct.pack('<HHH',0,1,len(sizes))+b''.join(entries)+b''.join(blobs))''')
(WORK/'check_package.py').write_text(check,encoding='utf-8')
shutil.copy2(__file__,ROOT/'09_source/build_revision.py')
print('v3.2 sources and vector resources ready')
