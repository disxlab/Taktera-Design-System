/* Local component showcase: fixed demo fixtures, no network, no persistence. */
(function(){
'use strict';
const ui=globalThis.TakteraUI;
if(!ui)throw new Error('Load Taktera UI Web Core before demo.js');
const $=id=>document.getElementById(id);
const body=document.body;
const products={platform:'Platform',clinic:'Clinic',beauty:'Beauty',spa:'Spa',fitness:'Fitness',travel:'Travel'};
const toasts=ui.toastRegion();$('toastMount').append(toasts.element);
const records=[{name:'Александр В.',type:'Консультация',date:'24.11.2026',status:'Подтверждено'},
{name:'Мария С.',type:'Повторный визит',date:'25.11.2026',status:'Ожидание'},
{name:'Ирина М.',type:'Процедура',date:'26.11.2026',status:'Подтверждено'},
{name:'Ольга Н.',type:'Консультация',date:'27.11.2026',status:'Завершено'},
{name:'Дмитрий П.',type:'Повторный визит',date:'28.11.2026',status:'Ожидание'},
{name:'Светлана К.',type:'Процедура',date:'29.11.2026',status:'Подтверждено'},
{name:'Елена А.',type:'Консультация',date:'30.11.2026',status:'Ожидание'}];
const dialog=ui.dialog({title:'Новая демонстрационная запись',content:'Это тестовый диалог. Данные не сохраняются.',
  onConfirm:()=>{toasts.push('Демонстрационная запись создана','success');return true;}});
$('dialogMount').append(dialog.element);
const actions=$('buttonDemo');
actions.append(ui.button({label:'Создать запись',onClick:()=>dialog.open()}),
 ui.button({label:'Вторичное действие',variant:'secondary',onClick:()=>toasts.push('Действие выполнено')}),
 ui.button({label:'Недоступно',disabled:true}),
 ui.button({label:'Загрузка',loading:true}));
const nameField=ui.field({label:'Название услуги',placeholder:'Например, консультация',required:true});
const invalid=ui.field({label:'Поле с ошибкой',value:'',error:'Это поле необходимо заполнить'});
const select=ui.select({label:'Тип визита',options:[{value:'first',label:'Первичный'},{value:'repeat',label:'Повторный'}]});
const checked=ui.checkbox({label:'Напоминание включено',checked:true,switchRole:true});
$('formDemo').append(nameField.element,invalid.element,select.element,checked.element);
const statuses=$('statusDemo');for(const [tone,label] of Object.entries({success:'Готово',info:'В работе',warning:'Внимание',error:'Ошибка'}))statuses.append(ui.status({tone,label}));
$('alertDemo').append(ui.alert({title:'Семантические цвета',message:'Цвет продукта не заменяет цвет предупреждения или ошибки.'}));
$('tabsDemo').append(ui.tabs({items:[{id:'summary',label:'Обзор',content:'Общий журнал и показатели.'},{id:'settings',label:'Настройки',content:'Настройки продукта и доступа.'},{id:'history',label:'История',content:'Последние действия.'}]}).element);
$('tableDemo').append(ui.table({columns:[{key:'name',label:'Клиент',sortable:true},{key:'type',label:'Услуга'},{key:'date',label:'Дата',sortable:true},{key:'status',label:'Статус'}],rows:records,pageSize:4,rowKey:r=>r.name}).element);
function update(){ui.setTheme(body,{product:$('product').value,theme:$('theme').value});$('variantBadge').textContent=`${products[$('product').value].toUpperCase()} / ${$('theme').value.toUpperCase()}`;}
$('product').addEventListener('change',update);$('theme').addEventListener('change',update);update();
globalThis.TakteraShowcase={ui,dialog,table:$('tableDemo').querySelector('table')};
})();
