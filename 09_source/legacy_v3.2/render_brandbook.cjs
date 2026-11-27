const fs=require('fs');
const path=require('path');
const {pathToFileURL}=require('url');
const runtime='C:/Users/sgkomc/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const sharp=require(path.join(runtime,'sharp'));
const {chromium}=require(path.join(runtime,'playwright'));
const root='C:/Users/sgkomc/Documents/Persona/output/Taktera_Brand_Package_v3.2';
const qa='C:/Users/sgkomc/Documents/Persona/work/brand-v3.2/qa';
fs.mkdirSync(qa,{recursive:true});
async function main(){
  for(const kind of ['master','products','products/ru']){
    const dir=path.join(root,'02_logos',kind,'svg');
    for(const f of fs.readdirSync(dir).filter(x=>x.endsWith('.svg'))){
      await sharp(path.join(dir,f),{density:216}).png().toFile(path.join(root,'02_logos',kind,'png',f.replace('.svg','.png')));
    }
  }
  for(const f of fs.readdirSync(path.join(root,'03_icons/app/svg'))){
    for(const size of [16,24,32,48,64,128,256,512,1024]){
      await sharp(path.join(root,size<=24?'03_icons/app/micro/svg':'03_icons/app/svg',f),{density:576}).resize(size,size).png().toFile(path.join(root,'03_icons/app/png',f.replace('.svg',`-${size}.png`)));
    }
  }
  for(const f of fs.readdirSync(path.join(root,'06_templates')).filter(f=>f.endsWith('.svg'))){
    await sharp(path.join(root,'06_templates',f)).png().toFile(path.join(root,'06_templates',f.replace('.svg','.png')));
  }
  const browser=await chromium.launch({headless:true,executablePath:'C:/Users/sgkomc/AppData/Local/ms-playwright/chromium-1223/chrome-win64/chrome.exe'});
  const page=await browser.newPage({viewport:{width:1440,height:1100},deviceScaleFactor:1});
  const errors=[];page.on('pageerror',e=>errors.push(String(e)));
  await page.goto(pathToFileURL(path.join(root,'Taktera-brandbook-v3.2.html')).href);
  await page.evaluate(()=>document.fonts.ready);
  const inspect=await page.evaluate(()=>({font:document.fonts.check('700 16px Inter'),images:[...document.images].filter(i=>!i.complete||i.naturalWidth===0).map(i=>i.src),pages:[...document.querySelectorAll('.page')].map(p=>({id:p.id,contentBottom:p.querySelector('.content').getBoundingClientRect().bottom-p.getBoundingClientRect().top,footerTop:p.querySelector('footer').getBoundingClientRect().top-p.getBoundingClientRect().top}))}));
  fs.writeFileSync(path.join(qa,'layout-check.json'),JSON.stringify({...inspect,errors},null,2));
  for(let i=0;i<inspect.pages.length;i++)await page.locator('.page').nth(i).screenshot({path:path.join(qa,`page-${String(i+1).padStart(2,'0')}.png`)});
  fs.copyFileSync(path.join(qa,'page-02.png'),path.join(root,'01_brandbook/product-family.png'));
  fs.copyFileSync(path.join(qa,'page-13.png'),path.join(root,'01_brandbook/product-family-ru.png'));
  fs.copyFileSync(path.join(qa,'page-14.png'),path.join(root,'01_brandbook/app-icon-sizes.png'));
  await page.pdf({path:path.join(root,'01_brandbook/Taktera-brandbook-v3.2.pdf'),printBackground:true,preferCSSPageSize:true});
  await page.setViewportSize({width:390,height:844});
  await page.screenshot({path:path.join(qa,'mobile.png'),fullPage:false});
  const mobile=await page.evaluate(()=>({viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth}));
  await browser.close();
  const thumbs=[];
  for(let i=0;i<inspect.pages.length;i++)thumbs.push({input:await sharp(path.join(qa,`page-${String(i+1).padStart(2,'0')}.png`)).resize(449,318).toBuffer(),left:(i%3)*449,top:Math.floor(i/3)*318});
  await sharp({create:{width:1347,height:Math.ceil(inspect.pages.length/3)*318,channels:3,background:'#e7e8ea'}}).composite(thumbs).png().toFile(path.join(qa,'contact-sheet.png'));
  fs.copyFileSync(__filename,path.join(root,'09_source/render_brandbook.cjs'));
  console.log(JSON.stringify({...inspect,mobile,errors}));
}
main().catch(e=>{console.error(e);process.exit(1)});
