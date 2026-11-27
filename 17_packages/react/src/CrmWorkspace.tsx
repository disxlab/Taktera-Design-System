import * as React from 'react';
import {chronological,timeLabel,activeFields,formPayload,formErrors,searchCommands} from './crm-core.js';
import type {UiLocale,CustomerSummary,ActivityItem,CenterNotice,FormStep,FormValues,FormValue,FieldError,WorkspaceCommand} from './crm-core.js';
const secondary='tku-button tku-button--secondary',primary='tku-button tku-button--primary';
const tr=(locale:UiLocale,r:string,e:string)=>locale==='ru-RU'?r:e;
export function CustomerProfile({customer,locale='ru-RU',onEdit}:{customer:CustomerSummary;locale?:UiLocale;onEdit?:()=>void}){
 const id=React.useId();return <section className="tku-crm-card" aria-labelledby={id}><h2 id={id}>{customer.displayName}</h2><p>{customer.status}</p><dl className="tku-crm-facts">{[...customer.contacts,...(customer.facts??[])].map(f=><React.Fragment key={f.id}><dt>{f.label}</dt><dd>{f.value}</dd></React.Fragment>)}</dl>{onEdit&&<button type="button" className={secondary} onClick={onEdit}>{tr(locale,'Редактировать клиента','Edit customer')}</button>}</section>
}
export function ActivityTimeline({items,zone,locale='ru-RU'}:{items:readonly ActivityItem[];zone:string;locale?:UiLocale}){
 const id=React.useId(),[kind,setKind]=React.useState('');const kinds=[...new Set(items.map(i=>i.kind))];const shown=chronological(items.filter(i=>!kind||i.kind===kind));
 return <section className="tku-crm-card" aria-labelledby={id}><h2 id={id}>{tr(locale,'История взаимодействий','Activity timeline')}</h2><label htmlFor={id+'-kind'}>{tr(locale,'Тип события','Activity type')}</label><select id={id+'-kind'} className="tku-input" value={kind} onChange={e=>setKind(e.target.value)}><option value="">{tr(locale,'Все события','All events')}</option>{kinds.map(k=><option key={k}>{k}</option>)}</select>
 {shown.length?<ol className="tku-activity">{shown.map(i=><li key={i.id}><time dateTime={i.at}>{timeLabel(i.at,zone)}</time><h3>{i.title}</h3><p>{i.kind}</p>{i.description&&<p>{i.description}</p>}</li>)}</ol>:<p>{tr(locale,'Нет событий','No events')}</p>}</section>
}
export type FormSaveRequest={values:Record<string,FormValue>;version:string;idempotencyKey:string};
export type FormSaveResult={status:'applied'|'conflict'|'invalid'|'forbidden'};
export function AdvancedForm({label,steps,initialValues,version,locale='ru-RU',onSave}:{label:string;steps:readonly FormStep[];initialValues:FormValues;version:string;locale?:UiLocale;onSave:(request:FormSaveRequest,signal:AbortSignal)=>Promise<FormSaveResult>}){
 const id=React.useId(),[values,setValues]=React.useState<FormValues>(()=>({...initialValues})),[index,setIndex]=React.useState(0),[errors,setErrors]=React.useState<Record<string,FieldError>>({}),[message,setMessage]=React.useState(''),[failure,setFailure]=React.useState(''),[busy,setBusy]=React.useState(false),[locked,setLocked]=React.useState(false);
 const pending=React.useRef<AbortController|undefined>(undefined),summary=React.useRef<HTMLDivElement>(null),heading=React.useRef<HTMLHeadingElement>(null);
 React.useEffect(()=>()=>pending.current?.abort(),[]);
 React.useEffect(()=>{if(Object.keys(errors).length)summary.current?.focus()},[errors]);
 const step=steps[Math.min(index,steps.length-1)],active=new Set(activeFields(steps,values).map(f=>f.id));
 const translate=(e:FieldError)=>e==='required'?tr(locale,'Обязательное поле','Required field'):e==='tooLong'?tr(locale,'Слишком длинное значение','Value too long'):tr(locale,'Некорректное значение','Invalid value');
 function change(key:string,value:FormValue){setValues(v=>({...v,[key]:value}));setErrors({});setMessage('');setFailure('')}
 function navigate(n:number){setIndex(n);setErrors({});requestAnimationFrame(()=>heading.current?.focus())}
 async function next(){if(busy||locked||pending.current)return;setFailure('');setMessage('');
  const last=index===steps.length-1,errs=formErrors(steps,values,last?undefined:step.id);setErrors(errs);
  if(Object.keys(errs).length){const first=steps.findIndex(s=>s.fields.some(f=>Object.hasOwn(errs,f.id)));if(first>=0)setIndex(first);return}
  if(!last){navigate(index+1);return}
  const abort=new AbortController();pending.current=abort;setBusy(true);
  try{const result=await onSave({values:formPayload(steps,values),version,idempotencyKey:globalThis.crypto.randomUUID()},abort.signal);if(abort.signal.aborted)return;
   if(result.status==='applied'){setMessage(tr(locale,'Сохранено','Saved'));setLocked(true)}
   else if(['conflict','invalid','forbidden'].includes(result.status)){setFailure(tr(locale,'Сервер отклонил сохранение: ','Server rejected save: ')+result.status)}
   else throw Error('Unknown result');
  }catch{if(!abort.signal.aborted){setLocked(true);setFailure(tr(locale,'Результат неизвестен. Сверьте данные с сервером.','Outcome unknown. Reconcile with server.'))}}
  finally{pending.current=undefined;if(!abort.signal.aborted)setBusy(false)}
 }
 return <section className="tku-crm-card" aria-labelledby={id}><h2 id={id}>{label}</h2><ol className="tku-form-steps">{steps.map((s,i)=><li key={s.id} aria-current={i===index?'step':undefined}>{s.label}</li>)}</ol>
 <form noValidate aria-label={label} onSubmit={e=>{e.preventDefault();void next()}}><h3 ref={heading} tabIndex={-1}>{step.label}</h3>
 {Object.keys(errors).length>0&&<div ref={summary} tabIndex={-1} role="alert" className="tku-crm-error"><strong>{tr(locale,'Исправьте ошибки','Correct errors')}</strong><ul>{steps.flatMap(s=>s.fields).filter(f=>errors[f.id]).map(f=><li key={f.id}>{f.label}: {translate(errors[f.id])}</li>)}</ul></div>}
 {step.fields.filter(f=>active.has(f.id)).map(f=>{const fid=id+'-'+f.id,error=errors[f.id],v=values[f.id];const attrs={id:fid,disabled:busy||locked,required:!!f.required,'aria-invalid':!!error||undefined,'aria-describedby':error?fid+'-error':undefined};
 return <div key={f.id} className="tku-field"><label htmlFor={fid}>{f.label}</label>{f.kind==='select'?<select {...attrs} className="tku-input" value={typeof v==='string'?v:''} onChange={e=>change(f.id,e.target.value)}><option value="">{tr(locale,'Выберите','Select')}</option>{f.options?.map(o=><option key={o.value} value={o.value}>{o.label}</option>)}</select>:f.kind==='checkbox'?<input {...attrs} type="checkbox" checked={v===true} onChange={e=>change(f.id,e.target.checked)}/>:<input {...attrs} className="tku-input" type={f.kind} value={typeof v==='string'?v:''} maxLength={f.maxLength} onChange={e=>change(f.id,e.target.value)}/>}
 {error&&<span id={fid+'-error'} className="tku-field__error">{translate(error)}</span>}</div>})}
 <div className="tku-crm-actions"><button type="button" className={secondary} disabled={index===0||busy||locked} onClick={()=>navigate(index-1)}>{tr(locale,'Назад','Back')}</button><button type="submit" className={primary} disabled={busy||locked}>{index===steps.length-1?tr(locale,'Сохранить форму','Save form'):tr(locale,'Далее','Next')}</button></div></form>
 {message&&<p role="status">{message}</p>}{failure&&<p role="alert" className="tku-crm-error">{failure}</p>}</section>
}
export type WorkspacePage={id:string;label:string;content:React.ReactNode};
export function ApplicationShell({label,pages,active,onNavigate,locale='ru-RU',tools}:{label:string;pages:readonly WorkspacePage[];active:string;onNavigate:(id:string)=>void;locale?:UiLocale;tools?:React.ReactNode}){
 const id=React.useId(),selected=pages.some(p=>p.id===active)?active:pages[0]?.id,buttons=React.useRef<Array<HTMLButtonElement|null>>([]);
 function key(e:React.KeyboardEvent){const i=buttons.current.indexOf(document.activeElement as HTMLButtonElement);if(i<0||!pages.length)return;const n=e.key==='ArrowRight'?(i+1)%pages.length:e.key==='ArrowLeft'?(i+pages.length-1)%pages.length:e.key==='Home'?0:e.key==='End'?pages.length-1:-1;if(n>=0){e.preventDefault();onNavigate(pages[n].id);buttons.current[n]?.focus()}}
 return <section className="tku-app-shell" aria-labelledby={id}><header className="tku-app-header"><h2 id={id}>{label}</h2>{tools}</header><div className="tku-app-body"><nav aria-label={tr(locale,'Разделы приложения','Application sections')} className="tku-app-nav">{pages.map(p=><button type="button" key={p.id} className={secondary} aria-current={p.id===selected?'page':undefined} onClick={()=>onNavigate(p.id)}>{p.label}</button>)}</nav>
 <div className="tku-app-workspace"><div role="tablist" aria-label={tr(locale,'Рабочие вкладки','Workspace tabs')} className="tku-tablist" onKeyDown={key}>{pages.map((p,i)=><button key={p.id} type="button" ref={el=>{buttons.current[i]=el}} role="tab" id={id+'-tab-'+i} aria-controls={id+'-panel-'+i} aria-selected={p.id===selected} tabIndex={p.id===selected?0:-1} className="tku-tab" onClick={()=>onNavigate(p.id)}>{p.label}</button>)}</div>
 {pages.map((p,i)=><div key={p.id} role="tabpanel" id={id+'-panel-'+i} aria-labelledby={id+'-tab-'+i} hidden={p.id!==selected} tabIndex={0}>{p.content}</div>)}</div></div></section>
}
export function CommandPalette({commands,onCommand,locale='ru-RU',shortcut=false}:{commands:readonly WorkspaceCommand[];onCommand:(id:string)=>void;locale?:UiLocale;shortcut?:boolean}){
 const id=React.useId(),dialog=React.useRef<HTMLDialogElement>(null),input=React.useRef<HTMLInputElement>(null),opener=React.useRef<HTMLElement|null>(null),[query,setQuery]=React.useState(''),[active,setActive]=React.useState(0);
 const matches=searchCommands(commands,query,locale),enabled=matches.filter(c=>!c.disabled),current=enabled[Math.min(active,Math.max(0,enabled.length-1))];
 function open(){if(!dialog.current||dialog.current.open)return;opener.current=document.activeElement instanceof HTMLElement?document.activeElement:null;setQuery('');setActive(0);dialog.current.showModal();input.current?.focus()}
 function close(){dialog.current?.close()}
 function execute(command?:WorkspaceCommand){if(!command||command.disabled)return;close();onCommand(command.id)}
 React.useEffect(()=>{if(!shortcut)return;const handler=(e:KeyboardEvent)=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'&&!e.altKey&&!e.repeat&&!document.querySelector('dialog[open]')){e.preventDefault();open()}};document.addEventListener('keydown',handler);return()=>document.removeEventListener('keydown',handler)},[shortcut]);
 return <><button type="button" className={secondary} onClick={open}>{tr(locale,'Команды','Commands')}</button><dialog className="tku-dialog" ref={dialog} aria-labelledby={id} onClose={()=>{if(opener.current?.isConnected)opener.current.focus()}}><h2 id={id}>{tr(locale,'Командная палитра','Command palette')}</h2>
 <label htmlFor={id+'-search'}>{tr(locale,'Поиск команд','Search commands')}</label><input ref={input} id={id+'-search'} className="tku-input" value={query} onChange={e=>{setQuery(e.target.value);setActive(0)}} onKeyDown={e=>{if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();setActive(n=>Math.max(0,Math.min(enabled.length-1,n+(e.key==='ArrowDown'?1:-1))))}if(e.key==='Enter'){e.preventDefault();execute(current)}}}/>
 <p role="status">{current?tr(locale,'Выбрано: ','Selected: ')+current.label:tr(locale,'Нет доступных команд','No available commands')}</p><ul className="tku-command-list">{matches.map(c=><li key={c.id}><button type="button" className={secondary} data-command-current={c.id===current?.id?'true':undefined} disabled={c.disabled} onClick={()=>execute(c)}>{c.label}</button></li>)}</ul><button type="button" className={secondary} onClick={close}>{tr(locale,'Закрыть','Close')}</button></dialog></>
}
export function NotificationCenter({notices,onRead,onReadAll,zone,locale='ru-RU'}:{notices:readonly CenterNotice[];onRead:(id:string)=>void;onReadAll?:()=>void;zone:string;locale?:UiLocale}){
 const id=React.useId(),[only,setOnly]=React.useState(false),heading=React.useRef<HTMLHeadingElement>(null);const unread=notices.filter(n=>!n.read).length;
 return <section className="tku-crm-card" aria-labelledby={id}><h2 ref={heading} tabIndex={-1} id={id}>{tr(locale,'Центр уведомлений','Notification center')}</h2><p aria-live="polite">{tr(locale,'Непрочитано: ','Unread: ')}{unread}</p><label className="tku-check"><input type="checkbox" checked={only} onChange={e=>setOnly(e.target.checked)}/>{tr(locale,'Только непрочитанные','Unread only')}</label>{onReadAll&&<button type="button" className={secondary} disabled={!unread} onClick={()=>{onReadAll();heading.current?.focus()}}>{tr(locale,'Отметить все прочитанными','Mark all read')}</button>}
 <ul className="tku-activity">{chronological(notices.filter(n=>!only||!n.read)).map(n=><li key={n.id}><time dateTime={n.at}>{timeLabel(n.at,zone)}</time><h3>{n.title}</h3>{n.description&&<p>{n.description}</p>}<p>{n.read?tr(locale,'Прочитано','Read'):tr(locale,'Новое','New')}</p>{!n.read&&<button type="button" className={secondary} aria-label={tr(locale,'Отметить прочитанным: ','Mark read: ')+n.title} onClick={()=>{onRead(n.id);heading.current?.focus()}}>{tr(locale,'Отметить прочитанным','Mark read')}</button>}</li>)}</ul>{!notices.some(n=>!only||!n.read)&&<p>{tr(locale,'Нет уведомлений','No notifications')}</p>}</section>
}
