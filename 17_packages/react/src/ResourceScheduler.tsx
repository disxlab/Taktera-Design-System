import * as React from 'react';
import {addCivilDays,calendarDays,bookingsForDay,localMinute,localCandidates,resolveEditedLocal,zonedMinuteLabel,instant,validateDraft,resourceIds,expandRecurrence,validateSeries,moveBooking,dropInstant,workingIntervals,timelinePosition} from './resource-scheduler.js';
import type {SchedulerResource,SchedulerBooking,SchedulerDraft,SchedulerMutation,SchedulerTransport,CalendarDay,RecurrenceRule} from './resource-scheduler.js';
type Fold='earlier'|'later'|'reject';
type Editor={additionalResourceIds?:string[];frequency?:'none'|'daily'|'weekly';count?:number;exclusions?:string;id?:string;version?:string;resourceId:string;title:string;start:string;end:string;startFold:Fold;endFold:Fold};
export type ResourceSchedulerProps={label:string;resources:readonly SchedulerResource[];bookings:readonly SchedulerBooking[];initialDate:string;initialZone:string;zones:readonly string[];locale?:'ru-RU'|'en-US';mutate?:SchedulerTransport;advanced?:boolean};
export function ResourceScheduler({label,resources,bookings,initialDate,initialZone,zones,locale='ru-RU',mutate,advanced=false}:ResourceSchedulerProps){
 const ru=locale==='ru-RU',t=(r:string,e:string)=>ru?r:e,id=React.useId();
 const [date,setDate]=React.useState(initialDate),[mode,setMode]=React.useState<'day'|'week'>('day'),[zone,setZone]=React.useState(initialZone),[resource,setResource]=React.useState('');
 const [view,setView]=React.useState<'agenda'|'timeline'>('agenda');
 const dragged=React.useRef<{id:string;from:string}|null>(null);
 const [editor,setEditor]=React.useState<Editor|null>(null),[cancelConfirm,setCancelConfirm]=React.useState(false),[busy,setBusy]=React.useState(false),[uncertain,setUncertain]=React.useState(false),[message,setMessage]=React.useState(''),[error,setError]=React.useState('');
 const active=React.useRef<AbortController|undefined>(undefined),opener=React.useRef<HTMLElement|null>(null),editorTitle=React.useRef<HTMLInputElement>(null),heading=React.useRef<HTMLHeadingElement>(null),table=React.useRef<HTMLTableElement>(null);
 const days=React.useMemo(()=>calendarDays(date,mode,zone),[date,mode,zone]);
 const visible=resources.filter(r=>!resource||r.id===resource);
 const editing=!!editor;
 React.useEffect(()=>()=>active.current?.abort(),[]);
 React.useEffect(()=>{if(editing)editorTitle.current?.focus()},[editing]);
 function closeEditor(){setEditor(null);setCancelConfirm(false);setError('');requestAnimationFrame(()=>{if(opener.current?.isConnected)opener.current.focus();else heading.current?.focus()})}
 function openNew(resourceId:string,day:string){opener.current=document.activeElement as HTMLElement;setMessage('');setError('');setCancelConfirm(false);setEditor({resourceId,additionalResourceIds:[],frequency:'none',count:2,exclusions:'',title:'',start:day+'T09:00',end:day+'T10:00',startFold:'reject',endFold:'reject'})}
 function openEdit(b:SchedulerBooking,proposal?:SchedulerDraft){opener.current=document.activeElement as HTMLElement;setMessage('');setError('');setCancelConfirm(false);const draft=proposal??b;const start=localMinute(instant(draft.start),zone),end=localMinute(instant(draft.end),zone);const fold=(v:string,original:string):Fold=>{const candidates=localCandidates(v,zone);return candidates.length>1&&Math.floor(candidates.at(-1)!/60000)===Math.floor(instant(original)/60000)?'later':candidates.length>1?'earlier':'reject'};setEditor({id:b.id,version:b.version,resourceId:draft.resourceId,additionalResourceIds:[...(draft.additionalResourceIds??[])],title:draft.title,start,end,startFold:fold(start,draft.start),endFold:fold(end,draft.end)})}
 function patch(v:Partial<Editor>){setEditor(e=>e?{...e,...v}:e);setError('');setCancelConfirm(false)}
 function move(e:React.KeyboardEvent<HTMLButtonElement>,row:number,col:number){const moves:Record<string,[number,number]>={ArrowLeft:[row,col-1],ArrowRight:[row,col+1],ArrowUp:[row-1,col],ArrowDown:[row+1,col],Home:[row,0],End:[row,days.length-1]};const next=moves[e.key];if(!next)return;e.preventDefault();const [r,c]=next;table.current?.querySelector<HTMLButtonElement>('[data-cell="'+r+'-'+c+'"]')?.focus()}
 function navigate(n:number){try{const next=addCivilDays(date,n*(mode==='week'?7:1));if(next<'2000-01-10'||next>'2099-12-20')throw Error('Range');calendarDays(next,mode,zone);setDate(next);setError('')}catch{setError(t('Дата вне диапазона календаря','Date outside calendar range'))}}
 function changeDate(value:string){try{if(value<'2000-01-10'||value>'2099-12-20')throw Error('Range');calendarDays(value,mode,zone);setDate(value);setError('')}catch{setError(t('Некорректная дата','Invalid date'))}}
 async function submit(cancel=false){
  if(!editor||!mutate||busy||uncertain||active.current)return;
  setError('');setMessage('');
  let request:SchedulerMutation;
  try{
   const key=globalThis.crypto.randomUUID();
   const original=editor.id?bookings.find(b=>b.id===editor.id):undefined;
   if(editor.id&&(!original||original.version!==editor.version||original.status==='cancelled')){setError(t('Запись изменилась. Откройте её заново.','Booking changed. Reopen it.'));return}
   if(cancel){if(!cancelConfirm||!editor.id||!editor.version)return;request={kind:'cancel',id:editor.id,version:editor.version,idempotencyKey:key}}
   else{
    const draft:SchedulerDraft={resourceId:editor.resourceId,additionalResourceIds:editor.additionalResourceIds??[],title:editor.title.trim(),start:resolveEditedLocal(editor.start,zone,editor.startFold,original?.start),end:resolveEditedLocal(editor.end,zone,editor.endFold,original?.end)};
    const conflicts=validateDraft(draft,resources,bookings,editor.id);
    if(conflicts.length){setError(t('Конфликт ресурса: ','Resource conflict: ')+conflicts.map(b=>b.title).join(', '));return}
    if(!editor.id&&editor.frequency&&editor.frequency!=='none'){
     const rule:RecurrenceRule={frequency:editor.frequency,count:editor.count??2,timeZone:zone,excludeDates:(editor.exclusions??'').split(',').map(x=>x.trim()).filter(Boolean),startFold:editor.startFold,endFold:editor.endFold};
     const occurrences=expandRecurrence(draft,rule);validateSeries(occurrences,resources,bookings);request={kind:'create-series',draft,rule,occurrences,idempotencyKey:key};
    }else request=editor.id&&editor.version?{kind:'update',id:editor.id,version:editor.version,draft,idempotencyKey:key}:{kind:'create',draft,idempotencyKey:key};
   }
  }catch{setError(t('Проверьте название, ресурсы, рабочие часы, серию, интервал и локальное время.','Check title, resources, working hours, series, interval and local time.'));return}
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
 function proposeMove(b:SchedulerBooking,from:string,to:string,start:number){if(!canEdit)return;try{openEdit(b,moveBooking(b,from,to,start));setMessage(t('Проверьте перенос и сохраните запись','Review move and save booking'))}catch{setError(t('Перенос недоступен; используйте редактор','Move unavailable; use editor'))}}
 function onDrop(e:React.DragEvent<HTMLDivElement>,r:SchedulerResource,d:CalendarDay){e.preventDefault();const payload=dragged.current;dragged.current=null;if(!payload||!canEdit)return;const b=bookings.find(x=>x.id===payload.id&&x.status!=='cancelled');if(!b)return;const rect=e.currentTarget.getBoundingClientRect();try{proposeMove(b,payload.from,r.id,dropInstant(d,(e.clientX-rect.left)/rect.width))}catch{setError(t('Некорректный перенос','Invalid move'))}}
 function work(r:SchedulerResource,d:CalendarDay){try{return workingIntervals(r,d)}catch{return []}}
 function timelineTicks(d:CalendarDay){return Array.from({length:Math.ceil((d.end-d.start)/3600000)},(_,i)=>d.start+i*3600000)}
 const time=(b:SchedulerBooking)=>zonedMinuteLabel(instant(b.start),zone)+' — '+zonedMinuteLabel(instant(b.end),zone);
 return <section className="tku-scheduler" aria-labelledby={id}><h2 id={id} ref={heading} tabIndex={-1}>{label}</h2>
 <div className="tku-scheduler-toolbar">
 <button className="tku-button tku-button--secondary" type="button" disabled={editing||busy} onClick={()=>navigate(-1)}>{t('Назад','Previous')}</button>
 <button className="tku-button tku-button--secondary" type="button" disabled={editing||busy} onClick={()=>navigate(1)}>{t('Вперёд','Next')}</button>
 <label>{t('Дата','Date')}<input className="tku-input" type="date" min="2000-01-10" max="2099-12-20" value={date} disabled={editing||busy} onChange={e=>changeDate(e.target.value)}/></label>
 <button type="button" className="tku-button tku-button--secondary" disabled={editing||busy} aria-pressed={mode==='day'} onClick={()=>setMode('day')}>{t('День','Day')}</button>
 <button type="button" className="tku-button tku-button--secondary" disabled={editing||busy} aria-pressed={mode==='week'} onClick={()=>setMode('week')}>{t('Неделя','Week')}</button>
 {advanced&&<><button type="button" className="tku-button tku-button--secondary" disabled={editing||busy} aria-pressed={view==='agenda'} onClick={()=>setView('agenda')}>{t('Список','Agenda')}</button><button type="button" className="tku-button tku-button--secondary" disabled={editing||busy} aria-pressed={view==='timeline'} onClick={()=>setView('timeline')}>{t('Шкала времени','Timeline')}</button></>}
 <label>{t('Часовой пояс','Time zone')}<select className="tku-input" aria-label={t('Часовой пояс','Time zone')} value={zone} disabled={editing||busy} onChange={e=>setZone(e.target.value)}>{[...new Set([initialZone,...zones])].map(z=><option key={z}>{z}</option>)}</select></label>
 <label>{t('Ресурс','Resource')}<select className="tku-input" aria-label={t('Ресурс','Resource')} value={resource} disabled={editing||busy} onChange={e=>setResource(e.target.value)}><option value="">{t('Все ресурсы','All resources')}</option>{resources.map(r=><option key={r.id} value={r.id}>{r.label}</option>)}</select></label></div>
 <p aria-live="polite">{days[0].date}{mode==='week'?' — '+days.at(-1)?.date:''} · {zone}</p>
 <p className="tku-scheduler-hint">{t('Кнопки новых записей: стрелки, Home и End для перехода по календарю; Enter для открытия.','New booking buttons: arrows, Home and End navigate; Enter opens.')}</p>
 {view==='agenda'?<div className="tku-table-scroll"><table className="tku-table tku-scheduler-table" ref={table}><caption>{t('Календарь ресурсов','Resource calendar')}</caption><thead><tr><th scope="col">{t('Ресурс','Resource')}</th>{days.map(d=><th scope="col" key={d.date} data-day={d.date}>{d.date}</th>)}</tr></thead><tbody>
 {visible.map((r,ri)=><tr key={r.id}><th scope="row">{r.label}</th>{days.map((d,di)=><td key={d.date}>
 {bookingsForDay(bookings,r.id,d).map(b=><div key={b.id} className="tku-scheduler-booking"><span>{time(b)}</span><button type="button" className="tku-button tku-button--secondary" disabled={!canEdit} onClick={()=>openEdit(b)}>{b.title}</button><span>{b.status==='held'?t('Резерв','Held'):t('Подтверждено','Confirmed')}</span></div>)}
 {mutate&&<button type="button" className="tku-button tku-button--secondary" data-cell={ri+'-'+di} disabled={!canEdit||d.start===d.end} aria-label={t('Новая запись','New booking')+' '+r.label+' '+d.date} onKeyDown={e=>move(e,ri,di)} onClick={()=>openNew(r.id,d.date)}>{t('Новая запись','New booking')}</button>}
 {d.start===d.end&&<span>{t('Дата отсутствует в часовом поясе','Date does not exist in time zone')}</span>}
 </td>)}</tr>)}
 </tbody></table></div>:<div className="tku-timeline">
 <p>{t('Перетащите запись на ресурс и время или нажмите её и измените поля. Alt + стрелки влево/вправо: перенос на 15 минут с подтверждением.','Drag a booking to a resource/time or open its editor. Alt + Left/Right: propose a 15-minute move.')}</p>
 {days.map(d=><section key={d.date} aria-label={d.date}><h3>{d.date}</h3>{visible.map(r=><section key={r.id} aria-label={r.label+' '+d.date}><h4>{r.label}</h4>
 <div className="tku-timeline-axis" aria-hidden="true">{timelineTicks(d).filter((_,i)=>i%4===0).map(ms=><span key={ms} style={{left:100*(ms-d.start)/(d.end-d.start)+'%'}}>{zonedMinuteLabel(ms,zone).slice(11,16)}</span>)}</div>
 <div className="tku-timeline-track" data-track={r.id+'-'+d.date} onDragOver={e=>{if(canEdit&&dragged.current)e.preventDefault()}} onDrop={e=>onDrop(e,r,d)}>
 {work(r,d).map((w,i)=>{const pos=timelinePosition(w,d);return pos&&<span key={i} aria-hidden="true" className="tku-timeline-work" style={{left:pos.left+'%',width:pos.width+'%'}}/>})}
 {bookingsForDay(bookings,r.id,d).map((b,i)=>{const pos=timelinePosition({start:instant(b.start),end:instant(b.end)},d)!;return <button key={b.id} type="button" className="tku-timeline-event" data-event={b.id} draggable={canEdit} disabled={!canEdit} style={{left:pos.left+'%',width:pos.width+'%',top:8+i*38}} title={b.title+' · '+time(b)} aria-label={b.title+' · '+r.label+' · '+time(b)} onDragStart={e=>{if(!canEdit){e.preventDefault();return}dragged.current={id:b.id,from:r.id};e.dataTransfer.setData('text/plain',b.id);e.dataTransfer.effectAllowed='move'}} onDragEnd={()=>{dragged.current=null}} onClick={()=>openEdit(b)} onKeyDown={e=>{if(e.altKey&&(e.key==='ArrowLeft'||e.key==='ArrowRight')){e.preventDefault();proposeMove(b,r.id,r.id,instant(b.start)+(e.key==='ArrowRight'?1:-1)*900000)}}}>{b.title}</button>})}
 <span aria-hidden="true" style={{display:'block',height:Math.max(54,bookingsForDay(bookings,r.id,d).length*38+16)}}/>
 </div><p className="tku-scheduler-hint">{r.schedule?t('Рабочие интервалы: ','Working intervals: ')+work(r,d).map(w=>zonedMinuteLabel(w.start,zone)+' – '+zonedMinuteLabel(w.end,zone)).join('; '):t('Без ограничений рабочего графика','No working-hours restriction')}</p>
 {mutate&&<button type="button" className="tku-button tku-button--secondary" disabled={!canEdit||d.start===d.end} aria-label={t('Новая запись','New booking')+' '+r.label+' '+d.date} onClick={()=>openNew(r.id,d.date)}>{t('Новая запись','New booking')}</button>}</section>)}</section>)}</div>}
 {editor&&<form className="tku-scheduler-editor" aria-label={t('Редактор записи','Booking editor')} onSubmit={e=>{e.preventDefault();void submit()}}>
 <h3>{editor.id?t('Изменить запись','Edit booking'):t('Создать запись','Create booking')}</h3>
 <label>{t('Название','Title')}<input ref={editorTitle} className="tku-input" value={editor.title} disabled={busy} required onChange={e=>patch({title:e.target.value})}/></label>
 <label>{t('Ресурс записи','Booking resource')}<select className="tku-input" aria-label={t('Ресурс записи','Booking resource')} value={editor.resourceId} disabled={busy} onChange={e=>patch({resourceId:e.target.value,additionalResourceIds:(editor.additionalResourceIds??[]).filter(id=>id!==e.target.value)})}>{resources.map(r=><option key={r.id} value={r.id}>{r.label}</option>)}</select></label>
 {advanced&&<fieldset><legend>{t('Дополнительные ресурсы','Additional resources')}</legend>{resources.filter(r=>r.id!==editor.resourceId).map(r=><label key={r.id} className="tku-scheduler-resource-choice"><input type="checkbox" checked={editor.additionalResourceIds?.includes(r.id)??false} disabled={busy} onChange={e=>patch({additionalResourceIds:e.target.checked?[...(editor.additionalResourceIds??[]),r.id]:(editor.additionalResourceIds??[]).filter(id=>id!==r.id)})}/>{r.label}</label>)}</fieldset>}
 {advanced&&!editor.id&&<fieldset><legend>{t('Повторение','Recurrence')}</legend><label>{t('Частота','Frequency')}<select className="tku-input" aria-label={t('Частота','Frequency')} value={editor.frequency??'none'} disabled={busy} onChange={e=>patch({frequency:e.target.value as Editor['frequency']})}><option value="none">{t('Без повторения','None')}</option><option value="daily">{t('Ежедневно','Daily')}</option><option value="weekly">{t('Еженедельно','Weekly')}</option></select></label>{editor.frequency&&editor.frequency!=='none'&&<><label>{t('Количество повторений','Occurrence count')}<input className="tku-input" type="number" min={2} max={52} value={editor.count??2} disabled={busy} onChange={e=>patch({count:Number(e.target.value)})}/></label><label>{t('Исключения (ГГГГ-ММ-ДД через запятую)','Excluded dates (YYYY-MM-DD, comma separated)')}<input className="tku-input" value={editor.exclusions??''} disabled={busy} onChange={e=>patch({exclusions:e.target.value})}/></label></>}</fieldset>}
 {editor.id&&bookings.find(b=>b.id===editor.id)?.seriesId&&<p>{t('Изменяется только эта запись серии','Only this occurrence is edited')}</p>}
 <label>{t('Начало','Start')}<input className="tku-input" type="datetime-local" value={editor.start} disabled={busy} required onChange={e=>patch({start:e.target.value,startFold:'reject'})}/></label>
 <label>{t('Неоднозначное начало','Ambiguous start')}<select className="tku-input" aria-label={t('Неоднозначное начало','Ambiguous start')} value={editor.startFold} disabled={busy} onChange={e=>patch({startFold:e.target.value as Fold})}><option value="reject">{t('Требовать однозначность','Require unambiguous')}</option><option value="earlier">{t('Первый момент','Earlier instant')}</option><option value="later">{t('Второй момент','Later instant')}</option></select></label>
 <label>{t('Окончание','End')}<input className="tku-input" type="datetime-local" value={editor.end} disabled={busy} required onChange={e=>patch({end:e.target.value,endFold:'reject'})}/></label>
 <label>{t('Неоднозначное окончание','Ambiguous end')}<select className="tku-input" aria-label={t('Неоднозначное окончание','Ambiguous end')} value={editor.endFold} disabled={busy} onChange={e=>patch({endFold:e.target.value as Fold})}><option value="reject">{t('Требовать однозначность','Require unambiguous')}</option><option value="earlier">{t('Первый момент','Earlier instant')}</option><option value="later">{t('Второй момент','Later instant')}</option></select></label>
 <div className="tku-scheduler-toolbar"><button type="submit" className="tku-button tku-button--primary" disabled={busy||uncertain}>{t('Сохранить запись','Save booking')}</button><button type="button" className="tku-button tku-button--secondary" disabled={busy} onClick={closeEditor}>{t('Закрыть редактор','Close editor')}</button>{editor.id&&<button type="button" className="tku-button tku-button--secondary" disabled={busy||uncertain} onClick={()=>setCancelConfirm(true)}>{t('Отменить запись','Cancel booking')}</button>}{cancelConfirm&&<button type="button" className="tku-button tku-button--danger" disabled={busy||uncertain} onClick={()=>void submit(true)}>{t('Подтвердить отмену','Confirm cancellation')}</button>}</div></form>}
 {message&&<p role="status">{message}</p>}{error&&<p role="alert" className="tku-scheduler-error">{error}</p>}
 </section>
}
