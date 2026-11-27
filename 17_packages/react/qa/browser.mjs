import { chromium, firefox, webkit } from 'playwright';
import { createServer } from 'node:http';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { resolve, extname, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import assert from 'node:assert/strict';
const root = fileURLToPath(new URL('../../../', import.meta.url));
const require = createRequire(import.meta.url);
const axePath = require.resolve('axe-core/axe.min.js');
const engine = process.argv[2] || 'chromium';
const output = resolve(root, '28_engineering/qa/results', engine);
const engines = {chromium, firefox, webkit};
if (!engines[engine]) throw Error('Unknown browser '+engine);
await mkdir(output,{recursive:true});
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.mjs':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.woff2':'font/woff2','.png':'image/png','.svg':'image/svg+xml'};
const server=createServer(async (req,res)=>{
  try{
    const path=resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));
    if(!path.startsWith(resolve(root)+sep)){res.writeHead(403).end();return;}
    const data=await readFile(path);res.writeHead(200,{'Content-Type':types[extname(path)]||'application/octet-stream'}).end(data);
  }catch{res.writeHead(404).end();}
});
await new Promise((ok,fail)=>{server.once('error',fail);server.listen(0,'127.0.0.1',ok)});
let browser; const report={engine,scope:'Web Core HTTP sample; not React hydration, native Safari or complete WCAG audit',checks:[],axe:[],errors:[]};
try{
  browser=await engines[engine].launch();
  report.browserVersion=browser.version();
  const page=await browser.newPage({viewport:{width:1440,height:900},reducedMotion:'reduce'});
  page.on('pageerror',e=>report.errors.push(String(e)));
  page.on('response',r=>{if(r.status()>=400 && !r.url().endsWith('/favicon.ico'))report.errors.push(r.status()+' '+r.url())});
  const check=(name,ok)=>{report.checks.push({name,ok:Boolean(ok)});assert.ok(ok,name)};
  await page.goto('http://127.0.0.1:'+server.address().port+'/17_packages/samples/index.html');
  await page.locator('.tku-table').waitFor();
  check('HTTP ESM API',await page.evaluate(async()=>{const m=await import('/17_packages/web-core/index.mjs');return typeof m.setTheme==='function'&&typeof m.table==='function'}));
  const colors=JSON.parse(await readFile(resolve(root,'04_tokens/taktera.tokens.json'),'utf8'));
  await page.addScriptTag({path:axePath});
  for(const product of ['platform','clinic','beauty','spa','fitness','travel'])for(const theme of ['light','dark']){
    await page.locator('#product').selectOption(product);await page.locator('#theme').selectOption(theme);
    check(product+'/'+theme+' attributes',await page.evaluate(([p,t])=>document.body.dataset.product===p&&document.body.dataset.theme===t,[product,theme]));
    const expected=colors.products[product][theme==='light'?'accentLight':'accentDark'].slice(1);
    const rgb=Array.from(Buffer.from(expected,'hex')).join(',');
    const actual=await page.locator('.tku-button--primary').first().evaluate(e=>getComputedStyle(e).backgroundColor);
    check(product+'/'+theme+' accent',actual.match(/\d+/g).slice(0,3).join(',')===rgb);
    const scan=await page.evaluate(async()=>window.axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']}}));
    report.axe.push({product,theme,violations:scan.violations.map(({id,impact,help,helpUrl,nodes})=>({id,impact,help,helpUrl,nodes:nodes.map(n=>({target:n.target,summary:n.failureSummary}))})),incomplete:scan.incomplete.map(x=>({id:x.id,nodes:x.nodes.map(n=>n.target)}))});
    await page.screenshot({path:resolve(output,product+'-'+theme+'.png'),fullPage:true});
  }
  for(const width of [320,390,768,1440]){await page.setViewportSize({width,height:900});check('viewport '+width,await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth))}
  check('label',await page.getByRole('textbox',{name:'Название услуги'}).count()===1);
  check('error association',Boolean(await page.getByRole('textbox',{name:'Поле с ошибкой'}).getAttribute('aria-describedby')));
  check('disabled',await page.getByRole('button',{name:'Недоступно'}).isDisabled());
  const tab=page.getByRole('tab',{name:'Обзор'});await tab.focus();await page.keyboard.press('ArrowRight');check('tab arrow',await page.getByRole('tab',{name:'Настройки'}).getAttribute('aria-selected')==='true');
  const col=page.getByRole('columnheader',{name:'Клиент'});await col.getByRole('button').click();check('table sort',await col.getAttribute('aria-sort')==='ascending');
  const opener=page.getByRole('button',{name:'Создать запись'});await opener.focus();await opener.click();await page.getByRole('dialog').waitFor();check('modal focus',await page.evaluate(()=>Boolean(document.activeElement.closest('dialog'))));await page.keyboard.press('Escape');await page.getByRole('dialog').waitFor({state:'hidden'});check('focus restoration',await opener.evaluate(e=>document.activeElement===e));
  check('XSS escaping',await page.evaluate(()=>{const t=window.TakteraUI.table({columns:[{key:'name',label:'Name'}],rows:[{name:'<img src=x onerror=alert(1)>'}],rowKey:()=> 'x'});return t.element.textContent.includes('<img')&&!t.element.querySelector('img')}));
  check('no page/HTTP errors',report.errors.length===0);
}catch(e){report.errors.push(String(e));}
finally{if(browser)await browser.close();await new Promise(ok=>server.close(ok));await writeFile(resolve(output,'report.json'),JSON.stringify(report,null,2)+'\n')}
const violations=report.axe.reduce((n,x)=>n+x.violations.length,0);
console.log(JSON.stringify({engine,checks:report.checks.length,passed:report.checks.filter(x=>x.ok).length,scans:report.axe.length,violations,errors:report.errors}));
if(report.errors.length||report.axe.length!==12||violations)process.exitCode=1;
