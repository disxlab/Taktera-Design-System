#!/usr/bin/env python3
"""Browser behavior tests for Taktera reusable Web Core, not for earlier alpha demo."""
import base64, json, re, sys, traceback, shutil
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
PACK=ROOT/'17_packages'
SAMPLE=PACK/'samples'; WEB=PACK/'web-core'; SHOTS=PACK/'qa'/'screenshots'
SHOTS.mkdir(parents=True,exist_ok=True)
palette=json.loads((ROOT/'04_tokens/taktera.tokens.json').read_text(encoding='utf-8'))
checks=[]; errors=[]
def check(name,condition,info=''):
    checks.append({'name':name,'ok':bool(condition),'info':str(info)[:160]})
    if not condition:print('FAILED',name,info)

def css_font():
    fonts=ROOT/'05_typography'
    blocks=[]
    for weight,file in [(400,'Inter-Regular.woff2'),(600,'Inter-SemiBold.woff2'),(700,'Inter-Bold.woff2')]:
        data=base64.b64encode((fonts/file).read_bytes()).decode()
        blocks.append(f'@font-face{{font-family:Inter;src:url(data:font/woff2;base64,{data});font-weight:{weight};font-display:swap}}')
    return '\n'.join(blocks)

def load(page):
    html=(SAMPLE/'index.html').read_text(encoding='utf-8')
    html=re.sub(r'<link[^>]*rel="stylesheet"[^>]*>', '', html)
    html=re.sub(r'<script\s+src="[^"]+"\s*></script>','',html)
    page.set_content(html,wait_until='domcontentloaded')
    page.add_style_tag(content=css_font()+(WEB/'taktera-ui.css').read_text(encoding='utf-8')+(SAMPLE/'demo.css').read_text(encoding='utf-8'))
    page.add_script_tag(content=(WEB/'taktera-ui.js').read_text(encoding='utf-8'))
    page.add_script_tag(content=(SAMPLE/'demo.js').read_text(encoding='utf-8'))

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=shutil.which('chromium') or shutil.which('chromium-browser') or None,args=['--no-sandbox','--disable-dev-shm-usage'])
    page=browser.new_page(viewport={'width':1440,'height':900},device_scale_factor=1)
    page.on('pageerror',lambda e: errors.append(str(e)))
    page.emulate_media(reduced_motion='reduce')
    load(page)
    check('Loaded API and native components',page.evaluate('Boolean(window.TakteraUI && document.querySelector(".tku-table"))'))
    check('No page errors at bootstrap',not errors,str(errors))
    products=['platform','clinic','beauty','spa','fitness','travel'];themes=['light','dark']
    for product in products:
      for theme in themes:
        page.locator('#product').select_option(product)
        page.locator('#theme').select_option(theme)
        check(f'Theme attributes {product}/{theme}',page.evaluate('''() => document.body.dataset.product === document.querySelector('#product').value && document.body.dataset.theme === document.querySelector('#theme').value'''))
        expected=palette['products'][product]['accentLight' if theme=='light' else 'accentDark']
        actual=page.locator('.tku-button--primary').first.evaluate('e=>getComputedStyle(e).backgroundColor')
        channels=tuple(int(c) for c in re.findall(r'\d+',actual)[:3]);expected_channels=tuple(bytes.fromhex(expected[1:]))
        check(f'Canonical accent rendered {product}/{theme}',channels==expected_channels, f'{actual} vs {expected}')
        page.screenshot(path=str(SHOTS/f'{product}-{theme}.png'),full_page=True)
    for width in [320,390,768,1440]:
        page.set_viewport_size({'width':width,'height':900})
        check(f'Responsive no horizontal viewport overflow {width}',page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'),page.evaluate('({scroll:document.documentElement.scrollWidth,width:window.innerWidth})'))
        if width in (320,1440):page.screenshot(path=str(SHOTS/f'responsive-{width}.png'),full_page=True)
    page.set_viewport_size({'width':1440,'height':900})
    check('Name field has associated label',page.get_by_role('textbox',name='Название услуги').count()==1)
    check('Invalid field has error association',page.get_by_role('textbox',name='Поле с ошибкой').get_attribute('aria-describedby') is not None)
    check('Disabled action cannot be clicked',page.get_by_role('button',name='Недоступно').is_disabled())
    check('Loading action aria-busy',page.get_by_role('button',name='Загрузка').get_attribute('aria-busy')=='true')
    check('Switch exposes checked role',page.get_by_role('switch',name='Напоминание включено').is_checked())
    # Tab roving & focus
    page.get_by_role('tab',name='Обзор').focus()
    page.keyboard.press('ArrowRight')
    check('Tab right arrow changes selection',page.get_by_role('tab',name='Настройки').get_attribute('aria-selected')=='true')
    check('Arrow-selected tab is keyboard focus',page.get_by_role('tab',name='Настройки').evaluate('e=>document.activeElement===e'))
    page.keyboard.press('End')
    check('Tab End navigates to last tab',page.get_by_role('tab',name='История').get_attribute('aria-selected')=='true')
    page.keyboard.press('Home')
    check('Tab Home navigates to first tab',page.get_by_role('tab',name='Обзор').get_attribute('aria-selected')=='true')
    # Table sort/pagination
    page.get_by_role('columnheader',name='Клиент').get_by_role('button').click()
    check('Table sort aria-sort ascending',page.get_by_role('columnheader',name='Клиент').get_attribute('aria-sort')=='ascending')
    page.get_by_role('columnheader',name='Клиент').get_by_role('button').click()
    check('Table sort toggles desc',page.get_by_role('columnheader',name='Клиент').get_attribute('aria-sort')=='descending')
    page.get_by_role('button',name='Далее').click()
    check('Table pagination updates range',page.get_by_text('5–7 из 7').count()==1)
    page.get_by_role('button',name='Назад').click()
    check('Table previous works',page.get_by_text('1–4 из 7').count()==1)
    # Dialog and focus restore
    opener=page.get_by_role('button',name='Создать запись')
    opener.focus();opener.click()
    check('Native dialog is modal',page.get_by_role('dialog',name='Новая демонстрационная запись').evaluate('e=>e.open'))
    check('Dialog holds focus',page.evaluate('document.activeElement.closest("dialog")!==null'))
    page.keyboard.press('Escape')
    check('Dialog Escape closes',not page.locator('dialog').evaluate('e=>e.open'))
    check('Focus returns to opener',opener.evaluate('e=>document.activeElement===e'))
    opener.click();page.get_by_role('dialog').get_by_role('button',name='Сохранить').click()
    check('Dialog confirmation closes',not page.locator('dialog').evaluate('e=>e.open'))
    check('Toast appears on confirmation',page.get_by_text('Демонстрационная запись создана').count()>=1)
    page.get_by_role('button',name='Закрыть уведомление').click()
    check('Toast can be dismissed',page.locator('.tku-toast').count()==0)
    # User-input XSS sentinel; should remain text, not HTML
    check('XSS escaping in table cells',page.evaluate('''() => {const root=document.createElement('div');document.body.append(root);
      const t=TakteraUI.table({columns:[{key:'name',label:'Имя'}],rows:[{name:'<img src=x onerror=alert(1)>'}],rowKey:()=> 'x'});
      root.append(t.element);const valid=root.querySelector('td').textContent.includes('<img')&&!root.querySelector('img');root.remove();return valid;}'''))
    check('Invalid theme rejected',page.evaluate("() => {try {TakteraUI.setTheme(document.body,{product:'other',theme:'light'});return false;}catch(e){return e instanceof RangeError}}"))
    check('Zero browser errors',not errors,str(errors))
    browser.close()
result={'version':'v4.0-alpha.3','test_target':'web-core standalone samples demo','browser':'system Chromium','navigation':'set_content+inject local source because file/http blocked','checks':checks,'passed':sum(x['ok'] for x in checks),'failed':sum(not x['ok'] for x in checks),'browser_errors':errors}
(PACK/'qa'/'browser-qa.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(f"Passed {result['passed']}/{len(checks)}; failed {result['failed']}")
sys.exit(1 if result['failed'] else 0)
