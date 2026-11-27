import {chromium,firefox,webkit} from 'playwright';
import {createServer} from 'node:http';
import {readFile,mkdir,mkdtemp,rm,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
const root=fileURLToPath(new URL('../../../',import.meta.url)),engine=process.argv[2]||'chromium',engines={chromium,firefox,webkit};
const base=resolve(root,'21_alpha6'),out=resolve(root,'28_engineering/qa/results','board-'+engine),profile=await mkdtemp(resolve(tmpdir(),'taktera-board-'));
const html=await readFile(resolve(base,'dashboard.html'),'utf8'),seed=JSON.parse(html.match(/<script id="seed" type="application\/json">([\s\S]*?)<\/script>/)[1]);
const key='taktera-design-board-alpha6-v1',snapshotKey=key+'-github-snapshot-v1';
const allowed={'/dashboard.html':'text/html; charset=utf-8','/dashboard.js':'text/javascript; charset=utf-8','/dashboard.css':'text/css; charset=utf-8'};
const server=createServer(async(req,res)=>{const path=new URL(req.url,'http://localhost').pathname;if(!Object.hasOwn(allowed,path)){res.writeHead(404).end();return}try{res.writeHead(200,{'Content-Type':allowed[path]}).end(await readFile(resolve(base,path.slice(1))))}catch{res.writeHead(500).end()}});
await mkdir(out,{recursive:true});await new Promise(ok=>server.listen(0,'127.0.0.1',ok));
let context;const checks=[],errors=[];const check=(name,ok)=>{checks.push({name,ok:Boolean(ok)});assert.ok(ok,name)};
const url='http://127.0.0.1:'+server.address().port+'/dashboard.html';
const old=structuredClone(seed);old.tasks=old.tasks.filter(t=>t.id!=='BR5-06');old.release='old';const task=old.tasks.find(t=>t.id==='BR4-08');task.status='blocked';task.description='Local unsaved-by-server decision';task.owner='Local QA';old.tasks.push({id:'CUSTOM-777',title:'Local task',phase:'Local',priority:'P1',status:'planned',dependencies:[],description:'preserve',owner:'',due:''});old.history.unshift({at:'2026-11-28',message:'Local history sentinel'});
const file=(name,obj)=>({name,mimeType:'application/json',buffer:Buffer.from(JSON.stringify(obj))});
try{
 context=await engines[engine].launchPersistentContext(profile,{acceptDownloads:true});
 let page=await context.newPage();page.on('pageerror',e=>errors.push(String(e)));await page.goto(url);await page.evaluate(([k,v])=>localStorage.setItem(k,JSON.stringify(v)),[key,old]);await page.reload();
 const card=id=>page.locator('.ticket').filter({has:page.locator('.id',{hasText:new RegExp('^'+id+'$')})});
 check('local edited status and owner',await card('BR4-08').locator('p').textContent()==='Local unsaved-by-server decision');check('new seed task appended',await card('BR5-06').count()===1);check('custom task kept',await card('CUSTOM-777').count()===1);check('local history retained',await page.locator('#history').getByText('Local history sentinel').count()===1);
 await card('BR4-08').click();check('local status unchanged',await page.locator('#taskStatus').inputValue()==='blocked');check('owner unchanged',await page.locator('#owner').inputValue()==='Local QA');await page.locator('#title').fill('Local edited title');await page.locator('#taskForm button[type=submit]').click();
 const before=await page.evaluate(k=>localStorage.getItem(k),key);
 const snapshot={schemaVersion:1,repository:'disxlab/Taktera-Design-System',capturedAt:'2026-11-28T00:00:00Z',issues:[{number:8,state:'closed'}]};
 await page.locator('#issueFile').setInputFiles(file('snapshot.json',snapshot));await page.waitForFunction(k=>Boolean(localStorage.getItem(k)),snapshotKey);
 check('issue state shown separately',(await card('BR4-08').textContent()).includes('GitHub #8 · closed'));check('snapshot did not write task data',await page.evaluate(k=>localStorage.getItem(k),key)===before);
 const prior=await page.evaluate(k=>localStorage.getItem(k),snapshotKey);const alert=page.waitForEvent('dialog');const invalid=page.locator('#issueFile').setInputFiles(file('bad.json',{...snapshot,repository:'other/repo'}));const dialog=await alert;await dialog.dismiss();await invalid;check('invalid snapshot rejected',await page.evaluate(k=>localStorage.getItem(k),snapshotKey)===prior);
 await card('DS-001').click();page.once('dialog',d=>d.accept());await page.locator('#deleteTask').click();check('seed deletion applied',await card('DS-001').count()===0);
 const dl=page.waitForEvent('download');await page.locator('#export').click();const downloaded=await dl;const exported=JSON.parse(await readFile(await downloaded.path(),'utf8'));check('export includes deletion tombstone',exported.deletedSeedIds.includes('DS-001'));check('export keeps user task',exported.tasks.some(t=>t.id==='CUSTOM-777'));
 await context.close();context=null;context=await engines[engine].launchPersistentContext(profile,{acceptDownloads:true});page=await context.newPage();page.on('pageerror',e=>errors.push(String(e)));await page.goto(url);
 check('persistent restart retains edit',(await card('BR4-08').textContent()).includes('Local edited title'));check('persistent restart retains deletion',await card('DS-001').count()===0);check('persistent restart retains snapshot',(await card('BR4-08').textContent()).includes('GitHub #8 · closed'));check('persistent restart retains custom and new seed',await card('CUSTOM-777').count()===1&&await card('BR5-06').count()===1);
 page.once('dialog',d=>d.dismiss());await page.locator('#reset').click();check('cancel reset keeps local tasks',await card('CUSTOM-777').count()===1);
 page.once('dialog',d=>d.accept());await page.locator('#importFile').setInputFiles(file('backup.json',exported));await page.waitForFunction(()=>document.getElementById('toast').textContent.includes('Резервная копия'));check('restore backup retains tombstone and edit',await card('DS-001').count()===0&&(await card('BR4-08').textContent()).includes('Local edited title'));
 check('no JS errors',errors.length===0);
}catch(e){errors.push(String(e))}
finally{if(context)await context.close();await new Promise(ok=>server.close(ok));await rm(profile,{recursive:true,force:true});await writeFile(resolve(out,'report.json'),JSON.stringify({engine,checks,errors},null,2)+'\n')}
console.log(JSON.stringify({engine,boardChecks:checks.length,passed:checks.filter(x=>x.ok).length,errors}));if(errors.length)process.exitCode=1;
