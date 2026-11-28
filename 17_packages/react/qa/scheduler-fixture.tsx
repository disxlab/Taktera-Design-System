import * as React from 'react';
import {TakteraProvider,ResourceScheduler,validateDraft,validateSeries} from '../src/index.js';
import type {Product,Theme,SchedulerBooking,SchedulerTransport} from '../src/index.js';
const weekdays=Object.fromEntries([1,2,3,4,5].map(d=>[d,[{start:'08:00',end:'12:00'},{start:'13:00',end:'18:00'}]]));
const resources=[{id:'r1',label:'Room 1',schedule:{timeZone:'Europe/Amsterdam',weekly:weekdays}},{id:'r2',label:'Room 2',schedule:{timeZone:'Europe/Amsterdam',weekly:weekdays}}];
const initial:SchedulerBooking[]=[{id:'a',version:'v1',title:'Existing A',resourceId:'r1',start:'2026-12-01T08:00:00Z',end:'2026-12-01T09:00:00Z',status:'confirmed'},{id:'b',version:'v1',title:'Existing B',resourceId:'r2',start:'2026-12-01T08:00:00Z',end:'2026-12-01T09:00:00Z',status:'held'}];
export function SchedulerFixture({product,theme,locale='ru-RU'}:{product:Product;theme:Theme;locale?:'ru-RU'|'en-US'}){
 const [rows,setRows]=React.useState(initial),[calls,setCalls]=React.useState(0);
 const current=React.useRef(rows);current.current=rows;
 const mutate:SchedulerTransport=async request=>{
  setCalls(n=>n+1);const old=current.current;
  if(request.kind==='cancel'){const match=old.find(b=>b.id===request.id);if(!match||match.version!==request.version)return {status:'conflict'};setRows(old.map(b=>b.id===request.id?{...b,status:'cancelled',version:'v2'}:b));return {status:'applied'}}
  if(request.kind==='create-series'){try{validateSeries(request.occurrences,resources,old)}catch{return {status:'conflict'}};setRows([...old,...request.occurrences.map((d,i):SchedulerBooking=>({...d,id:request.idempotencyKey+'-'+i,seriesId:request.idempotencyKey,version:'v1',status:'confirmed'}))]);return {status:'applied'}}
  if(request.draft.title==='Server conflict')return {status:'conflict'};
  if(request.draft.title==='Unknown outcome')throw Error('Synthetic transport failure');
  if(validateDraft(request.draft,resources,old,request.kind==='update'?request.id:undefined).length)return {status:'conflict'};
  if(request.kind==='update'){const match=old.find(b=>b.id===request.id);if(!match||match.version!==request.version)return {status:'conflict'};setRows(old.map(b=>b.id===request.id?{...b,...request.draft,version:'v2'}:b))}
  else setRows([...old,{...request.draft,id:'new-'+request.idempotencyKey,version:'v1',status:'confirmed'}]);
  return {status:'applied'};
 };
 React.useEffect(()=>{document.documentElement.dataset.hydrated='yes'},[]);
 return <TakteraProvider product={product} theme={theme}><main style={{padding:24}}><h1>Scheduler QA</h1><p data-testid="calls">{calls}</p><ResourceScheduler label="Scheduler BR5" resources={resources} bookings={rows} initialDate="2026-12-01" initialZone="Europe/Amsterdam" zones={['UTC','Asia/Kathmandu']} locale={locale} mutate={mutate} advanced/></main></TakteraProvider>
}
