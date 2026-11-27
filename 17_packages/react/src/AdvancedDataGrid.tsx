import * as React from 'react';
import { queryGrid,pageWindow,selectRows,virtualWindow } from './advanced-grid.js';
import type {GridColumn,GridSort} from './advanced-grid.js';

/** Client-side grid; all mutations and permission checks belong to the host. */
export type AdvancedDataGridProps<T>={
 rows:readonly T[]; columns:readonly GridColumn<T>[]; rowKey:(r:T)=>string; label:string;
 searchColumn:string; groupBy?:string; pageSize?:number; locale?:'ru-RU'|'en-US';
 /** Optional bounded scroll mode; accessible paginated fallback remains available. */
 virtualization?:boolean; onSelectionChange?:(ids:readonly string[])=>void;
};
const ROW=48, VIEWPORT=384;
export function AdvancedDataGrid<T>({rows,columns,rowKey,label,searchColumn,groupBy,pageSize=25,locale='ru-RU',virtualization=false,onSelectionChange}:AdvancedDataGridProps<T>){
 const ru=locale==='ru-RU',id=React.useId();
 const [search,setSearch]=React.useState(''),[sort,setSort]=React.useState<GridSort[]>([]),[page,setPage]=React.useState(0),[selection,setSelection]=React.useState<ReadonlySet<string>>(()=>new Set());
 const [virtual,setVirtual]=React.useState(virtualization),[scroll,setScroll]=React.useState(0);
 const scroller=React.useRef<HTMLDivElement>(null),head=React.useRef<HTMLTableSectionElement>(null),[headerHeight,setHeaderHeight]=React.useState(48);
 const isVirtual=virtualization&&virtual;
 const view=React.useMemo(()=>queryGrid(rows,columns,rowKey,{locale,filters:search?[{column:searchColumn,op:'contains',value:search}]:[],sort,groupBy}),[rows,columns,rowKey,locale,searchColumn,search,sort,groupBy]);
 const available=React.useMemo(()=>new Set(rows.map(rowKey)),[rows,rowKey]);
 const selected=React.useMemo(()=>[...selection].filter(k=>available.has(k)),[selection,available]);
 const window=pageWindow(view.rows.length,page,pageSize);
 const vw=virtualWindow(view.rows.length,scroll,Math.max(0,VIEWPORT-headerHeight),ROW,3);
 const direct=virtualWindow(view.rows.length,scroll,Math.max(0,VIEWPORT-headerHeight),ROW,0);
 const start=isVirtual?vw.start:window.start,end=isVirtual?vw.end:window.end;
 const visible=view.rows.slice(start,end),visibleIds=view.rows.slice(isVirtual?direct.start:start,isVirtual?direct.end:end).map(rowKey);
 const all=visibleIds.length>0&&visibleIds.every(k=>selection.has(k)),mixed=visibleIds.some(k=>selection.has(k))&&!all;
 const checkRef=React.useRef<HTMLInputElement>(null);
 React.useEffect(()=>{if(checkRef.current)checkRef.current.indeterminate=mixed},[mixed]);
 React.useEffect(()=>{setPage(p=>Math.min(p,window.pages-1))},[window.pages]);
 React.useEffect(()=>{setSelection(prev=>{const next=new Set([...prev].filter(k=>available.has(k)));return next.size===prev.size?prev:next})},[available]);
 React.useEffect(()=>{if(!isVirtual||!head.current)return;const el=head.current;const update=()=>setHeaderHeight(el.getBoundingClientRect().height);update();const observer=new ResizeObserver(update);observer.observe(el);return()=>observer.disconnect()},[isVirtual]);
 function resetWindow(){setPage(0);setScroll(0);if(scroller.current)scroller.current.scrollTop=0}
 function scrollChanged(e:React.UIEvent<HTMLDivElement>){if(!isVirtual)return;const node=e.currentTarget,next=node.scrollTop;const nextWindow=virtualWindow(view.rows.length,next,Math.max(0,VIEWPORT-headerHeight),ROW,3);const focused=document.activeElement?.closest<HTMLElement>('tr[data-grid-index]');if(focused&&node.contains(focused)){const i=Number(focused.dataset.gridIndex);if(i<nextWindow.start||i>=nextWindow.end)node.focus({preventScroll:true})}setScroll(next)}
 function keyScroll(e:React.KeyboardEvent<HTMLDivElement>){if(!isVirtual||e.target!==e.currentTarget)return;const node=e.currentTarget;const moves:Record<string,number>={ArrowDown:node.scrollTop+ROW,ArrowUp:node.scrollTop-ROW,PageDown:node.scrollTop+VIEWPORT-headerHeight,PageUp:node.scrollTop-VIEWPORT+headerHeight,Home:0,End:node.scrollHeight};if(Object.hasOwn(moves,e.key)){e.preventDefault();node.scrollTop=moves[e.key]}}
 const toggle=(ids:string[],checked:boolean)=>{const next=selectRows(new Set(selected),ids,checked);setSelection(next);onSelectionChange?.([...next])};
 const changeSort=(column:string)=>{setSort(old=>[{column,direction:old[0]?.column===column&&old[0].direction==='asc'?'desc':'asc'}]);resetWindow()};
 const rowLabel=ru?'Выбрать запись ':'Select row ';
 const scrollLabel=ru?'Прокрутка реестра':'Registry scroll';
 return <section aria-labelledby={id}><h2 id={id}>{label}</h2>
 <label className="tku-field">{ru?'Поиск в реестре':'Search registry'}<input className="tku-input" value={search} onChange={e=>{setSearch(e.target.value);resetWindow()}}/></label>
 <p aria-live="polite">{ru?'Выбрано: ':'Selected: '}{selected.length}</p>
 {virtualization&&<button type="button" className="tku-button tku-button--secondary" onClick={()=>{setVirtual(v=>!v);resetWindow()}}>{isVirtual?(ru?'Постраничный режим':'Paginated mode'):(ru?'Виртуальный режим':'Virtual mode')}</button>}
 {groupBy&&<ul aria-label={ru?'Группы':'Groups'}>{view.groups.map(g=><li key={JSON.stringify(g.value)}>{String(g.value??'—')}: {g.count}</li>)}</ul>}
 <div ref={scroller} className={'tku-table-scroll'+(isVirtual?' tku-virtual-scroll':'')} role={isVirtual?'region':undefined} aria-label={isVirtual?scrollLabel:undefined} tabIndex={isVirtual?0:undefined} onScroll={scrollChanged} onKeyDown={keyScroll} style={isVirtual?{height:VIEWPORT}:undefined}>
 <table className={'tku-table'+(isVirtual?' tku-virtual-table':'')} aria-label={isVirtual?label:undefined} aria-rowcount={isVirtual?view.rows.length+1:undefined}>
 {!isVirtual&&<caption>{label}</caption>}<thead ref={head}><tr aria-rowindex={isVirtual?1:undefined}><th scope="col"><input ref={checkRef} type="checkbox" aria-label={isVirtual?(ru?'Выбрать видимые записи':'Select visible rows'):(ru?'Выбрать страницу':'Select page')} checked={all} disabled={!visibleIds.length} onChange={e=>toggle(visibleIds,e.target.checked)}/></th>{columns.map(c=><th key={c.id} scope="col" aria-sort={sort[0]?.column===c.id?(sort[0].direction==='asc'?'ascending':'descending'):undefined}><button type="button" className="tku-button tku-button--ghost" onClick={()=>changeSort(c.id)}>{c.label}</button></th>)}</tr></thead>
 <tbody>{isVirtual&&vw.before>0&&<tr aria-hidden="true" className="tku-virtual-spacer"><td colSpan={columns.length+1} style={{height:vw.before}}/></tr>}
 {visible.map((r,i)=><tr key={rowKey(r)} data-grid-index={start+i} aria-rowindex={isVirtual?start+i+2:undefined}><td><input type="checkbox" aria-label={rowLabel+rowKey(r)} checked={selection.has(rowKey(r))} onChange={e=>toggle([rowKey(r)],e.target.checked)}/></td>{columns.map(c=><td key={c.id}>{isVirtual?<span className="tku-virtual-cell" title={String(c.value(r)??'—')}>{String(c.value(r)??'—')}</span>:String(c.value(r)??'—')}</td>)}</tr>)}
 {isVirtual&&vw.after>0&&<tr aria-hidden="true" className="tku-virtual-spacer"><td colSpan={columns.length+1} style={{height:vw.after}}/></tr>}
 {!visible.length&&<tr><td colSpan={columns.length+1}>{ru?'Нет записей':'No records'}</td></tr>}</tbody></table></div>
 {isVirtual?<p>{ru?'Записей: ':'Records: '}{view.rows.length}</p>:<nav className="tku-pager" aria-label={ru?'Страницы реестра':'Registry pages'}><button type="button" className="tku-button tku-button--secondary" disabled={window.page===0} onClick={()=>setPage(window.page-1)}>{ru?'Предыдущая':'Previous'}</button><span aria-live="polite">{window.page+1} / {window.pages}</span><button type="button" className="tku-button tku-button--secondary" disabled={window.page+1===window.pages} onClick={()=>setPage(window.page+1)}>{ru?'Следующая':'Next'}</button></nav>}</section>;
}
