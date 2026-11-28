import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {join,resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
import {createHash} from 'node:crypto';
import {spawn,spawnSync} from 'node:child_process';
import assert from 'node:assert/strict';
const root=fileURLToPath(new URL('../../',import.meta.url));
const engine=process.argv[2],host=resolve(process.argv[3]),out=resolve(process.argv[4]);
assert.ok(['chromium','firefox','webkit'].includes(engine));
const tools=createRequire(join(root,'17_packages/react/package.json'));
const playwright=tools('playwright'),axePath=tools.resolve('axe-core/axe.min.js');
const read=async p=>JSON.parse(await readFile(p,'utf8'));
const hash=(data,algorithm='sha256')=>createHash(algorithm).update(data).digest('hex');
const input=await read(join(host,'acceptance-input.json'));
assert.equal(input.sourceCommit,process.env.GITHUB_SHA);
assert.equal(input.githubRunId,process.env.GITHUB_RUN_ID);
assert.equal(input.githubRunAttempt,process.env.GITHUB_RUN_ATTEMPT);
assert.equal(input.publicationAllowed,false);
const report={...input,engine,scope:'Canonical npm package-only reference workspace, English SDK workflows plus RU/EN host-owned synthetic transport; not production/native Safari or complete accessibility acceptance',checks:[],axe:[],errors:[],scenarios:[],publicationAllowed:false};
const products=['platform','clinic','beauty','spa','fitness','travel'],themes=['light','dark'];
// Intercept external network requests only, not local resources or axe's internal
// about:blank/data/blob documents. Keep the independent request observation.
function externalNetwork(target,origin){
 const u=new URL(target);
 return ['http:','https:','ws:','wss:'].includes(u.protocol)&&u.origin!==origin;
}
const probe='http://127.0.0.1:43210';
assert.equal(externalNetwork(probe+'/app.js',probe),false);
assert.equal(externalNetwork('about:blank',probe),false);
assert.equal(externalNetwork('data:text/html,test',probe),false);
assert.equal(externalNetwork('blob:'+probe+'/test',probe),false);
assert.equal(externalNetwork('https://example.invalid/',probe),true);
assert.equal(externalNetwork('http://127.0.0.1:43211/',probe),true);
assert.equal(externalNetwork('wss://example.invalid/',probe),true);
await mkdir(out,{recursive:true});
function check(name,ok){assert.equal(name,name.trim().replace(/\s+/g,' '),'Noncanonical check name: '+JSON.stringify(name));assert.ok(!report.checks.some(c=>c.name===name),'Duplicate check name: '+name);report.checks.push({name,ok:Boolean(ok)});assert.ok(ok,name);}
function run(command,args,cwd=host){const p=spawnSync(command,args,{cwd,encoding:'utf8',maxBuffer:16*1024*1024,env:{...process.env,NPM_CONFIG_CACHE:join(cwd,'.npm-cache')}});if(p.error||p.status!==0)throw Error(command+' failed: '+String(p.error??'')+'\n'+p.stdout+'\n'+p.stderr);return p.stdout.trim();}
let child,browser;const servers=[];
async function start(cwd=host){
 child=spawn(process.execPath,['serve.mjs'],{cwd,env:{...process.env,PORT:'0'},stdio:['ignore','pipe','pipe']});
 servers.push(child);
 return new Promise((ok,fail)=>{let output='';const timer=setTimeout(()=>fail(Error('Reference server timeout: '+output)),30000);
 child.stdout.on('data',buf=>{output+=buf;const m=output.match(/http:\/\/127\.0\.0\.1:(\d+)/);if(m){clearTimeout(timer);ok(m[0]);}});
 child.stderr.on('data',buf=>{output+=buf;});child.once('error',e=>{clearTimeout(timer);fail(e);});
 child.once('exit',code=>{clearTimeout(timer);fail(Error('Reference server exited '+code+': '+output));});});
}

// Firefox 1572 cross-world ARIA reflection regression:
// https://github.com/microsoft/playwright/issues/44135
// Separate role-locator interactions from main-world axe scans.
async function guardContext(context,url,external){
 await context.route(target=>externalNetwork(target,url),route=>route.abort());
 context.on('request',req=>{if(externalNetwork(req.url(),url))external.push(new URL(req.url()).origin);});
 await context.routeWebSocket('**/*',ws=>{external.push('websocket:'+new URL(ws.url()).origin);ws.close();});
}
async function auditRegistry(browser,url,product,theme){
 const errors=[],external=[];
 const context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce',serviceWorkers:'block'});
 try{
  await guardContext(context,url,external);
  const page=await context.newPage();
  page.on('crash',()=>errors.push('audit page crashed'));
  page.on('pageerror',e=>errors.push(String(e)));
  page.on('console',m=>{if(m.type()==='error'&&!m.text().includes('404'))errors.push(m.text());});
  await page.goto(url);
  await page.waitForFunction(()=>document.documentElement.dataset.referenceHydrated==='yes');
  await page.evaluate(({product,theme})=>{
   const set=(label,value)=>{
    const element=document.querySelector('select[aria-label="'+label+'"]');
    if(!(element instanceof HTMLSelectElement))throw Error('Missing audit select '+label);
    const setter=Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype,'value')?.set;
    if(!setter)throw Error('Missing native select setter');
    setter.call(element,value);
    element.dispatchEvent(new Event('change',{bubbles:true}));
   };
   set('Product',product);set('Theme',theme);
  },{product,theme});
  await page.waitForFunction(({product,theme})=>{
   const app=document.querySelector('#root .tku-root');
   return app?.dataset.product===product&&app?.dataset.theme===theme;
  },{product,theme});
  const state=await page.evaluate(()=>{
   const app=document.querySelector('#root .tku-root'),text=app?.textContent??'';
   return {product:app?.dataset.product,theme:app?.dataset.theme,registry:text.includes('Synthetic Alice')&&text.includes('Synthetic Bob')};
  });
  check(product+'/'+theme+' separate audit document state',state.product===product&&state.theme===theme&&state.registry);
  await page.addScriptTag({path:axePath});
  const scan=await page.evaluate(async()=>{
   const x=await window.axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']}});
   return {violations:x.violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))})),
           incomplete:x.incomplete.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)}))};
  });
  report.axe.push({product,theme,page:'registry',...scan});
  check(product+'/'+theme+' audit no browser errors',errors.length===0);
  check(product+'/'+theme+' audit no external requests',external.length===0);
 }finally{await context.close();}
}

// Host-owned localized transport acceptance; existing English workflows remain mandatory.
const transportLabels={
 en:{region:'Synthetic transport',name:'Customer name',save:'Save record',fail:'Fail next request',retry:'Retry same request',replay:'Replay last request',compete:'Simulate competing write',reload:'Reload record',external:'Synthetic competing name',validation:'Invalid customer name',unavailable:'Temporarily unavailable',applied:'Saved',conflict:'Version conflict',idle:'Ready',newName:'Synthetic updated name',finalName:'Synthetic resolved name'},
 ru:{region:'Синтетический транспорт',name:'Имя клиента',save:'Сохранить запись',fail:'Ошибка следующего запроса',retry:'Повторить тот же запрос',replay:'Повторить сохранённый запрос',compete:'Имитировать параллельную запись',reload:'Загрузить запись',external:'Синтетическое конкурентное имя',validation:'Недопустимое имя клиента',unavailable:'Временно недоступно',applied:'Сохранено',conflict:'Конфликт версий',idle:'Готово',newName:'Синтетическое новое имя',finalName:'Синтетическое исправленное имя'}
};

const operationsLabels={
 en:{section:'Synthetic operations',scheduler:'Localized schedule',analytics:'Localized analytics',visit:'Synthetic appointment',reject:'Synthetic conflict',updated:'Synthetic revised appointment',zone:'Time zone',week:'Week',day:'Day',editor:'Booking editor',title:'Title',save:'Save booking',conflict:'Server rejected operation: conflict',saved:'Saved',start:'Period start',end:'Period end',apply:'Apply period',invalid:'Choose a valid period of 1 to 366 days',incomplete:'Incomplete data: totals and export unavailable',export:'Export CSV',table:'Data table',details:'Details: 2026-12-01',detail:'Day details'},
 ru:{section:'Тестовые операции',scheduler:'Локализованное расписание',analytics:'Локализованная аналитика',visit:'Тестовая запись',reject:'Тестовый конфликт',updated:'Тестовая изменённая запись',zone:'Часовой пояс',week:'Неделя',day:'День',editor:'Редактор записи',title:'Название',save:'Сохранить запись',conflict:'Сервер отклонил операцию: конфликт',saved:'Сохранено',start:'Начало периода',end:'Конец периода',apply:'Применить период',invalid:'Укажите корректный период от 1 до 366 дней',incomplete:'Неполные данные: итоговые KPI и экспорт недоступны',export:'Экспорт CSV',table:'Таблица данных',details:'Подробнее: 2026-12-01',detail:'Показатели дня'}
};
async function localizedOperations(page,name){
 await page.getByRole('tab',{name:'Operations',exact:true}).click();
 for(const locale of ['en','ru']){
  const l=operationsLabels[locale],prefix=name+' '+locale+' operations ';
  await page.getByLabel('Operations language / Язык операций',{exact:true}).selectOption(locale);
  const host=page.getByRole('region',{name:l.section,exact:true}),sched=host.getByRole('region',{name:l.scheduler,exact:true}),analytics=host.getByRole('region',{name:l.analytics,exact:true});
  const booking=()=>sched.getByRole('button',{name:new RegExp('^'+l.visit+'(?:$| ·)')}).first();
  const calls=host.getByTestId('schedule-calls'),version=host.getByTestId('schedule-version');
  check(prefix+'locale',await host.getAttribute('lang')===locale&&await sched.getByLabel(l.zone).isVisible()&&await analytics.getByLabel(l.start).isVisible());
  check(prefix+'initial booking',await booking().isVisible()&&await version.textContent()==='v1'&&await calls.textContent()==='0');
  await sched.getByRole('button',{name:l.week,exact:true}).click();
  check(prefix+'week mode',await sched.getByRole('button',{name:l.week,exact:true}).getAttribute('aria-pressed')==='true');
  await sched.getByRole('button',{name:l.day,exact:true}).click();
  await sched.getByLabel(l.zone).selectOption('Europe/Amsterdam');
  check(prefix+'timezone',await sched.getByLabel(l.zone).inputValue()==='Europe/Amsterdam'&&(await sched.textContent()).includes('10:00'));
  await sched.getByLabel(l.zone).selectOption('UTC');
  await booking().click();
  const editor=sched.getByRole('form',{name:l.editor,exact:true}),title=editor.getByLabel(l.title,{exact:true});
  await title.fill(l.reject);await editor.getByRole('button',{name:l.save,exact:true}).click();
  await sched.getByRole('alert').filter({hasText:l.conflict}).waitFor();
  check(prefix+'scheduler conflict',await title.inputValue()===l.reject&&await calls.textContent()==='1'&&await version.textContent()==='v1');
  await title.fill(l.updated);await editor.getByRole('button',{name:l.save,exact:true}).click();
  await editor.waitFor({state:'hidden'});
  check(prefix+'scheduler applied',await sched.getByText(l.updated,{exact:true}).first().isVisible()&&await calls.textContent()==='2'&&await version.textContent()==='v2');
  const start=analytics.getByLabel(l.start),end=analytics.getByLabel(l.end),apply=analytics.getByRole('button',{name:l.apply,exact:true}),exportButton=analytics.getByRole('button',{name:l.export,exact:true});
  check(prefix+'analytics complete',await exportButton.isEnabled());
  await start.fill('2026-12-03');await apply.click();
  await analytics.getByRole('alert').filter({hasText:l.invalid}).waitFor();
  check(prefix+'invalid period retained',await exportButton.isEnabled()&&(await analytics.textContent()).includes('2026-12-01 — 2026-12-02'));
  await start.fill('2026-12-01');await end.fill('2026-12-03');await apply.click();
  await analytics.getByRole('status').filter({hasText:l.incomplete}).waitFor();
  check(prefix+'incomplete export denied',await exportButton.isDisabled());
  await end.fill('2026-12-02');await apply.click();
  await analytics.getByRole('button',{name:l.table,exact:true}).click();
  check(prefix+'table mode',await analytics.getByRole('button',{name:l.table,exact:true}).getAttribute('aria-pressed')==='true');
  await analytics.getByRole('button',{name:l.details,exact:true}).click();
  check(prefix+'day details',await analytics.getByRole('region',{name:l.detail,exact:true}).isVisible());
  const pending=page.waitForEvent('download');
  await exportButton.click();
  const download=await pending;
  const bytes=await readFile(await download.path(),'utf8');
  check(prefix+'csv exact bytes',download.suggestedFilename()==='taktera-metrics-2026-12-01-2026-12-02.csv'&&bytes==='date,currency,revenue_minor,visits,completed,capacity,used\r\n2026-12-01,RUB,12000,4,3,8,4\r\n2026-12-02,RUB,18000,6,5,8,5\r\n');
 }
}

async function localizedTransport(page,name,standalone=false){
 if(!standalone)await page.getByRole('tab',{name:'Transport',exact:true}).click();
 for(const locale of ['en','ru']){
  const l=transportLabels[locale],prefix=name+' '+locale+(standalone?' web transport ':' transport ');
  await page.getByLabel(standalone?'Web language / Язык':'Language / Язык',{exact:true}).selectOption(locale);
  const region=page.getByRole('region',{name:standalone?(locale==='ru'?'Web синтетический транспорт':'Web synthetic transport'):l.region,exact:true});
  const field=region.getByRole('textbox',{name:l.name,exact:true});
  const button=label=>region.getByRole('button',{name:label,exact:true});
  const record=region.getByTestId('transport-record'),version=region.getByTestId('transport-version'),status=region.getByTestId('transport-status');
  async function state(label,code,message,expectedName,expectedVersion){
   await status.getByText(message,{exact:true}).waitFor();
   check(prefix+label,await status.getAttribute('data-status')===code&&await record.textContent()===expectedName&&await version.textContent()===expectedVersion);
  }
  await state('initial','idle',l.idle,'Synthetic Alice','1');
  check(prefix+'locale',await region.getAttribute('lang')===locale&&await field.isVisible());
  await field.fill('');await button(l.save).click();
  await state('validation','validation',l.validation,'Synthetic Alice','1');
  check(prefix+'accessible error',await field.getAttribute('aria-invalid')==='true'&&Boolean(await field.getAttribute('aria-describedby')));
  await field.fill(l.newName);await button(l.fail).click();await button(l.save).click();
  await state('unavailable','unavailable',l.unavailable,'Synthetic Alice','1');
  await button(l.retry).click();await state('retry','applied',l.applied,l.newName,'2');
  await button(l.replay).click();await state('idempotent replay','applied',l.applied,l.newName,'2');
  await button(l.compete).click();await state('competing write','idle',l.idle,l.external,'3');
  await field.fill(l.finalName);await button(l.save).click();await state('conflict','conflict',l.conflict,l.external,'3');
  await button(l.reload).click();await state('reload current','idle',l.idle,l.external,'3');
  check(prefix+'draft reloaded',await field.inputValue()===l.external);
  await field.fill(l.finalName);await button(l.save).click();await state('resolved save','applied',l.applied,l.finalName,'4');
 }
}


async function standaloneWeb(){
 const web=host+'-web';
 const inventory=await read(join(web,'package-inventory.json'));
 assert.equal(inventory.length,1);
 const item=inventory[0],archive=await readFile(join(web,item.file));
 check('standalone Web canonical archive',item.name==='@taktera/ui-core'&&hash(archive)===input.canonicalPackages[item.file.split('/').at(-1)]);
 run('npm',['install','--package-lock-only','--ignore-scripts','--no-audit','--no-fund','--offline'],web);
 run('npm',['ci','--ignore-scripts','--no-audit','--no-fund','--offline'],web);
 const lock=await read(join(web,'package-lock.json'));
 check('standalone Web exact lock',Object.keys(lock.packages).sort().join('|')==='|node_modules/@taktera/ui-core'&&lock.packages['node_modules/@taktera/ui-core'].integrity==='sha512-'+createHash('sha512').update(archive).digest('base64'));
 const meta=await read(join(web,'node_modules/@taktera/ui-core/package.json'));
 check('standalone Web installed identity',meta.name===item.name&&meta.version===item.version);
 const url=await start(web);
 for(const product of products)for(const theme of themes){
  const name=product+'/'+theme,errors=[],external=[];
  const context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce',serviceWorkers:'block'});
  try{
   await guardContext(context,url,external);
   const page=await context.newPage();
   page.on('pageerror',e=>errors.push(String(e)));page.on('crash',()=>errors.push('page crashed'));
   page.on('console',m=>{if(m.type()==='error'&&!m.text().includes('404'))errors.push(m.text());});
   await page.goto(url);await page.waitForFunction(()=>document.documentElement.dataset.webHydrated==='yes');
   await page.getByLabel('Web product',{exact:true}).selectOption(product);
   await page.getByLabel('Web theme',{exact:true}).selectOption(theme);
   const root=page.locator('#root');
   check(name+' standalone Web product/theme',await root.getAttribute('data-product')===product&&await root.getAttribute('data-theme')===theme);
   await localizedTransport(page,name,true);
   check(name+' standalone Web no browser errors',errors.length===0);
   check(name+' standalone Web no external requests',external.length===0);
  }finally{await context.close();}
 }
}

try{
 check('exact Node',process.version==='v26.13.1');
 check('exact npm',run('npm',['--version'])==='11.20.0');
 const lockFile=join(host,'package-lock.json');
 check('original consumer lock',hash(await readFile(lockFile))===input.consumerLockSha256);
 run('npm',['ci','--ignore-scripts','--no-audit','--no-fund']);
 check('lock unchanged after npm ci',hash(await readFile(lockFile))===input.consumerLockSha256);
 const lock=await read(lockFile),inventory=await read(join(host,'package-inventory.json'));
 for(const p of inventory){
  const bytes=await readFile(join(host,p.file)),filename=p.file.split('/').at(-1);
  check(p.name+' canonical archive',hash(bytes)===input.canonicalPackages[filename]&&hash(bytes)===p.sha256);
  check(p.name+' exact npm integrity',lock.packages['node_modules/'+p.name].integrity==='sha512-'+createHash('sha512').update(bytes).digest('base64'));
  const meta=await read(join(host,'node_modules',p.name,'package.json'));
  check(p.name+' installed identity',meta.name===p.name&&meta.version===p.version);
 }
 run('npm',['run','build']);check('strict TypeScript build from packages',true);
 const url=await start();browser=await playwright[engine].launch();
 for(const product of products)for(const theme of themes){
  const name=product+'/'+theme,errors=[],external=[];
  let phase='context';
  const context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce',serviceWorkers:'block'});
  try{
   await guardContext(context,url,external);
   const page=await context.newPage();
   page.on('crash',()=>errors.push('page crashed at '+phase));
   page.on('pageerror',e=>errors.push(String(e)));
   page.on('console',m=>{if(m.type()==='error'&&!m.text().includes('404'))errors.push(m.text());});
   phase='navigation/hydration';await page.goto(url);await page.waitForFunction(()=>document.documentElement.dataset.referenceHydrated==='yes');
   await page.getByLabel('Product',{exact:true}).selectOption(product);
   await page.getByLabel('Theme',{exact:true}).selectOption(theme);
   const app=page.locator('#root .tku-root');
   check(name+' product/theme',await app.getAttribute('data-product')===product&&await app.getAttribute('data-theme')===theme);
   const grid=page.getByRole('region',{name:'Reference registry',exact:true});
   await grid.getByRole('textbox',{name:'Search registry'}).fill('Bob');
   check(name+' registry filtering',await grid.getByText('Synthetic Bob',{exact:true}).count()===1&&await grid.getByText('Synthetic Alice',{exact:true}).count()===0);
   await grid.getByRole('textbox',{name:'Search registry'}).fill('');
   phase='workflow interactions';
   await page.getByRole('tab',{name:'Schedule',exact:true}).click();
   check(name+' scheduler booking',await page.getByText('Synthetic visit',{exact:true}).first().isVisible());
   await page.getByRole('tab',{name:'CRM',exact:true}).click();
   const form=page.getByRole('form',{name:'Reference form',exact:true});
   await form.getByLabel('Customer name').fill('Synthetic updated '+product);
   await form.getByRole('button',{name:'Save form'}).click();
   await page.getByRole('heading',{name:'Synthetic updated '+product,exact:true}).waitFor();
   check(name+' CRM host save',true);
   await page.getByRole('tab',{name:'Analytics',exact:true}).click();
   check(name+' analytics export available',await page.getByRole('region',{name:'Reference analytics',exact:true}).getByRole('button',{name:'Export CSV'}).isEnabled());
   await page.getByRole('tab',{name:'Notifications',exact:true}).click();
   await page.getByRole('button',{name:'Mark read: Synthetic reminder'}).click();
   check(name+' notification state',await page.getByText('Unread: 0',{exact:true}).count()===1);
   await page.getByRole('button',{name:'Web Core action',exact:true}).click();
   check(name+' Web Core callback',await page.locator('#web-core').getAttribute('data-clicked')==='yes');
   await page.reload();await page.waitForFunction(()=>document.documentElement.dataset.referenceHydrated==='yes');
   await page.getByRole('tab',{name:'CRM',exact:true}).click();
   check(name+' synthetic state reset',await page.getByRole('heading',{name:'Synthetic Alice',exact:true}).isVisible());
   phase='localized transport';await localizedTransport(page,name);
   phase='localized operations';await localizedOperations(page,name);
   check(name+' no browser errors',errors.length===0);
   check(name+' no external requests',external.length===0);
   report.scenarios.push({product,theme,status:'passed'});
  }catch(e){report.scenarios.push({product,theme,status:'failed',phase,errors,external});report.errors.push(name+' ['+phase+']: '+String(e));}
  finally{await context.close();}
 }
 for(const product of products)for(const theme of themes){
  try{await auditRegistry(browser,url,product,theme);}
  catch(e){report.errors.push(product+'/'+theme+' [separate axe document]: '+String(e));}
 }
 await standaloneWeb();
 check('all 12 scenarios completed',report.scenarios.length===12&&report.scenarios.every(x=>x.status==='passed'));
 check('all 12 registry axe scans',report.axe.length===12);
 check('no detected axe violations',report.axe.every(x=>x.violations.length===0));
}catch(e){report.errors.push(String(e));}
finally{
 if(browser)await browser.close();
 for(const server of servers)if(server.exitCode===null&&server.signalCode===null){await new Promise(ok=>{server.once('exit',ok);if(!server.kill()||server.exitCode!==null||server.signalCode!==null)ok();});}
 report.status=report.errors.length?'failed':'passed';
 await writeFile(join(out,'canonical-browser-acceptance.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({canonicalBrowserAcceptance:{engine,status:report.status,checks:report.checks.length,passed:report.checks.filter(x=>x.ok).length,scenarios:report.scenarios.length,axeScans:report.axe.length,violations:report.axe.reduce((n,x)=>n+x.violations.length,0),errors:report.errors}}));
 if(report.errors.length)process.exitCode=1;
}
