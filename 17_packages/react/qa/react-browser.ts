import * as React from 'react';
import { renderToString } from 'react-dom/server';
import { chromium, firefox, webkit } from 'playwright';
import { createRequire } from 'node:module';
import { createServer } from 'node:http';
import { fileURLToPath } from 'node:url';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import assert from 'node:assert/strict';
import { Fixture } from './react-fixture';
import type { Product,Theme } from '../src/index';
// tsx already locks esbuild; resolve through its declared dependency (no new npm dependency).
const require=createRequire(import.meta.url);
const esbuild=createRequire(require.resolve('tsx/package.json'))('esbuild');
const dir=fileURLToPath(new URL('../',import.meta.url));
const out=resolve(dir,'../../28_engineering/qa/results','react-'+(process.argv[2]||'chromium'));
const engines={chromium,firefox,webkit};
const engine=(process.argv[2]||'chromium') as keyof typeof engines;
if(!engines[engine])throw Error('Unsupported engine');
const products:Product[]=['platform','clinic','beauty','spa','fitness','travel'],themes:Theme[]=['light','dark'];
const bundle=await esbuild.build({entryPoints:[resolve(dir,'qa/react-client.tsx')],bundle:true,write:false,platform:'browser',format:'iife',jsx:'automatic',define:{'process.env.NODE_ENV':'"development"'}});
const css=await readFile(resolve(dir,'styles.css'));
const server=createServer((req,res)=>{
 const u=new URL(req.url||'/','http://localhost');
 if(u.pathname==='/client.js'){res.writeHead(200,{'Content-Type':'text/javascript'}).end(bundle.outputFiles[0].contents);return}
 if(u.pathname==='/styles.css'){res.writeHead(200,{'Content-Type':'text/css'}).end(css);return}
 if(u.pathname!=='/'){res.writeHead(404).end();return}
 const product=u.searchParams.get('product') as Product,theme=u.searchParams.get('theme') as Theme;
 if(!products.includes(product)||!themes.includes(theme)){res.writeHead(400).end();return}
 const markup=renderToString(React.createElement(Fixture,{product,theme}));
 res.writeHead(200,{'Content-Type':'text/html; charset=utf-8'}).end('<!doctype html><html lang="ru"><head><title>React QA</title><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="/styles.css"></head><body><div id="root" data-product="'+product+'" data-theme="'+theme+'">'+markup+'</div></body></html>');
});
await mkdir(out,{recursive:true});
await new Promise<void>((ok,fail)=>{server.once('error',fail);server.listen(0,'127.0.0.1',ok)});
const address=server.address();if(!address||typeof address==='string')throw Error('HTTP server failed');
const report:{engine:string;scope:string;checks:{name:string;ok:boolean}[];errors:string[];axe:{product:string;theme:string;violations:unknown[];incomplete:unknown[]}[]}={engine,scope:'React 19 SSR renderToString -> hydrateRoot, interactive sample; not native Safari or complete WCAG',checks:[],errors:[],axe:[]};
let browser;
const check=(name:string,ok:unknown)=>{report.checks.push({name,ok:Boolean(ok)});assert.ok(ok,name)};
try{
 browser=await engines[engine].launch();const page=await browser.newPage({viewport:{width:1440,height:900},reducedMotion:'reduce'});
 page.on('pageerror',e=>report.errors.push(String(e)));page.on('console',m=>{if(m.type()==='error'&&!m.text().includes('favicon.ico')&&!m.text().includes('Failed to load resource: the server responded with a status of 404'))report.errors.push(m.text())});
 for(const product of products)for(const theme of themes){
  const label=product+'/'+theme;
  await page.goto('http://127.0.0.1:'+address.port+'/?product='+product+'&theme='+theme);
  const field=page.getByRole('textbox',{name:'Имя',exact:true});
  check(label+' SSR',await field.count()===1 && !(await page.locator('html').getAttribute('data-hydrated')));
  await field.evaluate(e=>{(window as any).__ssrField=e});
  await page.addScriptTag({url:'/client.js'});
  await page.waitForFunction(()=>document.documentElement.dataset.hydrated==='yes');
  check(label+' DOM retained',await field.evaluate(e=>(window as any).__ssrField===e));
  check(label+' provider',await page.locator('.tku-root').getAttribute('data-product')===product&&await page.locator('.tku-root').getAttribute('data-theme')===theme);
  await field.fill('Тест');await page.waitForFunction(()=>document.querySelector('[data-testid=value]')?.textContent==='Тест');check(label+' controlled input',await page.getByTestId('value').textContent()==='Тест');
  const err=page.getByRole('textbox',{name:'Ошибка'});check(label+' label/error',await err.getAttribute('aria-invalid')==='true'&&Boolean(await err.getAttribute('aria-describedby')));
  await page.getByRole('combobox',{name:'Услуга'}).selectOption('b');check(label+' select',await page.getByRole('combobox',{name:'Услуга'}).inputValue()==='b');
  const checkbox=page.getByRole('checkbox',{name:'Согласие'});await checkbox.check();check(label+' checkbox',await checkbox.isChecked());
  check(label+' switch/disabled/loading',await page.getByRole('switch',{name:'Напоминание'}).isChecked()&&await page.getByRole('button',{name:'Недоступно'}).isDisabled()&&await page.getByRole('button',{name:'Загрузка'}).getAttribute('aria-busy')==='true');
  await page.getByRole('tab',{name:'Обзор'}).focus();await page.keyboard.press('ArrowRight');check(label+' keyboard tabs',await page.getByRole('tab',{name:'Настройки'}).getAttribute('aria-selected')==='true'&&await page.getByRole('tab',{name:'Настройки'}).evaluate(e=>document.activeElement===e));
  const col=page.getByRole('columnheader',{name:'Имя записи'});await col.getByRole('button').click();const cells=await page.locator('table').first().locator('tbody td').allTextContents();check(label+' numeric sorting',await col.getAttribute('aria-sort')==='ascending'&&cells.indexOf('2')<cells.indexOf('10'));
  check(label+' escaped HTML',cells.some(x=>x.startsWith('<img'))&&await page.locator('table').first().locator('tbody img').count()===0);
  await page.getByRole('button',{name:'Далее'}).click();check(label+' pagination',await page.getByRole('navigation',{name:'Страницы'}).getByText('2 из 3').count()===1);
  const opener=page.getByRole('button',{name:'Открыть диалог'});await opener.focus();await opener.click();await page.getByRole('dialog',{name:'Новая запись'}).waitFor();check(label+' modal focus',await page.evaluate(()=>Boolean(document.activeElement?.closest('dialog'))));
  await page.keyboard.press('Escape');await page.getByRole('dialog').waitFor({state:'hidden'});await page.waitForFunction(()=>document.activeElement?.textContent==='Открыть диалог');check(label+' restore focus',await opener.evaluate(e=>document.activeElement===e));
  await opener.click();await page.getByRole('dialog').getByRole('button',{name:'Сохранить'}).click();await page.getByRole('dialog').waitFor({state:'hidden'});check(label+' confirm',true);
  const grid=page.getByRole('region',{name:'Реестр BR5',exact:true});
  check(label+' grid initial page',await grid.locator('tbody tr').count()===2);
  await grid.getByRole('button',{name:'Сумма'}).click();check(label+' grid numeric sort',(await grid.locator('tbody tr').first().textContent())?.includes('Record 2'));
  await grid.getByRole('checkbox',{name:'Выбрать запись r2'}).check();await grid.getByRole('button',{name:'Следующая'}).click();check(label+' grid selection across pages',await grid.getByText('Выбрано: 1',{exact:true}).count()===1&&await grid.locator('tbody tr').count()===1);
  await grid.getByRole('button',{name:'Предыдущая'}).click();check(label+' grid selected row restored',await grid.getByRole('checkbox',{name:'Выбрать запись r2'}).isChecked());
  await grid.getByRole('textbox',{name:'Поиск в реестре'}).fill('Other');check(label+' grid search/group',await grid.locator('tbody tr').count()===1&&(await grid.locator('tbody').textContent())?.includes('Other')&&await grid.getByText('closed: 1',{exact:true}).count()===1);
  await grid.getByRole('textbox',{name:'Поиск в реестре'}).fill('');
  const virtual=page.getByRole('region',{name:'Виртуальный реестр BR5',exact:true}),scroll=virtual.getByRole('region',{name:'Прокрутка реестра'});
  const rendered=()=>virtual.locator('tbody tr[data-grid-index]');
  check(label+' virtual bounded DOM',await rendered().count()<=20&&await virtual.getByRole('table').getAttribute('aria-rowcount')==='10001');
  await virtual.getByRole('checkbox',{name:'Выбрать запись v00000',exact:true}).check();
  await scroll.focus();await page.keyboard.press('End');
  await virtual.getByRole('checkbox',{name:'Выбрать запись v09999',exact:true}).waitFor();
  check(label+' virtual end and bounded DOM',await rendered().count()<=20&&await virtual.getByRole('checkbox',{name:'Выбрать запись v09999',exact:true}).count()===1);
  check(label+' virtual selection retained',await virtual.getByText('Выбрано: 1',{exact:true}).count()===1);
  await scroll.focus();await page.keyboard.press('Home');await virtual.getByRole('checkbox',{name:'Выбрать запись v00000',exact:true}).waitFor();
  check(label+' virtual Home and selection',await virtual.getByRole('checkbox',{name:'Выбрать запись v00000',exact:true}).isChecked());
  await virtual.getByRole('button',{name:'Постраничный режим'}).click();
  check(label+' virtual accessible page fallback',await rendered().count()===25&&await virtual.getByRole('checkbox',{name:'Выбрать запись v00000',exact:true}).isChecked());
  await virtual.getByRole('button',{name:'Виртуальный режим'}).click();
  check(label+' virtual toggle bounded',await rendered().count()<=20);
  await virtual.getByRole('textbox',{name:'Поиск в реестре'}).fill('Synthetic 9999');
  check(label+' virtual filtered result',await rendered().count()===1&&await virtual.getByRole('checkbox',{name:'Выбрать запись v09999',exact:true}).count()===1);
  await virtual.getByRole('textbox',{name:'Поиск в реестре'}).fill('');
  await page.addScriptTag({path:require.resolve('axe-core/axe.min.js')});
  const scan=await page.evaluate(async()=>{const x=await (window as any).axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']}});return {violations:x.violations.map((v:any)=>({id:v.id,nodes:v.nodes.map((n:any)=>n.target)})),incomplete:x.incomplete.map((v:any)=>({id:v.id,nodes:v.nodes.map((n:any)=>n.target)}))}});
  report.axe.push({product,theme,...scan});
  if(scan.violations.length)console.log(JSON.stringify({engine,product,theme,axeViolations:scan.violations}));
 }
 check('no console/hydration/page errors',report.errors.length===0);
}catch(e){report.errors.push(String(e))}
finally{if(browser)await browser.close();await new Promise<void>(ok=>server.close(()=>ok()));await writeFile(resolve(out,'report.json'),JSON.stringify(report,null,2)+'\n')}
const violations=report.axe.reduce((n,x)=>n+x.violations.length,0);
console.log(JSON.stringify({engine,checks:report.checks.length,passed:report.checks.filter(x=>x.ok).length,scans:report.axe.length,violations,errors:report.errors}));
if(report.errors.length||report.axe.length!==12||violations)process.exitCode=1;
