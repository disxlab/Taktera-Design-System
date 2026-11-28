import {createSyntheticTransport} from './synthetic-transport.mjs';
// Standalone package-only host, no React and no network transport.
const root=document.getElementById('root'),ui=globalThis.TakteraUI;
ui.setTheme(root,{product:'platform',theme:'light'});
root.append(ui.button({label:'Test action',onClick:()=>{document.getElementById('result').textContent='Action completed'}}));
const labels={
 en:{region:'Web synthetic transport',name:'Customer name',save:'Save record',fail:'Fail next request',retry:'Retry same request',replay:'Replay last request',compete:'Simulate competing write',reload:'Reload record',external:'Synthetic competing name',validation:'Invalid customer name',unavailable:'Temporarily unavailable',applied:'Saved',conflict:'Version conflict',idle:'Ready',unexpected:'Unexpected synthetic result'},
 ru:{region:'Web синтетический транспорт',name:'Имя клиента',save:'Сохранить запись',fail:'Ошибка следующего запроса',retry:'Повторить тот же запрос',replay:'Повторить сохранённый запрос',compete:'Имитировать параллельную запись',reload:'Загрузить запись',external:'Синтетическое конкурентное имя',validation:'Недопустимое имя клиента',unavailable:'Временно недоступно',applied:'Сохранено',conflict:'Конфликт версий',idle:'Готово',unexpected:'Неожиданный результат'}
};
let product='platform',theme='light',locale='en';
const options=values=>values.map(value=>({value,label:value}));
const controls=ui.select({label:'Web product',options:options(['platform','clinic','beauty','spa','fitness','travel']),value:product,onChange:value=>{product=value;ui.setTheme(root,{product,theme});}});
const themes=ui.select({label:'Web theme',options:options(['light','dark']),value:theme,onChange:value=>{theme=value;ui.setTheme(root,{product,theme});}});
const language=ui.select({label:'Web language / Язык',options:[{value:'en',label:'English'},{value:'ru',label:'Русский'}],value:locale,onChange:value=>{locale=value;mount();}});
const region=document.createElement('section');
root.append(controls.element,themes.element,language.element,region);
function mount(){
 const l=labels[locale],api=createSyntheticTransport();
 let record=api.read('p1'),version=record.version,serial=0,last=null,busy=false,status='idle';
 region.replaceChildren();region.lang=locale;region.setAttribute('aria-label',l.region);
 const name=document.createElement('p'),revision=document.createElement('p'),notice=document.createElement('div');
 name.dataset.testid='transport-record';revision.dataset.testid='transport-version';notice.dataset.testid='transport-status';
 const field=ui.field({label:l.name,value:record.name});
 const save=ui.button({label:l.save,onClick:()=>void execute({id:'p1',name:field.input.value,version,requestId:'editor-'+(++serial)})});
 const fail=ui.button({label:l.fail,variant:'secondary',onClick:()=>api.failNext()});
 const retry=ui.button({label:l.retry,variant:'secondary',onClick:()=>{if(last)void execute(last)}});
 const replay=ui.button({label:l.replay,variant:'secondary',onClick:()=>{if(last)void execute(last)}});
 const compete=ui.button({label:l.compete,variant:'secondary',onClick:()=>void competing()});
 const reload=ui.button({label:l.reload,variant:'secondary',onClick:()=>{record=api.read('p1');version=record.version;field.input.value=record.name;status='idle';last=null;render();}});
 function render(){
  name.textContent=record.name;revision.textContent=record.version;notice.dataset.status=status;
  notice.replaceChildren(ui.alert({tone:['validation','unavailable','conflict'].includes(status)?'error':status==='applied'?'success':'info',message:l[status]??l.unexpected}));
  field.setError(status==='validation'?l.validation:'');
  field.input.disabled=busy;for(const b of [save,fail,compete,reload])b.disabled=busy;
  retry.disabled=busy||status!=='unavailable';replay.disabled=busy||status!=='applied';
 }
 async function execute(request){
  if(busy)return;busy=true;render();
  try{const result=await api.save(request);last=request;status=result.status;record=api.read('p1');if(status==='applied'){version=record.version;field.input.value=record.name;}}
  finally{busy=false;render();}
 }
 async function competing(){
  if(busy)return;busy=true;render();
  try{const result=await api.save({id:'p1',name:l.external,version:api.read('p1').version,requestId:'competitor-'+(++serial)});if(result.status!=='applied')throw Error('Synthetic competing write failed');record=api.read('p1');status='idle';}
  finally{busy=false;render();}
 }
 region.append(name,revision,field.element,save,fail,retry,replay,compete,reload,notice);render();
}
mount();document.documentElement.dataset.webHydrated='yes';
