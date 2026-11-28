from pathlib import Path
import json, base64, re
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
url='about:blank'
html=(root/'13_ui_kit/index.html').read_text(encoding='utf8')
styles=[]
for rel in ['04_tokens/taktera.tokens.css','13_ui_kit/ui.css']:
 css=(root/rel).read_text(encoding='utf8')
 for font in ['Regular','SemiBold','Bold']:
  fontb=base64.b64encode((root/f'05_typography/Inter-{font}.woff2').read_bytes()).decode('ascii')
  css=css.replace(f"url('../05_typography/Inter-{font}.woff2')",f"url('data:font/woff2;base64,{fontb}')")
 styles.append(css)
html=re.sub(r'<link rel="stylesheet"[^>]*>', '', html)
html=re.sub(r'<script src="[^"]+" defer></script>', '', html)
html=html.replace('</head>', '<style>'+''.join(styles)+'</style></head>')
html=html.replace('</body>', '<script>'+ (root/'13_ui_kit/data.js').read_text(encoding='utf8') + '</script><script>'+(root/'13_ui_kit/ui.js').read_text(encoding='utf8')+'</script></body>')
def logo_data(product,theme):
 src=root/f'02_logos/products/ru/svg/{product}-ru-{theme}.svg'
 return 'data:image/svg+xml;base64,'+base64.b64encode(src.read_bytes()).decode('ascii')
def set_logo(page,product,theme):page.locator('#logo').evaluate('(e,src)=>e.src=src',logo_data(product,theme))
results={'browser':'Chromium','url':'about:blank + inlined local assets (navigation sandbox restriction)','checks':[],'console_errors':[],'page_errors':[]}
def check(name,ok,details=''):
 results['checks'].append({'name':name,'pass':bool(ok),'details':details});print(('OK ' if ok else 'FAIL ')+name+' '+details)
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
 page=browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
 page.on('console',lambda m: results['console_errors'].append(m.text) if m.type=='error' else None)
 page.on('pageerror',lambda e:results['page_errors'].append(str(e)))
 page.goto(url,wait_until='load');page.set_content(html,wait_until='load');set_logo(page,'clinic','light')
 page.screenshot(path=str(root/'16_quality/screenshots/clinic-light.png'),full_page=True)
 check('loaded',page.locator('#hero-title').inner_text()=='Обзор клиники')
 window_names={'platform':'Платформа','clinic':'Клиника','beauty':'Красота','spa':'СПА','fitness':'Фитнес','travel':'Путешествия'}
 for product in ['platform','clinic','beauty','spa','fitness','travel']:
  page.locator('#product-select').select_option(product)
  for theme in ['light','dark']:
   page.locator('#theme-select').select_option(theme)
   set_logo(page,product,theme)
   check(f'{product}-{theme}',page.locator('html').get_attribute('data-product')==product and page.locator('html').get_attribute('data-theme')==theme and page.locator('#logo').get_attribute('alt')==('Taktera '+window_names[product]))
   page.screenshot(path=str(root/f'16_quality/screenshots/{product}-{theme}.png'),full_page=True)
   check(f'no-overflow {product}-{theme}',page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'))
 page.locator('#product-select').select_option('clinic');page.locator('#theme-select').select_option('light');set_logo(page,'clinic','light')
 page.locator('[data-view="records"].tk4-nav-link').click()
 check('records navigation',page.locator('#view-records').is_visible())
 check('accessible mobile nav label',page.locator('[data-view="overview"].tk4-nav-link').get_attribute('aria-label')=='Обзор')
 page.locator('#records-search').fill('TK-0101')
 check('filter',page.locator('#records-table tbody tr').count()==1)
 page.locator('#records-search').fill('')
 page.locator('[data-tab="pending"]').click()
 check('status tabs',page.locator('#records-table tbody tr').count()>0 and page.locator('[data-tab="pending"]').get_attribute('aria-selected')=='true')
 page.locator('[data-tab="all"]').click()
 page.locator('#next-page').click()
 check('pagination',page.locator('#page-info').inner_text().startswith('Показано 6'))
 page.locator('#view-records [data-action="create"]').click()
 check('dialog opens',page.locator('#create-dialog').evaluate('(e)=>e.open'))
 page.locator('#create-form button[type=submit]').click()
 check('invalid form',page.locator('#create-name').get_attribute('aria-invalid')=='true')
 page.locator('#create-name').fill('Тестовый клиент');page.locator('#create-service').fill('Тестовая услуга')
 page.locator('#create-form button[type=submit]').click()
 check('create record',page.locator('#create-dialog').evaluate('(e)=>!e.open') and page.evaluate('takteraDemo.state.rows.clinic[0].contact')=='Тестовый клиент')
 page.locator('[data-view="components"].tk4-nav-link').click()
 check('components view',page.locator('#view-components').is_visible() and page.locator('#view-overview').is_hidden())
 page.locator('#sample-toast').click();check('toast',page.locator('.tk4-toast').count()>0)
 page.locator('#sample-confirm').click();check('confirm dialog',page.locator('#confirm-dialog').evaluate('(e)=>e.open'))
 page.keyboard.press('Escape');check('Escape closes',page.locator('#confirm-dialog').evaluate('(e)=>!e.open'))
 page.screenshot(path=str(root/'16_quality/screenshots/components-light.png'),full_page=True)
 page.locator('#theme-select').select_option('dark');page.screenshot(path=str(root/'16_quality/screenshots/components-dark.png'),full_page=True)
 mobile=browser.new_page(viewport={'width':390,'height':844},device_scale_factor=1)
 mobile.goto(url,wait_until='load');mobile.set_content(html,wait_until='load');set_logo(mobile,'clinic','light')
 mobile.screenshot(path=str(root/'16_quality/screenshots/clinic-mobile.png'),full_page=True)
 mobile.set_viewport_size({'width':320,'height':750});check('320px mobile no overflow',mobile.evaluate('document.documentElement.scrollWidth <= window.innerWidth'))
 check('mobile no horizontal overflow',mobile.evaluate('document.documentElement.scrollWidth <= window.innerWidth'))
 check('main landmark',page.locator('main#main').count()==1)
 check('page errors',not results['page_errors'],str(results['page_errors']))
 check('console errors',not results['console_errors'],str(results['console_errors']))
 browser.close()
report=root/'16_quality/browser-qa.json';report.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8');print('Result',sum(x['pass'] for x in results['checks']), '/',len(results['checks']));
if not all(x['pass'] for x in results['checks']):raise SystemExit(1)
