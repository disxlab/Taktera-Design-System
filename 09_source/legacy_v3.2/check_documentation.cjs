const fs=require('fs'),path=require('path');
const {pathToFileURL}=require('url');
const {chromium}=require('C:/Users/sgkomc/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root='C:/Users/sgkomc/Documents/Persona/output/Taktera_Brand_Package_v3.2';
const qa='C:/Users/sgkomc/Documents/Persona/work/brand-v3.2/qa';
async function main(){
  const browser=await chromium.launch({headless:true,executablePath:'C:/Users/sgkomc/AppData/Local/ms-playwright/chromium-1223/chrome-win64/chrome.exe'});
  const page=await browser.newPage({viewport:{width:1440,height:1100}});
  const errors=[]; page.on('pageerror',e=>errors.push(String(e)));
  await page.goto(pathToFileURL(path.join(root,'START-HERE.html')).href);
  await page.evaluate(()=>document.fonts.ready);
  const state=await page.evaluate(()=>({chapters:document.querySelectorAll('main section').length,font:document.fonts.check('700 16px Inter'),images:[...document.images].filter(i=>!i.complete||!i.naturalWidth).map(i=>i.src),links:[...document.querySelectorAll('a[href]')].map(a=>a.getAttribute('href')),viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth}));
  const missing=state.links.filter(x=>!x.startsWith('#')&&!/^https?:/.test(x)&&!fs.existsSync(path.join(root,x)));
  const badAnchors=await page.evaluate(()=>[...document.querySelectorAll('a[href^="#"]')].filter(a=>!document.getElementById(a.getAttribute('href').slice(1))).map(a=>a.getAttribute('href')));
  await page.screenshot({path:path.join(qa,'documentation-desktop.png')});
  await page.locator('[id="03-color-and-themes"]').screenshot({path:path.join(qa,'documentation-colors.png')});
  await page.setViewportSize({width:390,height:844});
  await page.evaluate(()=>{document.documentElement.style.scrollBehavior='auto';scrollTo({top:0,left:0,behavior:'instant'});});
  await page.screenshot({path:path.join(qa,'documentation-mobile.png')});
  const mobile=await page.evaluate(()=>({viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth}));
  const proof=await browser.newPage({viewport:{width:1440,height:1100}});
  await proof.goto(pathToFileURL(path.join(root,'Taktera-brandbook-v3.2.html')).href);
  await proof.evaluate(async()=>{
    document.querySelectorAll('#p14 img').forEach(i=>{i.src=i.src.replace('-light-','-dark-');});
    await Promise.all([...document.querySelectorAll('#p14 img')].map(i=>i.decode()));
  });
  await proof.locator('#p14').screenshot({path:path.join(root,'01_brandbook/app-icon-sizes-dark.png')});
  await browser.close();
  if(state.chapters!==9||!state.font||state.images.length||missing.length||badAnchors.length||errors.length||mobile.viewport!==mobile.scrollWidth||state.viewport!==state.scrollWidth)throw new Error(JSON.stringify({state,missing,badAnchors,errors,mobile}));
  const report={date:'2026-10-18',version:'3.2',chapters:9,localLinks:'all targets exist',anchors:'all targets exist',images:'all loaded',font:'local Inter loaded',browserErrors:errors,desktop:{viewport:state.viewport,scrollWidth:state.scrollWidth},mobile,contrast:'36 explicit color pairs calculated in 10_documentation/COLOR-CONTRAST.json; Spa and Fitness paper limitations documented',scope:'documentation and package resources, not application validation'};
  fs.writeFileSync(path.join(root,'DOCUMENTATION-VALIDATION.json'),JSON.stringify(report,null,2));
  fs.copyFileSync(__filename,path.join(root,'09_source/check_documentation.cjs'));
  console.log(JSON.stringify(report));
}
main().catch(e=>{console.error(e);process.exit(1)});
