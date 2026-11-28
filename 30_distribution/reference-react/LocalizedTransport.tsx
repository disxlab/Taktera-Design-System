import * as React from 'react';
import {Button,Field,Select,Alert} from '@taktera/ui-react';
import {createSyntheticTransport} from './synthetic-transport.mjs';
import type {SyntheticRequest,SyntheticRecord,SyntheticResult} from './synthetic-transport.mjs';

const labels={
 en:{region:'Synthetic transport',name:'Customer name',save:'Save record',fail:'Fail next request',retry:'Retry same request',replay:'Replay last request',compete:'Simulate competing write',reload:'Reload record',external:'Synthetic competing name',validation:'Invalid customer name',unavailable:'Temporarily unavailable',applied:'Saved',conflict:'Version conflict',idle:'Ready',unexpected:'Unexpected synthetic result'},
 ru:{region:'Синтетический транспорт',name:'Имя клиента',save:'Сохранить запись',fail:'Ошибка следующего запроса',retry:'Повторить тот же запрос',replay:'Повторить сохранённый запрос',compete:'Имитировать параллельную запись',reload:'Загрузить запись',external:'Синтетическое конкурентное имя',validation:'Недопустимое имя клиента',unavailable:'Временно недоступно',applied:'Сохранено',conflict:'Конфликт версий',idle:'Готово',unexpected:'Неожиданный результат'}
} as const;
type Locale=keyof typeof labels;

export function LocalizedTransport(){
 const [locale,setLocale]=React.useState<Locale>('en');
 return <div><Select label="Language / Язык" value={locale} options={[{value:'en',label:'English'},{value:'ru',label:'Русский'}]} onChange={e=>setLocale(e.target.value==='ru'?'ru':'en')}/><Editor key={locale} locale={locale}/></div>;
}
function Editor({locale}:{locale:Locale}){
 const l=labels[locale], [transport]=React.useState(createSyntheticTransport);
 const [record,setRecord]=React.useState<SyntheticRecord>(()=>transport.read('p1')!);
 const [version,setVersion]=React.useState(record.version),[draft,setDraft]=React.useState(record.name);
 const [result,setResult]=React.useState<SyntheticResult|null>(null),[busy,setBusy]=React.useState(false);
 const serial=React.useRef(0),last=React.useRef<SyntheticRequest|null>(null);
 const status=result?.status??'idle';
 const message=status==='idle'?l.idle:status==='validation'?l.validation:status==='unavailable'?l.unavailable:status==='applied'?l.applied:status==='conflict'?l.conflict:l.unexpected;
 const refresh=()=>{const actual=transport.read('p1');if(!actual)throw Error('Missing synthetic record');setRecord(actual);return actual;};
 async function execute(request:SyntheticRequest){
  setBusy(true);
  try{const response=await transport.save(request);last.current=request;setResult(response);const actual=refresh();if(response.status==='applied'){setVersion(actual.version);setDraft(actual.name);}}
  finally{setBusy(false);}
 }
 async function compete(){
  setBusy(true);
  try{const current=transport.read('p1')!;const response=await transport.save({id:'p1',name:l.external,version:current.version,requestId:'competitor-'+(++serial.current)});if(response.status!=='applied')throw Error('Synthetic competing write failed');refresh();setResult(null);}
  finally{setBusy(false);}
 }
 return <section aria-label={l.region} lang={locale}>
  <p data-testid="transport-record">{record.name}</p><p data-testid="transport-version">{record.version}</p>
  <form onSubmit={e=>{e.preventDefault();void execute({id:'p1',name:draft,version,requestId:'editor-'+(++serial.current)});}}>
   <Field label={l.name} value={draft} disabled={busy} error={status==='validation'?l.validation:undefined} onChange={e=>setDraft(e.target.value)}/>
   <Button type="submit" disabled={busy}>{l.save}</Button>
  </form>
  <Button type="button" variant="secondary" disabled={busy} onClick={()=>transport.failNext()}>{l.fail}</Button>
  <Button type="button" variant="secondary" disabled={busy||status!=='unavailable'} onClick={()=>{if(last.current)void execute(last.current);}}>{l.retry}</Button>
  <Button type="button" variant="secondary" disabled={busy||status!=='applied'} onClick={()=>{if(last.current)void execute(last.current);}}>{l.replay}</Button>
  <Button type="button" variant="secondary" disabled={busy} onClick={()=>void compete()}>{l.compete}</Button>
  <Button type="button" variant="secondary" disabled={busy} onClick={()=>{const actual=refresh();setVersion(actual.version);setDraft(actual.name);setResult(null);last.current=null;}}>{l.reload}</Button>
  <div data-testid="transport-status" data-status={status}><Alert tone={status==='validation'||status==='conflict'||status==='unavailable'?'error':status==='applied'?'success':'info'}>{message}</Alert></div>
 </section>;
}
