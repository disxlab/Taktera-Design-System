#!/usr/bin/env python3
"""Additional Web Core gates for Alpha.3. Self-contained browser checks; not a WCAG or assistive-tech certification."""
import base64, json, re, shutil, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / '17_packages/web-core'
DEMO = ROOT / '17_packages/samples'
OUT = ROOT / '18_beta_readiness/qa'
checks=[]
errors=[]
def check(name, value, detail=''):
    checks.append(dict(name=name,ok=bool(value),detail=str(detail)[:180]))
    if not value:print('FAIL',name,detail)

with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox','--disable-dev-shm-usage'])
    page=browser.new_page(viewport={'width':1440,'height':900})
    page.on('pageerror',lambda ex:errors.append(str(ex)))
    html=(DEMO/'index.html').read_text()
    html=re.sub(r'<link[^>]*rel="stylesheet"[^>]*>','',html)
    html=re.sub(r'<script\s+src="[^"]+"\s*></script>','',html)
    page.emulate_media(reduced_motion='reduce')
    page.set_content(html,wait_until='domcontentloaded')
    page.add_style_tag(content=(WEB/'taktera-ui.css').read_text()+(DEMO/'demo.css').read_text())
    page.add_script_tag(content=(WEB/'taktera-ui.js').read_text())
    page.add_script_tag(content=(DEMO/'demo.js').read_text())
    check('No JavaScript bootstrap errors',not errors,errors)
    # Negative cases: invalid page size, themes, tones and type validation.
    check('Table rejects page size zero',page.evaluate("() => {try {TakteraUI.table({columns:[{key:'id',label:'ID'}],pageSize:0});return false}catch(e){return e instanceof RangeError}}"))
    check('Table rejects fractional page size',page.evaluate("() => {try {TakteraUI.table({columns:[{key:'id',label:'ID'}],pageSize:2.5});return false}catch(e){return e instanceof RangeError}}"))
    check('Alert rejects unknown tone',page.evaluate("() => {try {TakteraUI.alert({tone:'evil'});return false}catch(e){return e instanceof RangeError}}"))
    check('Toast rejects unknown tone',page.evaluate("() => {try {TakteraUI.toastRegion().push('x','evil');return false}catch(e){return e instanceof RangeError}}"))
    check('setTheme validates HTMLElement',page.evaluate("() => {try {TakteraUI.setTheme({},{});return false}catch(e){return e instanceof TypeError}}"))
    check('Error alert uses role alert',page.evaluate("() => TakteraUI.alert({tone:'error',message:'Error'}).getAttribute('role')==='alert'"))
    check('Normal notice uses role status',page.evaluate("() => TakteraUI.alert({tone:'info'}).getAttribute('role')==='status'"))
    check('Pager uses named navigation',page.locator('.tku-pager').get_attribute('aria-label')=='Страницы таблицы')
    check('Pager change is live announced',page.locator('.tku-pager__info').get_attribute('aria-live')=='polite')
    # Regression: row index must remain stable across pagination.
    check('rowKey receives absolute row index',page.evaluate("""() => {const key=[];const root=TakteraUI.table({columns:[{key:'name',label:'Имя'}],rows:[{name:'A'},{name:'B'},{name:'C'}],pageSize:2,rowKey:(r,i)=>{key.push(i);return 'key-'+i}});
      root.element.querySelectorAll('button')[1].click();const rows=[...root.element.querySelectorAll('tbody tr')];return rows.length===1&&rows[0].dataset.rowKey==='key-2'&&key.join(',')==='0,1,2';} """))
    # Empty-state and setRows recover with working paging.
    check('Empty table result is not negative',page.evaluate("""() => {const t=TakteraUI.table({columns:[{key:'name',label:'Name'}],rows:[],pageSize:2});return t.element.querySelector('.tku-pager__info').textContent==='0–0 из 0';} """))
    check('setRows updates paging after empty',page.evaluate("""() => {const t=TakteraUI.table({columns:[{key:'name',label:'Name'}],rows:[],pageSize:2});t.setRows([{name:'A'},{name:'B'},{name:'C'}]);return t.element.querySelector('.tku-pager__info').textContent==='1–2 из 3';} """))
    # Untrusted text is not parsed by alert, input, table or toast.
    check('Status message is plain text',page.evaluate("""() => {const n=TakteraUI.status({label:'<svg onload=alert(1)>'});return !n.querySelector('svg')&&n.textContent.includes('<svg');} """))
    check('Toast message is plain text',page.evaluate("""() => {const n=TakteraUI.toastRegion().push('<script>alert(1)</script>');return !n.querySelector('script')&&n.textContent.includes('<script>');} """))
    # Text fields: error dynamically set and removed.
    check('setError associates explanation',page.evaluate("""() => {const x=TakteraUI.field({label:'Имя'});x.setError('Ошибка');return x.input.getAttribute('aria-invalid')==='true' && x.input.getAttribute('aria-describedby')===x.element.querySelector('.tku-field__error').id;} """))
    check('setError clears explanation',page.evaluate("""() => {const x=TakteraUI.field({label:'Имя',error:'Ошибка'});x.setError('');return !x.input.hasAttribute('aria-invalid')&&!x.input.hasAttribute('aria-describedby')&&x.element.querySelector('.tku-field__error').hidden;} """))
    # Focus tests incl wrap and browser dialog; no screenreader claims.
    page.get_by_role('tab',name='Обзор').focus()
    page.keyboard.press('ArrowLeft')
    check('ArrowLeft wraps to final tab',page.get_by_role('tab',name='История').get_attribute('aria-selected')=='true')
    page.keyboard.press('ArrowRight')
    check('ArrowRight wraps to first tab',page.get_by_role('tab',name='Обзор').get_attribute('aria-selected')=='true')
    # Product theme isolation: different root scopes, existing tokens must apply independently.
    check('Two roots have independent accents',page.evaluate("""() => {
      const a=document.createElement('div'),b=document.createElement('div');a.className=b.className='tku-root';
      TakteraUI.setTheme(a,{product:'clinic',theme:'light'});TakteraUI.setTheme(b,{product:'travel',theme:'dark'});
      const ba=TakteraUI.button({label:'A'}),bb=TakteraUI.button({label:'B'});a.append(ba);b.append(bb);document.body.append(a,b);
      const ca=getComputedStyle(ba).backgroundColor,cb=getComputedStyle(bb).backgroundColor; a.remove();b.remove();
      return ca==='rgb(35, 104, 209)'&&cb==='rgb(255, 212, 59)';} """))
    # Focus and keyboard behavior with real native modal dialog.
    opener=page.get_by_role('button',name='Создать запись');opener.focus();opener.click()
    check('Dialog receives keyboard focus',page.evaluate('document.activeElement.closest("dialog")!==null'))
    page.keyboard.press('Escape')
    check('Escape closes and restores opener',page.evaluate("() => !document.querySelector('dialog').open && document.activeElement?.textContent==='Создать запись'"))
    # High-contrast, reduced motion CSS presence and actual computed tab color in forced-colors.
    css=(WEB/'taktera-ui.css').read_text()
    check('CSS includes forced-color override','@media (forced-colors: active)' in css)
    check('CSS includes reduced motion','prefers-reduced-motion:reduce' in css)
    page.emulate_media(forced_colors='active')
    check('OS forced colors mode applied',page.evaluate("matchMedia('(forced-colors: active)').matches"))
    check('Selected tab has highlight border',page.locator('.tku-tab[aria-selected="true"]').evaluate("e=>getComputedStyle(e).borderBottomColor!=='rgba(0, 0, 0, 0)'"))
    page.emulate_media(forced_colors='none')
    # 320px viewport: errors+long text should not force page overflow.
    page.set_viewport_size({'width':320,'height':900})
    check('320px baseline no viewport overflow',page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
    page.evaluate("""() => {const node=document.createElement('div');node.className='tku-root';TakteraUI.setTheme(node,{product:'travel',theme:'dark'});node.style.width='100%';node.style.maxWidth='100%';
      node.append(TakteraUI.field({label:'Название очень длинной услуги в примере системы',value:'Пример'}).element);
      document.body.querySelector('main').append(node);} """)
    check('320px nested fields no overflow',page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
    page.screenshot(path=str(OUT/'alpha3-320.png'),full_page=True)
    page.evaluate("document.querySelector('main > .tku-root')?.remove()")
    page.set_viewport_size({'width':1440,'height':900})
    page.screenshot(path=str(OUT/'alpha3-desktop.png'),full_page=True)
    check('No browser JS errors',not errors,errors)
    browser.close()

report={'version':'4.0-alpha.3','scope':'Web Core Chromium extended regression and focused accessibility checks; no axe/NVDA/VoiceOver','passed':sum(c['ok'] for c in checks),'failed':sum(not c['ok'] for c in checks),'checks':checks,'errors':errors}
(OUT/'browser-extended.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(f"Alpha.3 Chromium extended: {report['passed']}/{len(checks)} passed")
sys.exit(1 if report['failed'] else 0)
