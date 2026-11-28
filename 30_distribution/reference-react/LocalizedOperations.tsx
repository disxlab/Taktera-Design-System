import * as React from 'react';
import {ResourceScheduler,AdvancedAnalyticsDashboard,Select,validateDraft} from '@taktera/ui-react';
import type {SchedulerBooking,SchedulerResource,SchedulerTransport} from '@taktera/ui-react';
const labels={
 en:{scheduler:'Localized schedule',analytics:'Localized analytics',room:'Synthetic room',visit:'Synthetic appointment',reject:'Synthetic conflict'},
 ru:{scheduler:'Локализованное расписание',analytics:'Локализованная аналитика',room:'Тестовый кабинет',visit:'Тестовая запись',reject:'Тестовый конфликт'}
} as const;
type Language=keyof typeof labels;
const metrics=[{date:'2026-12-01',revenueMinor:12000,visits:4,completed:3,capacity:8,used:4},{date:'2026-12-02',revenueMinor:18000,visits:6,completed:5,capacity:8,used:5}];
export function LocalizedOperations(){
 const [language,setLanguage]=React.useState<Language>('en');
 return <div><Select label="Operations language / Язык операций" value={language} options={[{value:'en',label:'English'},{value:'ru',label:'Русский'}]} onChange={e=>setLanguage(e.target.value==='ru'?'ru':'en')}/><Operations key={language} language={language}/></div>;
}
function Operations({language}:{language:Language}){
 const l=labels[language],locale=language==='ru'?'ru-RU':'en-US';
 const resources:SchedulerResource[]=[{id:'room',label:l.room}];
 const [rows,setRows]=React.useState<SchedulerBooking[]>(()=>[{id:'b1',version:'v1',resourceId:'room',title:l.visit,start:'2026-12-01T09:00:00Z',end:'2026-12-01T10:00:00Z',status:'confirmed'}]);
 const current=React.useRef(rows),[calls,setCalls]=React.useState(0);
 const mutate:SchedulerTransport=async(request,signal)=>{
  if(signal.aborted)return {status:'conflict'};
  setCalls(n=>n+1);
  // This isolated fixture supports single-record updates only; no network or persistent writes.
  if(request.kind!=='update')return {status:'invalid'};
  const old=current.current, match=old.find(b=>b.id===request.id);
  if(!match||match.version!==request.version||request.draft.title===l.reject)return {status:'conflict'};
  if(validateDraft(request.draft,resources,old,request.id).length)return {status:'conflict'};
  const next=old.map(b=>b.id===request.id?{...b,...request.draft,version:'v'+(Number(b.version.slice(1))+1)}:b);
  current.current=next;setRows(next);return {status:'applied'};
 };
 return <section aria-label={language==='ru'?'Тестовые операции':'Synthetic operations'} lang={language}>
  <p data-testid="schedule-calls">{calls}</p><p data-testid="schedule-version">{rows[0].version}</p>
  <ResourceScheduler label={l.scheduler} resources={resources} bookings={rows} initialDate="2026-12-01" initialZone="UTC" zones={['Europe/Amsterdam']} locale={locale} mutate={mutate} advanced/>
  <AdvancedAnalyticsDashboard label={l.analytics} rows={metrics} initialPeriod={{start:'2026-12-01',end:'2026-12-02'}} locale={locale} allowExport/>
 </section>;
}
