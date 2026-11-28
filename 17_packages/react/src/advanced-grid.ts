/** Pure BR5 grid query model. No DOM, backend, credentials or mutation. */
export type GridValue = string | number | boolean | null;
export type GridColumn<T> = { id: string; label: string; value: (row: T) => GridValue };
export type GridSort = { column: string; direction: 'asc' | 'desc' };
export type GridFilter = { column: string; op: 'contains'; value: string } | { column: string; op: 'equals'; value: GridValue } | { column: string; op: 'range'; min?: number; max?: number };
export type GridQuery = { filters?: readonly GridFilter[]; sort?: readonly GridSort[]; groupBy?: string; locale?: 'ru-RU' | 'en-US' };
export type GridGroup = { value: GridValue; count: number };
export type GridResult<T> = { rows: T[]; groups: GridGroup[] };
export function queryGrid<T>(rows: readonly T[], columns: readonly GridColumn<T>[], rowKey: (r:T)=>string, query: GridQuery = {}): GridResult<T> {
  const byId = new Map(columns.map(c=>[c.id,c] as const));
  if(byId.size!==columns.length)throw Error('Duplicate column ID');
  const ids=new Set<string>();for(const r of rows){const id=rowKey(r);if(!id||ids.has(id))throw Error('Duplicate or empty row ID');ids.add(id)}
  const get=(id:string)=>{const c=byId.get(id);if(!c)throw Error('Unknown column '+id);return c.value};
  const locale=query.locale??'ru-RU',collator=new Intl.Collator(locale,{numeric:true,sensitivity:'base'});
  const norm=(v:GridValue)=>String(v??'').normalize('NFKC').toLocaleLowerCase(locale);
  const filters=(query.filters??[]).map(f=>{const value=get(f.column);if(f.op==='range'&&((f.min!==undefined&&!Number.isFinite(f.min))||(f.max!==undefined&&!Number.isFinite(f.max))||(f.min!==undefined&&f.max!==undefined&&f.min>f.max)))throw Error('Invalid range');return {f,value}});
  const sort=(query.sort??[]).map(s=>({s,value:get(s.column)}));
  const group=query.groupBy===undefined?undefined:get(query.groupBy);
  const result=rows.filter(r=>filters.every(({f,value})=>{const v=value(r);switch(f.op){case 'contains':return norm(v).includes(norm(f.value));case 'equals':return v===f.value;case 'range':return typeof v==='number'&&Number.isFinite(v)&&(f.min===undefined||v>=f.min)&&(f.max===undefined||v<=f.max)}}));
  result.sort((a,b)=>{for(const {s,value} of sort){const x=value(a),y=value(b);if(x===null||y===null){if(x!==y)return x===null?1:-1;continue}const c=typeof x==='number'&&typeof y==='number'?x-y:collator.compare(String(x),String(y));if(c)return s.direction==='asc'?c:-c}const x=rowKey(a),y=rowKey(b);return x<y?-1:x>y?1:0});
  const counts=new Map<GridValue,number>();if(group)for(const row of result){const v=group(row);counts.set(v,(counts.get(v)??0)+1)}
  return {rows:result,groups:[...counts].map(([value,count])=>({value,count}))};
}
export function pageWindow(total:number,page:number,size:number){if(!Number.isSafeInteger(total)||total<0||!Number.isSafeInteger(page)||!Number.isSafeInteger(size)||size<1)throw Error('Invalid page');const pages=Math.max(1,Math.ceil(total/size));const index=Math.min(pages-1,Math.max(0,page));return {page:index,pages,start:index*size,end:Math.min(total,(index+1)*size)}}
export function virtualWindow(total:number,scrollTop:number,viewport:number,rowHeight:number,overscan=3){if(!Number.isSafeInteger(total)||total<0||![scrollTop,viewport,rowHeight].every(Number.isFinite)||viewport<0||rowHeight<=0||!Number.isSafeInteger(overscan)||overscan<0||!Number.isFinite(total*rowHeight))throw Error('Invalid viewport');const top=Math.min(Math.max(0,total*rowHeight-viewport),Math.max(0,scrollTop));const start=Math.max(0,Math.floor(top/rowHeight)-overscan),end=Math.min(total,Math.ceil((top+viewport)/rowHeight)+overscan);return {start,end,before:start*rowHeight,after:(total-end)*rowHeight}}
export function selectRows(previous:ReadonlySet<string>,ids:readonly string[],checked:boolean){const next=new Set(previous);for(const id of ids)checked?next.add(id):next.delete(id);return next}
