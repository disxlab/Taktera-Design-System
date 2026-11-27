import * as React from 'react';
import type {GridColumn,GridSort} from './advanced-grid.js';
import {RemoteGridController,prepareBulk,executeBulk,remainingSelection} from './remote-grid.js';
import type {GridTransport,ReadState,BulkItem,BulkResult} from './remote-grid.js';
/** Remote pagination and explicit versioned selection. Host must provide stable transport
 * scoped to one authenticated tenant; remount on tenant/session change. */
export function RemoteDataGrid<T>({transport,columns,label,searchColumn,pageSize=25,locale='ru-RU',bulkAction}:{transport:GridTransport<T>;columns:readonly GridColumn<T>[];label:string;searchColumn:string;pageSize?:number;locale?:'ru-RU'|'en-US';bulkAction?:{id:string;label:string}}){
 const ru=locale==='ru-RU',id=React.useId();
 const [search,setSearch]=React.useState(''),[sort,setSort]=React.useState<GridSort[]>([]),[cursors,setCursors]=React.useState<(string|undefined)[]>([undefined]);
 const [state,setState]=React.useState<ReadState<T>>({status:'idle'}),[reload,setReload]=React.useState(0);
 const [selected,setSelected]=React.useState<readonly BulkItem[]>([]),[confirm,setConfirm]=React.useState(false),[busy,setBusy]=React.useState(false);
 const [outcomes,setOutcomes]=React.useState<readonly BulkResult[]>([]),[uncertain,setUncertain]=React.useState(false);
 const pending=React.useRef<AbortController|undefined>(undefined),dialog=React.useRef<HTMLDialogElement>(null),opener=React.useRef<HTMLButtonElement>(null);
 const cursor=cursors.at(-1),page=state.status==='ready'?state.page:undefined;
 React.useEffect(()=>{const controller=new RemoteGridController(transport);void controller.read({query:{locale,filters:search?[{column:searchColumn,op:'contains',value:search}]:[],sort},cursor,limit:pageSize},setState).catch(error=>setState({status:'error',error}));return()=>controller.dispose()},[transport,search,searchColumn,sort,cursor,pageSize,locale,reload]);
 React.useEffect(()=>()=>pending.current?.abort(),[]);
 React.useEffect(()=>{const node=dialog.current;if(!node)return;if(confirm&&!node.open)node.showModal();if(!confirm&&node.open)node.close()},[confirm]);
 const reset=()=>{setCursors([undefined]);setSelected([]);setOutcomes([])};
 const disabled=busy||confirm||state.status!=='ready';
 function toggle(item:BulkItem,checked:boolean){setSelected(old=>checked?[...old.filter(x=>x.id!==item.id),item]:old.filter(x=>x.id!==item.id))}
 async function runBulk(){
  if(!bulkAction||!confirm||busy||pending.current||uncertain||state.status!=='ready')return;
  setConfirm(false);setBusy(true);setOutcomes([]);
  const abort=new AbortController();pending.current=abort;
  try{
   const request=prepareBulk(bulkAction.id,selected,globalThis.crypto.randomUUID(),true);
   const result=await executeBulk(transport,request,abort.signal);
   if(abort.signal.aborted)return;
   setOutcomes(result);setSelected(remainingSelection(selected,result));setReload(n=>n+1);
  }catch{if(!abort.signal.aborted)setUncertain(true)}
  finally{pending.current=undefined;if(!abort.signal.aborted)setBusy(false)}
 }
 const statusLabels:Record<BulkResult['status'],string>=ru?{applied:'Выполнено',conflict:'Конфликт версии',forbidden:'Нет доступа',invalid:'Ошибка данных',failed:'Ошибка'}:{applied:'Applied',conflict:'Version conflict',forbidden:'Forbidden',invalid:'Invalid',failed:'Failed'};
 return <section aria-labelledby={id}><h2 id={id}>{label}</h2>
 <label className="tku-field">{ru?'Серверный поиск':'Server search'}<input className="tku-input" value={search} disabled={busy||confirm} onChange={e=>{reset();setSearch(e.target.value)}}/></label>
 <p role="status">{ru?'Выбрано: ':'Selected: '}{selected.length}</p>
 {state.status==='loading'&&<p role="status">{ru?'Загрузка…':'Loading…'}</p>}
 {state.status==='error'&&<p role="alert">{ru?'Не удалось загрузить записи':'Could not load records'} <button type="button" className="tku-button tku-button--secondary" onClick={()=>setReload(n=>n+1)}>{ru?'Повторить загрузку':'Retry read'}</button></p>}
 <div className="tku-table-scroll"><table className="tku-table" aria-busy={state.status==='loading'}><caption>{label}</caption><thead><tr><th scope="col">{ru?'Выбор':'Selection'}</th>{columns.map(c=><th scope="col" key={c.id} aria-sort={sort[0]?.column===c.id?(sort[0].direction==='asc'?'ascending':'descending'):undefined}><button type="button" className="tku-button tku-button--ghost" disabled={busy||confirm} onClick={()=>{reset();setSort(old=>[{column:c.id,direction:old[0]?.column===c.id&&old[0].direction==='asc'?'desc':'asc'}])}}>{c.label}</button></th>)}</tr></thead><tbody>
 {page?.rows.map(r=><tr key={r.id}><td><input type="checkbox" disabled={disabled} aria-label={(ru?'Выбрать серверную запись ':'Select remote row ')+r.id} checked={selected.some(x=>x.id===r.id)} onChange={e=>toggle({id:r.id,version:r.version},e.target.checked)}/></td>{columns.map(c=><td key={c.id}>{String(c.value(r.data)??'—')}</td>)}</tr>)}
 {(!page||!page.rows.length)&&<tr><td colSpan={columns.length+1}>{state.status==='loading'?(ru?'Загрузка…':'Loading…'):(ru?'Нет записей':'No records')}</td></tr>}</tbody></table></div>
 <nav className="tku-pager" aria-label={ru?'Серверные страницы':'Remote pages'}><button type="button" className="tku-button tku-button--secondary" disabled={disabled||cursors.length<=1} onClick={()=>setCursors(x=>x.slice(0,-1))}>{ru?'Назад':'Previous'}</button><span>{cursors.length}</span><button type="button" className="tku-button tku-button--secondary" disabled={disabled||!page?.nextCursor} onClick={()=>setCursors(x=>[...x,page?.nextCursor])}>{ru?'Далее':'Next'}</button></nav>
 {bulkAction&&transport.bulk&&<button ref={opener} type="button" className="tku-button tku-button--secondary" disabled={!selected.length||disabled||uncertain||outcomes.length>0} onClick={()=>setConfirm(true)}>{bulkAction.label}</button>}
 <dialog ref={dialog} className="tku-dialog" aria-labelledby={id+'-confirm'} onCancel={e=>{e.preventDefault();setConfirm(false)}} onClose={()=>{setConfirm(false);opener.current?.focus()}}><h2 id={id+'-confirm'}>{ru?'Подтвердить массовую операцию':'Confirm bulk action'}</h2><p>{bulkAction?.label}: {selected.length}</p><div className="tku-dialog__footer"><button type="button" className="tku-button tku-button--secondary" onClick={()=>setConfirm(false)}>{ru?'Отмена':'Cancel'}</button><button type="button" className="tku-button tku-button--primary" onClick={()=>void runBulk()}>{ru?'Выполнить':'Execute'}</button></div></dialog>
 {outcomes.length>0&&<><ul aria-label={ru?'Результаты операции':'Operation results'}>{outcomes.map(o=><li key={o.id}>{o.id}: {statusLabels[o.status]}</li>)}</ul><button type="button" className="tku-button tku-button--secondary" disabled={busy} onClick={()=>{setSelected([]);setOutcomes([]);setReload(n=>n+1)}}>{ru?'Обновить и выбрать заново':'Refresh and reselect'}</button></>}
 {uncertain&&<p role="alert">{ru?'Результат неизвестен. Сверьте состояние с сервером и заново откройте реестр перед повтором.':'Outcome unknown. Reconcile with the server and reopen this grid before retrying.'}</p>}
 </section>
}
