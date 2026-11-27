/* Framework-free JS logic test for the offline demo. This is NOT browser QA. */
const assert = require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.resolve(__dirname,'..');
class FakeElement{
  constructor(value=''){this.value=value;this.listeners={};this.src='';this.alt='';this.textContent='';}
  addEventListener(name,fn){this.listeners[name]=fn;}
  change(){this.listeners.change();}
  click(){this.listeners.click();}
}
const elements={product:new FakeElement('clinic'),theme:new FakeElement('light'),'brand-logo':new FakeElement(),'save':new FakeElement(),'main-action':new FakeElement(),'notification':new FakeElement()};
const document={getElementById(id){assert.ok(elements[id],id);return elements[id];},documentElement:{dataset:{}}};
vm.runInNewContext(fs.readFileSync(path.join(root,'12_examples/preview.js'),'utf8'),{document,Set});
const products=['platform','clinic','beauty','spa','fitness','travel'];
for(const p of products){
 elements.product.value=p;elements.product.change();
 for(const t of ['light','dark']){
  elements.theme.value=t;elements.theme.change();
  assert.equal(document.documentElement.dataset.product,p);
  assert.equal(document.documentElement.dataset.theme,t);
  assert.ok(elements['brand-logo'].src.endsWith(`${p}-ru-${t}.svg`));
  assert.ok(elements['brand-logo'].alt.startsWith('Taktera '));
 }
}
elements.save.click();assert.ok(elements.notification.textContent.includes('данные не сохраняются'));
elements['main-action'].click();assert.ok(elements.notification.textContent.includes('действие выполнено'));
console.log('OK: 12 product/theme JS states; logo selection; demo actions (not rendered-browser tests)');
