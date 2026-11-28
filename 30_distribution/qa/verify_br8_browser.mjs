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
const report={...input,engine,scope:'Canonical npm package-only reference workspace, English synthetic data; not production/native Safari or complete accessibility acceptance',checks:[],axe:[],errors:[],scenarios:[],publicationAllowed:false};
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
function check(name,ok){report.checks.push({name,ok:Boolean(ok)});assert.ok(ok,name);}
function run(command,args){const p=spawnSync(command,args,{cwd:host,encoding:'utf8',maxBuffer:16*1024*1024,env:{...process.env,NPM_CONFIG_CACHE:join(host,'.npm-cache')}});if(p.error||p.status!==0)throw Error(command+' failed: '+String(p.error??'')+'\n'+p.stdout+'\n'+p.stderr);return p.stdout.trim();}
let child,browser;
async function start(){
 child=spawn(process.execPath,['serve.mjs'],{cwd:host,env:{...process.env,PORT:'0'},stdio:['ignore','pipe','pipe']});
 return new Promise((ok,fail)=>{let output='';const timer=setTimeout(()=>fail(Error('Reference server timeout: '+output)),30000);
 child.stdout.on('data',buf=>{output+=buf;const m=output.match(/http:\/\/127\.0\.0\.1:(\d+)/);if(m){clearTimeout(timer);ok(m[0]);}});
 child.stderr.on('data',buf=>{output+=buf;});child.once('error',e=>{clearTimeout(timer);fail(e);});
 child.once('exit',code=>{clearTimeout(timer);fail(Error('Reference server exited '+code+': '+output));});});
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
   await context.route(target=>externalNetwork(target,url),route=>route.abort());
   context.on('request',req=>{if(externalNetwork(req.url(),url))external.push(new URL(req.url()).origin);});
   await context.routeWebSocket('**/*',ws=>{external.push('websocket:'+new URL(ws.url()).origin);ws.close();});
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
   phase='axe injection';await page.addScriptTag({path:axePath});
   phase='axe scan';
   // Match the passing source-browser harness: project the actual scan result
   // in the page instead of serializing the entire axe result across CDP/Juggler.
   const scan=await page.evaluate(async()=>{
    const x=await window.axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']}});
    return {violations:x.violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))})),
            incomplete:x.incomplete.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)}))};
   });
   report.axe.push({product,theme,page:'registry',...scan});
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
   check(name+' no browser errors',errors.length===0);
   check(name+' no external requests',external.length===0);
   report.scenarios.push({product,theme,status:'passed'});
  }catch(e){report.scenarios.push({product,theme,status:'failed',phase,errors,external});report.errors.push(name+' ['+phase+']: '+String(e));}
  finally{await context.close();}
 }
 check('all 12 scenarios completed',report.scenarios.length===12&&report.scenarios.every(x=>x.status==='passed'));
 check('all 12 registry axe scans',report.axe.length===12);
 check('no detected axe violations',report.axe.every(x=>x.violations.length===0));
}catch(e){report.errors.push(String(e));}
finally{
 if(browser)await browser.close();
 if(child&&child.exitCode===null&&child.signalCode===null){await new Promise(ok=>{child.once('exit',ok);if(!child.kill()||child.exitCode!==null||child.signalCode!==null)ok();});}
 report.status=report.errors.length?'failed':'passed';
 await writeFile(join(out,'canonical-browser-acceptance.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({canonicalBrowserAcceptance:{engine,status:report.status,checks:report.checks.length,passed:report.checks.filter(x=>x.ok).length,scenarios:report.scenarios.length,axeScans:report.axe.length,violations:report.axe.reduce((n,x)=>n+x.violations.length,0),errors:report.errors}}));
 if(report.errors.length)process.exitCode=1;
}
