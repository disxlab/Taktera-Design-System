import * as React from 'react';
import { TakteraProvider, Button, Field, Select, Checkbox, Switch, Tabs, DataTable, Dialog, Pagination, Status } from '../src/index';
import type { Product, Theme } from '../src/index';
const rows=[{id:'a',name:'10'},{id:'b',name:'2'},{id:'c',name:'<img src=x onerror=alert(1)>'}];
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
    <Status tone="success">Готово</Status>
  </main></TakteraProvider>;
}
