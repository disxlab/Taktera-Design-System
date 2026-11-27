#!/usr/bin/env python3
"""HTTP hosted consumer smoke test for local npm-installed Web Core. Chromium only."""
import json,sys,re
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'pilot-app';OUT=ROOT/'qa'
checks=[];errors=[]
def check(k,v):checks.append({'check':k,'ok':bool(v)});print(('PASS' if v else 'FAIL'),k)
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  page=browser.new_page(viewport={'width':1280,'height':850})
  page.on('pageerror',lambda err:errors.append(str(err)))
  responses=[]
  page.on('response',lambda response:responses.append((response.url,response.status)))
  html=(APP/'index.html').read_text()
  html=re.sub(r'<link[^>]*rel="stylesheet"[^>]*>','',html)
  html=re.sub(r'<script[^>]*src="[^"]+"[^>]*></script>','',html)
  page.emulate_media(reduced_motion='reduce')
  page.set_content(html,wait_until='domcontentloaded')
  pkg=APP/'node_modules/@taktera/ui-core'
  page.add_style_tag(content=(pkg/'taktera-ui.css').read_text())
  page.add_script_tag(content=(pkg/'taktera-ui.js').read_text())
  pilot=(APP/'pilot.mjs').read_text()
  pilot=re.sub(r"import \{[^}]+\} from [^;]+;",'const {setTheme,button,field,table,dialog}=globalThis.TakteraUI;',pilot,count=1)
  page.add_script_tag(content=pilot)
  check('HTTP module loads',page.locator('.tku-table tbody tr').count()==2)
  check('Consumer app bootstraps with installed package',not errors)
  check('English pager',page.locator('.tku-pager__info').inner_text()=='1–2 of 3')
  check('English labels',page.get_by_role('button',name='Next').count()==1)
  check('Numeric sorting',page.locator('th').last.get_by_role('button').count()==1)
  page.get_by_role('button',name='Next').click()
  check('Pagination',page.locator('.tku-table tbody tr').count()==1)
  page.locator('#locale').select_option('ru')
  check('Russian labels',page.get_by_role('button',name='Далее').count()==1)
  check('Russian pager',page.locator('.tku-pager__info').inner_text()=='1–2 из 3')
  page.locator('#product').select_option('travel');page.locator('#theme').select_option('dark')
  check('Theme attributes',page.locator('#app').get_attribute('data-product')=='travel' and page.locator('#app').get_attribute('data-theme')=='dark')
  page.get_by_role('button',name='Создать').click()
  check('Localized modal',page.get_by_role('dialog').get_by_role('button',name='Отмена').count()==1)
  page.keyboard.press('Escape')
  check('Focus restored',page.evaluate("document.activeElement.textContent==='Создать'"))
  page.locator('#locale').select_option('en')
  page.get_by_role('button',name='Create').click()
  check('English modal',page.get_by_role('dialog').get_by_role('button',name='Cancel').count()==1)
  page.keyboard.press('Escape')
  page.set_viewport_size({'width':320,'height':750})
  check('Mobile no viewport overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
  page.screenshot(path=str(OUT/'pilot-mobile.png'),full_page=True)
  page.set_viewport_size({'width':1280,'height':850})
  page.screenshot(path=str(OUT/'pilot-desktop.png'),full_page=True)
  check('No JavaScript errors',not errors)
  browser.close()
finally:pass
report={'passed':sum(c['ok'] for c in checks),'total':len(checks),'checks':checks,'js_errors':errors,'scope':'Chromium injected-local-files pilot with npm ci --offline; HTTP navigation blocked by environment policy; not full cross-browser/assistive-tech audit'}
(OUT/'pilot-results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(report['passed'],'/',report['total'])
sys.exit(0 if report['passed']==report['total'] else 1)
