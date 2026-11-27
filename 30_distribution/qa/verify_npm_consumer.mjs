import {mkdtemp,mkdir,readFile,writeFile,cp,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createRequire} from 'node:module';
import {spawnSync,spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {createServer} from 'node:http';
import assert from 'node:assert/strict';
const root=fileURLToPath(new URL('../../',import.meta.url)),react=join(root,'17_packages/react'),web=join(root,'17_packages/web-core');
const reportDir=join(root,'30_distribution/qa/results/npm');await mkdir(reportDir,{recursive:true});
const work=await mkdtemp(join(tmpdir(),'taktera-consumer-')),archives=join(work,'archives'),consumer=join(work,'consumer');await mkdir(archives);
const report={checks:[],packages:[],errors:[],node:process.version};
function check(name,ok){report.checks.push({name,ok:Boolean(ok)});assert.ok(ok,name)}
function run(command,args,cwd){const p=spawnSync(command,args,{cwd,encoding:'utf8',maxBuffer:16*1024*1024});if(p.error||p.status!==0)throw Error(command+' '+args.join(' ')+' failed: '+String(p.error??'')+'\n'+p.stdout+'\n'+p.stderr);return p.stdout}
const npm=(args,cwd)=>run('npm',args,cwd); // Linux release runner
let browser,server;const starters=[];
async function startStarter(dir){const child=spawn(process.execPath,['serve.mjs'],{cwd:dir,env:{...process.env,PORT:'0'},stdio:['ignore','pipe','pipe']});starters.push(child);return new Promise((ok,fail)=>{let output='';const timer=setTimeout(()=>fail(Error('Starter server timeout: '+output)),30000);child.stdout.on('data',buf=>{output+=buf;const match=output.match(/http:\/\/127\.0\.0\.1:(\d+)/);if(match){clearTimeout(timer);ok(match[0])}});child.stderr.on('data',buf=>{output+=buf});child.once('error',e=>{clearTimeout(timer);fail(e)});child.once('exit',code=>{clearTimeout(timer);fail(Error('Starter server exited '+code+': '+output))})})}
try{
 const locked=JSON.parse(await readFile(join(react,'package-lock.json'),'utf8'));
 const ver=name=>{const v=locked.packages['node_modules/'+name]?.version;if(!v)throw Error('Missing locked version: '+name);return v};
 const packed=[];
 for(const dir of [react,web]){
  const result=JSON.parse(npm(['pack','--json','--ignore-scripts','--pack-destination',archives],dir))[0],file=join(archives,result.filename);
  const entries=result.files.map(f=>f.path);
  check(result.name+' excludes source/test/private config',entries.every(p=>!/(^|\/)(node_modules|qa|src|\.git|\.npmrc)(\/|$)/.test(p)));
  const expected=result.name==='@taktera/ui-react'?['dist/index.js','dist/index.d.ts','dist/AdvancedAnalyticsDashboard.js','dist/ResourceScheduler.js','styles.css']:['index.mjs','index.d.mts','taktera-ui.css','taktera-ui.js'];
  check(result.name+' public files',expected.every(p=>entries.includes(p)));
  report.packages.push({name:result.name,version:result.version,filename:result.filename,sha256:createHash('sha256').update(await readFile(file)).digest('hex'),entries});
  packed.push({name:result.name,file});
 }
 run('python3',[join(root,'30_distribution/taktera.py'),'init','react','--packages',archives,'--output',consumer],root);
 check('React CLI creates local package inventory',JSON.parse(await readFile(join(consumer,'package-inventory.json'),'utf8')).length===2);
 const duplicate=spawnSync('python3',[join(root,'30_distribution/taktera.py'),'init','react','--packages',archives,'--output',consumer],{cwd:root,encoding:'utf8'});
 check('CLI refuses overwrite',duplicate.status!==0&&duplicate.stderr.includes('Refusing to overwrite'));
 npm(['install','--package-lock-only','--ignore-scripts','--no-audit','--no-fund'],consumer);
 npm(['ci','--no-audit','--no-fund'],consumer);
 check('independent clean npm install',true);
 run(process.execPath,['node_modules/typescript/bin/tsc','-p','tsconfig.json'],consumer);check('strict public TypeScript consumer',true);
 const req=createRequire(join(consumer,'package.json')),React=req('react'),{renderToString}=req('react-dom/server'),{App}=await import(pathToFileURL(join(consumer,'dist/App.js')).href);
 const markup=renderToString(React.createElement(App));check('installed package SSR',markup.includes('Taktera reference workspace')&&markup.includes('Synthetic Alice'));
 const bundle=await req('esbuild').build({entryPoints:[join(consumer,'client.tsx')],bundle:true,write:false,platform:'browser',format:'iife',jsx:'automatic',define:{'process.env.NODE_ENV':'"production"'}});
 const reactCss=await readFile(req.resolve('@taktera/ui-react/styles.css')),webCss=await readFile(req.resolve('@taktera/ui-core/styles.css'));
 check('installed CSS and classic script exports',reactCss.length>1000&&webCss.length>1000&&!!req.resolve('@taktera/ui-core/script.js'));
 const html='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Taktera reference</title><link rel="stylesheet" href="/web.css"><link rel="stylesheet" href="/react.css"></head><body><div id="root">'+markup+'</div><div id="web-core" class="tku-root"></div><script src="/app.js" defer></script></body></html>';
 const assets={'/':['text/html; charset=utf-8',html],'/app.js':['text/javascript',bundle.outputFiles[0].contents],'/web.css':['text/css',webCss],'/react.css':['text/css',reactCss]};
 server=createServer((req,res)=>{const item=assets[req.url];if(!item){res.writeHead(404).end();return}res.writeHead(200,{'Content-Type':item[0]}).end(item[1])});
 await new Promise(ok=>server.listen(0,'127.0.0.1',ok));
 const playwright=createRequire(join(react,'package.json'))('playwright');browser=await playwright.chromium.launch();const page=await browser.newPage();
 const errors=[];page.on('pageerror',e=>errors.push(String(e)));page.on('console',m=>{if(m.type()==='error'&&!m.text().includes('404'))errors.push(m.text())});
 await page.goto('http://127.0.0.1:'+server.address().port+'/');await page.waitForFunction(()=>document.documentElement.dataset.referenceHydrated==='yes');
 const grid=page.getByRole('region',{name:'Reference registry',exact:true});
 await grid.getByRole('textbox',{name:'Search registry'}).fill('Bob');check('packed DataGrid interaction',await grid.getByText('Synthetic Bob',{exact:true}).count()===1&&await grid.getByText('Synthetic Alice',{exact:true}).count()===0);
 await page.getByRole('tab',{name:'Schedule',exact:true}).click();check('packed Scheduler',await page.getByText('Synthetic visit',{exact:true}).first().isVisible());
 await page.getByRole('tab',{name:'CRM',exact:true}).click();const form=page.getByRole('form',{name:'Reference form',exact:true});await form.getByLabel('Customer name').fill('Updated reference');await form.getByRole('button',{name:'Save form'}).click();await page.getByRole('heading',{name:'Updated reference',exact:true}).waitFor();check('packed CRM host callback',true);
 await page.getByRole('tab',{name:'Analytics',exact:true}).click();check('packed analytics',await page.getByRole('region',{name:'Reference analytics',exact:true}).getByRole('button',{name:'Export CSV'}).isEnabled());
 await page.getByRole('tab',{name:'Notifications',exact:true}).click();await page.getByRole('button',{name:'Mark read: Synthetic reminder'}).click();check('packed notification callback',await page.getByText('Unread: 0',{exact:true}).count()===1);
 await page.getByLabel('Theme',{exact:true}).selectOption('dark');await page.getByLabel('Product',{exact:true}).selectOption('fitness');check('packed product/theme switch',await page.locator('#root .tku-root').getAttribute('data-theme')==='dark'&&await page.locator('#root .tku-root').getAttribute('data-product')==='fitness');
 await page.getByRole('button',{name:'Web Core action',exact:true}).click();check('packed Web Core interaction',await page.locator('#web-core').getAttribute('data-clicked')==='yes');
 check('no hydration or browser errors',errors.length===0);
 const starterUrl=await startStarter(consumer),starterPage=await browser.newPage();
 const starterErrors=[];starterPage.on('pageerror',e=>starterErrors.push(String(e)));starterPage.on('console',m=>{if(m.type()==='error'&&!m.text().includes('404'))starterErrors.push(m.text())});
 try{await starterPage.goto(starterUrl);await starterPage.waitForFunction(()=>document.documentElement.dataset.referenceHydrated==='yes');check('React CLI starter launches and hydrates',await starterPage.getByRole('heading',{name:'Taktera reference workspace'}).isVisible()&&starterErrors.length===0)}finally{await starterPage.close()}
 const webStarter=join(work,'web-starter');run('python3',[join(root,'30_distribution/taktera.py'),'init','web','--packages',archives,'--output',webStarter],root);
 npm(['install','--package-lock-only','--ignore-scripts','--no-audit','--no-fund'],webStarter);npm(['ci','--no-audit','--no-fund'],webStarter);
 const webUrl=await startStarter(webStarter),webPage=await browser.newPage();try{await webPage.goto(webUrl);await webPage.getByRole('button',{name:'Test action',exact:true}).click();check('Web CLI starter installs and runs',await webPage.getByRole('status').textContent()==='Action completed')}finally{await webPage.close()}
 const portal=await browser.newPage();try{await portal.goto(pathToFileURL(join(root,'30_distribution/portal/index.html')).href);await portal.getByLabel('Search documentation').fill('NuGet');check('Portal filters catalog',await portal.locator('[data-doc]:visible').count()>0&&await portal.locator('[data-doc]:visible').count()<await portal.locator('[data-doc]').count());await portal.getByRole('button',{name:'Dark theme',exact:true}).click();check('Portal theme selection',await portal.locator('main').getAttribute('data-theme')==='dark')}finally{await portal.close()}
 await page.screenshot({path:join(reportDir,'reference.png'),fullPage:true});
 for(const p of packed)await cp(p.file,join(reportDir,p.file.split('/').at(-1)));
 await cp(join(consumer,'package-lock.json'),join(reportDir,'consumer-package-lock.json'));
}catch(e){report.errors.push(String(e));process.exitCode=1}
finally{for(const child of starters){if(child.exitCode===null&&child.signalCode===null){await new Promise(ok=>{child.once('exit',ok);if(!child.kill()||child.exitCode!==null||child.signalCode!==null)ok()})}}if(browser)await browser.close();if(server)await new Promise(ok=>server.close(()=>ok()));await writeFile(join(reportDir,'report.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({npmConsumerChecks:report.checks.length,passed:report.checks.filter(x=>x.ok).length,errors:report.errors}));await rm(work,{recursive:true,force:true})}
