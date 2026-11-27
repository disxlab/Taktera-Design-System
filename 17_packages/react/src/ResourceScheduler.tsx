import * as React from 'react';
import {addCivilDays,calendarDays,bookingsForDay,localMinute,localCandidates,resolveLocal,instant,validateDraft} from './resource-scheduler.js';
import type {SchedulerResource,SchedulerBooking,SchedulerDraft,SchedulerMutation,SchedulerTransport} from './resource-scheduler.js';
type Fold='earlier'|'later'|'reject';
type Editor={id?:string;version?:string;resourceId:string;title:string;start:string;end:string;startFold:Fold;endFold:Fold};
export type ResourceSchedulerProps={label:string;resources:readonly SchedulerResource[];bookings:readonly SchedulerBooking[];initialDate:string;initialZone:string;zones:readonly string[];locale?:'ru-RU'|'en-US';mutate?:SchedulerTransport};
export function ResourceScheduler({label,resources,bookings,initialDate,initialZone,zones,locale='ru-RU',mutate}:ResourceSchedulerProps){
 const ru=locale==='ru-RU',t=(r:string,e:string)=>ru?r:e,id=React.useId();
 const [date,setDate]=React.useState(initialDate),[mode,setMode]=React.useState<'day'|'week'>('day'),[zone,setZone]=React.useState(initialZone),[resource,setResource]=React.useState('');
 const [editor,setEditor]=React.useState<Editor|null>(null),[cancelConfirm,setCancelConfirm]=React.useState(false),[busy,setBusy]=React.useState(false),[uncertain,setUncertain]=React.useState(false),[message,setMessage]=React.useState(''),[error,setError]=React.useState('');
 const active=React.useRef<AbortController|undefined>(undefined),opener=React.useRef<HTMLElement|null>(null),editorTitle=React.useRef<HTMLInputElement>(null),heading=React.useRef<HTMLHeadingElement>(null),table=React.useRef<HTMLTableElement>(null);
 const days=React.useMemo(()=>calendarDays(date,mode,zone),[date,mode,zone]);
 const visible=resources.filter(r=>!resource||r.id===resource);
 const editing=!!editor;
 React.useEffect(()=>()=>active.current?.abort(),[]);
 React.useEffect(()=>{if(editing)editorTitle.current?.focus()},[editing]);
 function closeEditor(){setEditor(null);setCancelConfirm(false);setError('');requestAnimationFrame(()=>{if(opener.current?.isConnected)opener.current.focus();else heading.current?.focus()})}
 function openNew(resourceId:string,day:string){opener.current=document.activeElement as HTMLElement;setMessage('');setError('');setCancelConfirm(false);setEditor({resourceId,title:'',start:day+'T09:00',end:day+'T10:00',startFold:'reject',endFold:'reject'})}
 function openEdit(b:SchedulerBooking){opener.current=document.activeElement as HTMLElement;setMessage('');setError('');setCancelConfirm(false);const start=localMinute(instant(b.start),zone),end=localMinute(instant(b.end),zone);const fold=(v:string,original:string):Fold=>{const candidates=localCandidates(v,zone);return candidates.length>1&&candidates.at(-1)===instant(original)?'later':candidates.length>1?'earlier':'reject'};setEditor({id:b.id,version:b.version,resourceId:b.resourceId,title:b.title,start,end,startFold:fold(start,b.start),endFold:fold(end,b.end)})}
 function patch(v:Partial<Editor>){setEditor(e=>e?{...e,...v}:e);setError('');setCancelConfirm(false)}
 function move(e:React.KeyboardEvent<HTMLButtonElement>,row:number,col:number){const moves:Record<string,[number,number]>={ArrowLeft:[row,col-1],ArrowRight:[row,col+1],ArrowUp:[row-1,col],ArrowDown:[row+1,col],Home:[row,0],End:[row,days.length-1]};const next=moves[e.key];if(!next)return;e.preventDefault();const [r,c]=next;table.current?.querySelector<HTMLButtonElement>('[data-cell="'+r+'-'+c+'"]')?.focus()}
 function navigate(n:number){try{const next=addCivilDays(date,n*(mode==='week'?7:1));calendarDays(next,mode,zone);setDate(next);setError('')}catch{setError(t('Дата вне диапазона календаря','Date outside calendar range'))}}
 function changeDate(value:string){try{calendarDays(value,mode,zone);setDate(value);setError('')}catch{setError(t('Некорректная дата','Invalid date'))}}
 async function submit(cancel=false){
  if(!editor||!mutate||busy||uncertain||active.current)return;
  setError('');setMessage('');
  let request:SchedulerMutation;
  try{
   const key=globalThis.crypto.randomUUID();
   if(cancel){if(!cancelConfirm||!editor.id||!editor.version)return;request={kind:'cancel',id:editor.id,version:editor.version,idempotencyKey:key}}
   else{
    if(editor.id){const original=bookings.find(b=>b.id===editor.id);if(!original||original.version!==editor.version||original.status==='cancelled'){setError(t('Запись изменилась. Откройте её заново.','Booking changed. Reopen it.'));return}}
    const draft:SchedulerDraft={resourceId:editor.resourceId,title:editor.title.trim(),start:resolveLocal(editor.start,zone,editor.startFold),end:resolveLocal(editor.end,zone,editor.endFold)};
    const conflicts=validateDraft(draft,resources,bookings,editor.id);
    if(conflicts.length){setError(t('Конфликт ресурса: ','Resource conflict: ')+conflicts.map(b=>b.title).join(', '));return}
    request=editor.id&&editor.version?{kind:'update',id:editor.id,version:editor.version,draft,idempotencyKey:key}:{kind:'create',draft,idempotencyKey:key};
   }
  }catch{setError(t('Проверьте название, ресурс, интервал и неоднозначное или отсутствующее локальное время.','Check title, resource, interval and ambiguous or nonexistent local time.'));return}
  const abort=new AbortController();active.current=abort;setBusy(true);
  try{
   const result=await mutate(request,abort.signal);if(abort.signal.aborted)return;
   if(result.status==='applied'){closeEditor();setMessage(t('Сохранено','Saved'))}
   else if(result.status==='conflict'||result.status==='forbidden'||result.status==='invalid'){setError(t('Сервер отклонил операцию: ','Server rejected operation: ')+({conflict:t('конфликт','conflict'),forbidden:t('нет доступа','forbidden'),invalid:t('ошибка данных','invalid')}[result.status]));setCancelConfirm(false)}
   else throw Error('Unknown result');
  }catch{if(!abort.signal.aborted){setUncertain(true);setError(t('Результат неизвестен. Сверьте данные с сервером и заново откройте календарь.','Outcome unknown. Reconcile with server and reopen calendar.'))}}
  finally{active.current=undefined;if(!abort.signal.aborted)setBusy(false)}
 }
 const canEdit=!!mutate&&!uncertain&&!editing&&!busy;
 const time=(b:SchedulerBooking)=>localMinute(instant(b.start),zone).replace('T',' ')+' — '+localMinute(instant(b.end),zone).replace('T',' ');
 return <section className="tku-scheduler" aria-labelledby={id}><h2 id={id} ref={heading} tabIndex={-1}>{label}</h2>
 <div className="tku-scheduler-toolbar">
 <button className="tku-button tku-button--secondary" type="button" disabled={editing||busy} onClick={()=>navigate(-1)}>{t('Назад','Previous')}</button>
 <button className="tku-button tku-button--secondary" type="button" disabled={editing||busy} onClick={()=>navigate(1)}>{t('Вперёд','Next')}</button>
 <label>{t('Дата','Date')}<input className="tku-input" type="date" min="2000-01-10" max="2099-12-20" value={date} disabled={editing||busy} onChange={e=>changeDate(e.target.value)}/></label>
 <button type="button" className="tku-button tku-button--secondary" disabled={editing||busy} aria-pressed={mode==='day'} onClick={()=>setMode('day')}>{t('День','Day')}</button>
 <button type="button" className="tku-button tku-button--secondary" disabled={editing||busy} aria-pressed={mode==='week'} onClick={()=>setMode('week')}>{t('Неделя','Week')}</button>
 <label>{t('Часовой пояс','Time zone')}<select className="tku-input" value={zone} disabled={editing||busy} onChange={e=>setZone(e.target.value)}>{[...new Set([initialZone,...zones])].map(z=><option key={z}>{z}</option>)}</select></label>
 <label>{t('Ресурс','Resource')}<select className="tku-input" value={resource} disabled={editing||busy} onChange={e=>setResource(e.target.value)}><option value="">{t('Все ресурсы','All resources')}</option>{resources.map(r=><option key={r.id} value={r.id}>{r.label}</option>)}</select></label></div>
 <p aria-live="polite">{days[0].date}{mode==='week'?' — '+days.at(-1)?.date:''} · {zone}</p>
 <p className="tku-scheduler-hint">{t('Кнопки новых записей: стрелки, Home и End для перехода по календарю; Enter для открытия.','New booking buttons: arrows, Home and End navigate; Enter opens.')}</p>
 <div className="tku-table-scroll"><table className="tku-table tku-scheduler-table" ref={table}><caption>{t('Календарь ресурсов','Resource calendar')}</caption><thead><tr><th scope="col">{t('Ресурс','Resource')}</th>{days.map(d=><th scope="col" key={d.date} data-day={d.date}>{d.date}</th>)}</tr></thead><tbody>
 {visible.map((r,ri)=><tr key={r.id}><th scope="row">{r.label}</th>{days.map((d,di)=><td key={d.date}>
 {bookingsForDay(bookings,r.id,d).map(b=><div key={b.id} className="tku-scheduler-booking"><span>{time(b)}</span><button type="button" className="tku-button tku-button--secondary" disabled={!canEdit} onClick={()=>openEdit(b)}>{b.title}</button><span>{b.status==='held'?t('Резерв','Held'):t('Подтверждено','Confirmed')}</span></div>)}
 {mutate&&<button type="button" className="tku-button tku-button--secondary" data-cell={ri+'-'+di} disabled={!canEdit||d.start===d.end} aria-label={t('Новая запись','New booking')+' '+r.label+' '+d.date} onKeyDown={e=>move(e,ri,di)} onClick={()=>openNew(r.id,d.date)}>{t('Новая запись','New booking')}</button>}
 {d.start===d.end&&<span>{t('Дата отсутствует в часовом поясе','Date does not exist in time zone')}</span>}
 </td>)}</tr>)}
 </tbody></table></div>
 {editor&&<form className="tku-scheduler-editor" aria-label={t('Редактор записи','Booking editor')} onSubmit={e=>{e.preventDefault();void submit()}}>
 <h3>{editor.id?t('Изменить запись','Edit booking'):t('Создать запись','Create booking')}</h3>
 <label>{t('Название','Title')}<input ref={editorTitle} className="tku-input" value={editor.title} disabled={busy} required onChange={e=>patch({title:e.target.value})}/></label>
 <label>{t('Ресурс записи','Booking resource')}<select className="tku-input" value={editor.resourceId} disabled={busy} onChange={e=>patch({resourceId:e.target.value})}>{resources.map(r=><option key={r.id} value={r.id}>{r.label}</option>)}</select></label>
 <label>{t('Начало','Start')}<input className="tku-input" type="datetime-local" value={editor.start} disabled={busy} required onChange={e=>patch({start:e.target.value,startFold:'reject'})}/></label>
 <label>{t('Неоднозначное начало','Ambiguous start')}<select className="tku-input" value={editor.startFold} disabled={busy} onChange={e=>patch({startFold:e.target.value as Fold})}><option value="reject">{t('Требовать однозначность','Require unambiguous')}</option><option value="earlier">{t('Первый момент','Earlier instant')}</option><option value="later">{t('Второй момент','Later instant')}</option></select></label>
 <label>{t('Окончание','End')}<input className="tku-input" type="datetime-local" value={editor.end} disabled={busy} required onChange={e=>patch({end:e.target.value,endFold:'reject'})}/></label>
 <label>{t('Неоднозначное окончание','Ambiguous end')}<select className="tku-input" value={editor.endFold} disabled={busy} onChange={e=>patch({endFold:e.target.value as Fold})}><option value="reject">{t('Требовать однозначность','Require unambiguous')}</option><option value="earlier">{t('Первый момент','Earlier instant')}</option><option value="later">{t('Второй момент','Later instant')}</option></select></label>
 <div className="tku-scheduler-toolbar"><button type="submit" className="tku-button tku-button--primary" disabled={busy||uncertain}>{t('Сохранить запись','Save booking')}</button><button type="button" className="tku-button tku-button--secondary" disabled={busy} onClick={closeEditor}>{t('Закрыть редактор','Close editor')}</button>{editor.id&&<button type="button" className="tku-button tku-button--secondary" disabled={busy||uncertain} onClick={()=>setCancelConfirm(true)}>{t('Отменить запись','Cancel booking')}</button>}{cancelConfirm&&<button type="button" className="tku-button tku-button--danger" disabled={busy||uncertain} onClick={()=>void submit(true)}>{t('Подтвердить отмену','Confirm cancellation')}</button>}</div></form>}
 {message&&<p role="status">{message}</p>}{error&&<p role="alert" className="tku-scheduler-error">{error}</p>}
 </section>
}
