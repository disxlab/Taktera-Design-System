/** @taktera/ui-react v4.0.0-alpha.3 — source package, requires npm type/build verification. */
import * as React from 'react';
import { useEffect, useId, useMemo, useRef, useState } from 'react';

export type Product = 'platform'|'clinic'|'beauty'|'spa'|'fitness'|'travel';
export type Theme = 'light'|'dark';
export type Tone = 'info'|'success'|'warning'|'error';
export type ButtonVariant = 'primary'|'secondary'|'ghost'|'danger';
export type SortDirection = 'asc'|'desc';
export type SortState = { key: string; direction: SortDirection };

export type ProviderProps = React.HTMLAttributes<HTMLDivElement> & { product?: Product; theme?: Theme };
export function TakteraProvider({product='platform',theme='light',className='',children,...rest}:ProviderProps){
  return <div {...rest} className={`tku-root ${className}`.trim()} data-product={product} data-theme={theme}>{children}</div>;
}

export type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant; loading?: boolean;
};
export const Button = React.forwardRef<HTMLButtonElement,ButtonProps>(function Button(
  {variant='primary',loading=false,disabled,className='',children,...rest},ref){
    return <button {...rest} ref={ref} className={`tku-button tku-button--${variant} ${className}`.trim()}
      disabled={disabled||loading} aria-busy={loading||undefined} data-loading={loading?'':undefined}>{children}</button>;
});

export type FieldProps = Omit<React.InputHTMLAttributes<HTMLInputElement>,'size'> & {
  label:string; error?:string; hint?:string;
};
export const Field = React.forwardRef<HTMLInputElement,FieldProps>(function Field(
  {label,error,hint,id,className='',...rest},ref){
    const uid=useId(), inputId=id??uid, descId=`${uid}-description`;
    return <div className="tku-field"><label htmlFor={inputId} className="tku-field__label">{label}</label>
      <input {...rest} id={inputId} ref={ref} className={`tku-input ${className}`.trim()}
        aria-invalid={error?true:undefined} aria-describedby={(error||hint)?descId:undefined}/>
      {(error||hint)&&<div id={descId} className={error?'tku-field__error':'tku-field__hint'}>{error||hint}</div>}
    </div>;
});

export type SelectProps = React.SelectHTMLAttributes<HTMLSelectElement> & {
  label:string; options:ReadonlyArray<{label:string;value:string}>;error?:string;
};
export function Select({label,options,error,id,...rest}:SelectProps){
  const uid=useId(), selectId=id??uid;
  return <div className="tku-field"><label htmlFor={selectId} className="tku-field__label">{label}</label>
    <select {...rest} id={selectId} className="tku-input" aria-invalid={error?true:undefined}
      aria-describedby={error?`${uid}-error`:undefined}>
      {options.map(opt=><option key={opt.value} value={opt.value}>{opt.label}</option>)}
    </select>{error&&<span className="tku-field__error" id={`${uid}-error`}>{error}</span>}</div>;
}

export type CheckProps=Omit<React.InputHTMLAttributes<HTMLInputElement>,'type'> & {label:string};
export function Checkbox({label,...rest}:CheckProps){return <label className="tku-check"><input {...rest} type="checkbox"/><span>{label}</span></label>;}
export function Switch({label,...rest}:CheckProps){return <label className="tku-check"><input {...rest} type="checkbox" role="switch"/><span>{label}</span></label>;}

export function Status({tone='info',children}: {tone?:Tone;children:React.ReactNode}){
  return <span className={`tku-status tku-status--${tone}`}>{children}</span>;
}
export function Alert({tone='info',title,children}: {tone?:Tone;title?:string;children:React.ReactNode}){
  return <section role={tone==='error'?'alert':'status'} className={`tku-alert tku-alert--${tone}`}>{title&&<strong>{title}</strong>}<p>{children}</p></section>;
}
export function Card({title,children}: {title?:string;children:React.ReactNode}){
  return <section className="tku-card">{title&&<h3 className="tku-card__title">{title}</h3>}{children}</section>;
}

export type TabItem={id:string;label:string;panel:React.ReactNode};
export type TabsProps={items:ReadonlyArray<TabItem>;value?:string;defaultValue?:string;onValueChange?:(id:string)=>void};
export function Tabs({items,value,defaultValue,onValueChange}:TabsProps){
  const id=useId(),[internal,setInternal]=useState(defaultValue??items[0]?.id);
  const current=value??internal, tabs=useRef<Array<HTMLButtonElement|null>>([]);
  const selected=items.some(i=>i.id===current)?current:items[0]?.id;
  const choose=(next:string,focus=false)=>{if(value===undefined)setInternal(next);onValueChange?.(next);
    if(focus){const i=items.findIndex(item=>item.id===next);tabs.current[i]?.focus();}};
  const keyDown=(e:React.KeyboardEvent<HTMLDivElement>)=>{const i=tabs.current.indexOf(document.activeElement as HTMLButtonElement);if(i<0)return;
    let next:number;
    switch(e.key){case 'ArrowRight':next=(i+1)%items.length;break;case 'ArrowLeft':next=(i+items.length-1)%items.length;break;
      case 'Home':next=0;break;case 'End':next=items.length-1;break;default:return;}
    e.preventDefault();choose(items[next].id,true);
  };
  if(!items.length)return null;
  return <div className="tku-tabs"><div className="tku-tablist" role="tablist" onKeyDown={keyDown}>
      {items.map((item,i)=><button key={item.id} ref={node=>{tabs.current[i]=node;}} type="button" role="tab" className="tku-tab"
        id={`${id}-tab-${i}`} aria-controls={`${id}-panel-${i}`} aria-selected={item.id===selected}
        tabIndex={item.id===selected?0:-1} onClick={()=>choose(item.id)}>{item.label}</button>)}
    </div>{items.map((item,i)=><div key={item.id} role="tabpanel" className="tku-tabpanel" id={`${id}-panel-${i}`}
      aria-labelledby={`${id}-tab-${i}`} hidden={item.id!==selected} tabIndex={0}>{item.panel}</div>)}
  </div>;
}

export type DialogProps={open:boolean;title:string;children:React.ReactNode;onClose:()=>void;onConfirm?:()=>void;confirmLabel?:string};
export function Dialog({open,title,children,onClose,onConfirm,confirmLabel='Сохранить'}:DialogProps){
  const ref=useRef<HTMLDialogElement>(null), id=useId(), opener=useRef<Element|null>(null);
  useEffect(()=>{const node=ref.current;if(!node)return;
    if(open&&!node.open){opener.current=document.activeElement;node.showModal();node.querySelector<HTMLButtonElement>('[data-dialog-cancel]')?.focus();}
    if(!open&&node.open)node.close();
  },[open]);
  const handleClose=()=>{if(opener.current instanceof HTMLElement && opener.current.isConnected)opener.current.focus();onClose();};
  return <dialog ref={ref} className="tku-dialog" aria-labelledby={id} onClose={handleClose} onCancel={e=>{e.preventDefault();ref.current?.close();}}>
    <h2 className="tku-dialog__title" id={id}>{title}</h2><div className="tku-dialog__body">{children}</div>
    <div className="tku-dialog__footer"><Button data-dialog-cancel variant="secondary" onClick={()=>ref.current?.close()}>Отмена</Button>
      {onConfirm&&<Button onClick={onConfirm}>{confirmLabel}</Button>}</div>
  </dialog>;
}

export type Column<T>={key:keyof T & string;label:string;sortable?:boolean;format?:(row:T)=>React.ReactNode};
export type DataTableProps<T>={columns:ReadonlyArray<Column<T>>;rows:ReadonlyArray<T>;rowKey:(row:T)=>string;
  sort?:SortState;onSortChange?:(sort:SortState)=>void;emptyText?:string};
export function DataTable<T extends Record<string,unknown>>({columns,rows,rowKey,sort,onSortChange,emptyText='Нет записей'}:DataTableProps<T>){
  const [local,setLocal]=useState<SortState|null>(null), current=sort??local;
  const changeSort=(key:string)=>{const next:SortState={key,direction:current?.key===key&&current.direction==='asc'?'desc':'asc'};
    if(sort===undefined)setLocal(next);onSortChange?.(next);};
  const sorted=useMemo(()=>{if(!current)return rows;const copy=[...rows];copy.sort((a,b)=>String(a[current.key]??'').localeCompare(String(b[current.key]??''),'ru',{numeric:true}));
    if(current.direction==='desc')copy.reverse();return copy;},[rows,current?.key,current?.direction]);
  return <div className="tku-table-scroll"><table className="tku-table"><thead><tr>{columns.map(col=><th key={col.key} scope="col"
      aria-sort={current?.key===col.key?(current.direction==='asc'?'ascending':'descending'):undefined}>
        {col.sortable?<Button variant="ghost" onClick={()=>changeSort(col.key)}>{col.label}</Button>:col.label}</th>)}</tr></thead>
    <tbody>{sorted.length?sorted.map(row=><tr key={rowKey(row)}>{columns.map(col=><td key={col.key}>{col.format?col.format(row):String(row[col.key]??'')}</td>)}</tr>):
      <tr><td className="tku-table__empty" colSpan={columns.length}>{emptyText}</td></tr>}</tbody></table></div>;
}

export type PaginationProps={page:number;pageCount:number;onPageChange:(page:number)=>void};
export function Pagination({page,pageCount,onPageChange}:PaginationProps){
  const safePage=Math.max(1,Math.min(page,pageCount||1));
  return <nav className="tku-pager" aria-label="Страницы"><Button variant="secondary" disabled={safePage<=1} onClick={()=>onPageChange(safePage-1)}>Назад</Button>
    <span className="tku-pager__info" aria-live="polite">{safePage} из {Math.max(pageCount,1)}</span>
    <Button variant="secondary" disabled={safePage>=pageCount} onClick={()=>onPageChange(safePage+1)}>Далее</Button></nav>;
}
export type Notice={id:string;message:string;tone?:Tone};
export function ToastRegion({notices,onDismiss}:{notices:ReadonlyArray<Notice>;onDismiss:(id:string)=>void}){
  return <div className="tku-toasts" role="region" aria-label="Уведомления"><div role="status" className="tku-toasts__live" aria-live="polite">
    {notices.length?notices[notices.length-1].message:''}</div>
    {notices.map(n=><div key={n.id} className={`tku-toast tku-toast--${n.tone??'info'}`}>
      <span>{n.message}</span><Button variant="ghost" aria-label="Закрыть уведомление" onClick={()=>onDismiss(n.id)}>Закрыть</Button></div>)}
  </div>;
}

export * from './advanced-grid.js';
export * from './AdvancedDataGrid.js';

export * from './remote-grid.js';
export * from './resource-scheduler.js';

export * from './RemoteDataGrid.js';
