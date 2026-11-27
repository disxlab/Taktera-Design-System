import * as React from 'react';
import { TakteraProvider, Button, Field, Select, Checkbox, Switch, Tabs, DataTable, Dialog, Pagination, Status, AdvancedDataGrid, RemoteDataGrid } from '../src/index';
import type { Product, Theme, GridTransport } from '../src/index';
const rows=[{id:'a',name:'10'},{id:'b',name:'2'},{id:'c',name:'<img src=x onerror=alert(1)>'}];
const gridRows=[{id:'r1',name:'Record 10',amount:10,status:'open'},{id:'r2',name:'Record 2',amount:2,status:'open'},{id:'r3',name:'Other',amount:30,status:'closed'}];
const gridColumns=[{id:'name',label:'Название записи',value:(r:typeof gridRows[number])=>r.name},{id:'amount',label:'Сумма',value:(r:typeof gridRows[number])=>r.amount},{id:'status',label:'Статус записи',value:(r:typeof gridRows[number])=>r.status}];
const gridKey=(r:typeof gridRows[number])=>r.id;
const largeRows=Array.from({length:10000},(_,i)=>({id:'v'+String(i).padStart(5,'0'),name:'Synthetic '+i,amount:i,status:i%2?'open':'closed'}));
const remoteTransport:GridTransport<typeof gridRows[number]>={read:async request=>{const filtered=gridRows.filter(r=>!request.query.filters?.length||r.name.toLowerCase().includes(String((request.query.filters[0] as {value:string}).value).toLowerCase()));const offset=request.cursor==='next'?2:0;return {rows:filtered.slice(offset,offset+2).map(r=>({id:r.id,version:'v1',data:r})),nextCursor:filtered.length>offset+2?'next':undefined,revision:'synthetic',total:filtered.length}},bulk:async request=>request.items.map(i=>({id:i.id,status:i.id==='r2'?'conflict':'applied'}))};
export function Fixture({product,theme}:{product:Product;theme:Theme}){
  const [open,setOpen]=React.useState(false),[value,setValue]=React.useState(''),[page,setPage]=React.useState(1),[checked,setChecked]=React.useState(false);
  React.useEffect(()=>{document.documentElement.dataset.hydrated='yes'},[]);
  return <TakteraProvider product={product} theme={theme}><main style={{padding:24}}>
    <h1>React QA</h1><Field label="Имя" value={value} onChange={e=>setValue(e.target.value)} hint="Тестовое поле"/>
    <p data-testid="value">{value}</p><Field label="Ошибка" error="Введите значение"/>
    <Select label="Услуга" options={[{label:'A',value:'a'},{label:'B',value:'b'}]}/>
    <Checkbox label="Согласие" checked={checked} onChange={e=>setChecked(e.target.checked)}/><Switch label="Напоминание" defaultChecked/>
    <Button disabled>Недоступно</Button><Button loading>Загрузка</Button>
    <Tabs items={[{id:'a',label:'Обзор',panel:<p>Панель A</p>},{id:'b',label:'Настройки',panel:<p>Панель B</p>}]}/>
    <DataTable columns={[{key:'name',label:'Имя записи',sortable:true}]} rows={rows} rowKey={r=>r.id}/>
    <Pagination page={page} pageCount={3} onPageChange={setPage}/>
    <Button onClick={()=>setOpen(true)}>Открыть диалог</Button><Dialog open={open} title="Новая запись" onClose={()=>setOpen(false)} onConfirm={()=>setOpen(false)}><p>Тестовый диалог</p></Dialog>
    <Status tone="success">Готово</Status><AdvancedDataGrid rows={gridRows} columns={gridColumns} rowKey={gridKey} label="Реестр BR5" searchColumn="name" groupBy="status" pageSize={2}/><AdvancedDataGrid rows={gridRows} columns={gridColumns} rowKey={gridKey} label="Групповой реестр BR5" searchColumn="name" groupBy="status" groupedRows pageSize={5}/><RemoteDataGrid transport={remoteTransport} columns={gridColumns} label="Серверный реестр BR5" searchColumn="name" pageSize={2} bulkAction={{id:"archive",label:"Архивировать выбранные"}}/><AdvancedDataGrid rows={largeRows} columns={gridColumns} rowKey={gridKey} label="Виртуальный реестр BR5" searchColumn="name" pageSize={25} virtualization/>
  </main></TakteraProvider>;
}
