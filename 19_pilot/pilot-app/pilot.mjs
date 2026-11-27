import { setTheme,button,field,table,dialog,toastRegion } from './node_modules/@taktera/ui-core/index.mjs';
const $=selector=>document.querySelector(selector);
const data=[{id:'0001',name:'Aster',value:15},{id:'0002',name:'Bluebird',value:42},{id:'0003',name:'Cedar',value:8}];
const root=$('#app');const locale=$('#locale');let modal;
function render(){
 setTheme(root,{product:$('#product').value,theme:$('#theme').value});document.documentElement.lang=locale.value;
 const lang=locale.value, controls=$('#controls'),grid=$('#grid'),container=$('#modal');
 controls.replaceChildren();grid.replaceChildren();container.replaceChildren();
 const name=field({label:lang==='ru'?'Имя':'Name',name:'person'});controls.append(name.element);
 modal=dialog({title:lang==='ru'?'Новая запись':'New record',content:lang==='ru'?'Тестовое модальное окно':'Test modal',locale:lang,onClose:()=>{$('#pilot-result').textContent='Closed';}});
 container.append(modal.element);
 controls.append(button({label:lang==='ru'?'Создать':'Create',onClick:()=>modal.open()}));
 const toasts=toastRegion({locale:lang});controls.append(toasts.element);
 controls.append(button({label:lang==='ru'?'Уведомить':'Notify',variant:'secondary',onClick:()=>toasts.push(lang==='ru'?'Запись создана':'Record created','success')}));
 grid.append(table({columns:[{key:'id',label:'ID',sortable:true},{key:'name',label:lang==='ru'?'Название':'Name',sortable:true},{key:'value',label:lang==='ru'?'Значение':'Value',sortable:true}],rows:data,rowKey:x=>x.id,pageSize:2,locale:lang}).element);
}
for(const id of ['product','theme','locale'])$('#'+id).addEventListener('change',render);
render();
