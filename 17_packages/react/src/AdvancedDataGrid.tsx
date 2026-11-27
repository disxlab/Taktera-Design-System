import * as React from 'react';
import { queryGrid,pageWindow,selectRows } from './advanced-grid.js';
import type {GridColumn,GridSort} from './advanced-grid.js';
export type AdvancedDataGridProps<T>={rows:readonly T[];columns:readonly GridColumn<T>[];rowKey:(r:T)=>string;label:string;searchColumn:string;groupBy?:string;pageSize?:number;locale?:'ru-RU'|'en-US';onSelectionChange?:(ids:readonly string[])=>void};
export function AdvancedDataGrid<T>({rows,columns,rowKey,label,searchColumn,groupBy,pageSize=25,locale='ru-RU',onSelectionChange}:AdvancedDataGridProps<T>){
 const ru=locale==='ru-RU',id=React.useId(),[search,setSearch]=React.useState(''),[sort,setSort]=React.useState<GridSort[]>([]),[page,setPage]=React.useState(0),[selection,setSelection]=React.useState<ReadonlySet<string>>(()=>new Set());
 const view=React.useMemo(()=>queryGrid(rows,columns,rowKey,{locale,filters:search?[{column:searchColumn,op:'contains',value:search}]:[],sort,groupBy}),[rows,columns,rowKey,locale,searchColumn,search,sort,groupBy]);
 const window=pageWindow(view.rows.length,page,pageSize),visible=view.rows.slice(window.start,window.end),visibleIds=visible.map(rowKey),available=new Set(rows.map(rowKey));
 const selected=[...selection].filter(k=>available.has(k));
 const all=visibleIds.length>0&&visibleIds.every(k=>selection.has(k));
 const mixed=visibleIds.some(k=>selection.has(k))&&!all;
 const checkRef=React.useRef<HTMLInputElement>(null);React.useEffect(()=>{if(checkRef.current)checkRef.current.indeterminate=mixed},[mixed]);
 React.useEffect(()=>{setPage(p=>Math.min(p,window.pages-1))},[window.pages]);
 React.useEffect(()=>{setSelection(prev=>{const next=new Set([...prev].filter(k=>rows.some(r=>rowKey(r)===k)));return next.size===prev.size?prev:next})},[rows,rowKey]);
 const toggle=(ids:string[],checked:boolean)=>{const next=selectRows(new Set(selected),ids,checked);setSelection(next);onSelectionChange?.([...next])};
 const changeSort=(column:string)=>{setSort(old=>[{column,direction:old[0]?.column===column&&old[0].direction==='asc'?'desc':'asc'}]);setPage(0)};
 return <section aria-labelledby={id}><h2 id={id}>{label}</h2>
 <label className="tku-field">{ru?'Поиск в реестре':'Search registry'}<input className="tku-input" value={search} onChange={e=>{setSearch(e.target.value);setPage(0)}}/></label>
 <p aria-live="polite">{ru?'Выбрано: ':'Selected: '}{selected.length}</p>
 {groupBy&&<ul aria-label={ru?'Группы':'Groups'}>{view.groups.map(g=><li key={JSON.stringify(g.value)}>{String(g.value??'—')}: {g.count}</li>)}</ul>}
 <div className="tku-table-scroll"><table className="tku-table"><caption>{label}</caption><thead><tr><th scope="col"><input ref={checkRef} type="checkbox" aria-label={ru?'Выбрать страницу':'Select page'} checked={all} disabled={!visibleIds.length} onChange={e=>toggle(visibleIds,e.target.checked)}/></th>{columns.map(c=><th key={c.id} scope="col" aria-sort={sort[0]?.column===c.id?(sort[0].direction==='asc'?'ascending':'descending'):undefined}><button type="button" className="tku-button tku-button--ghost" onClick={()=>changeSort(c.id)}>{c.label}</button></th>)}</tr></thead>
 <tbody>{visible.map(r=><tr key={rowKey(r)}><td><input type="checkbox" aria-label={(ru?'Выбрать запись ':'Select row ')+rowKey(r)} checked={selection.has(rowKey(r))} onChange={e=>toggle([rowKey(r)],e.target.checked)}/></td>{columns.map(c=><td key={c.id}>{String(c.value(r)??'—')}</td>)}</tr>)}{!visible.length&&<tr><td colSpan={columns.length+1}>{ru?'Нет записей':'No records'}</td></tr>}</tbody></table></div>
 <nav className="tku-pager" aria-label={ru?'Страницы реестра':'Registry pages'}><button type="button" className="tku-button tku-button--secondary" disabled={window.page===0} onClick={()=>setPage(window.page-1)}>{ru?'Предыдущая':'Previous'}</button><span aria-live="polite">{window.page+1} / {window.pages}</span><button type="button" className="tku-button tku-button--secondary" disabled={window.page+1===window.pages} onClick={()=>setPage(window.page+1)}>{ru?'Следующая':'Next'}</button></nav></section>;
}
