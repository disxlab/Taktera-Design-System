import type {GridQuery,GridGroup} from './advanced-grid.js';
export type RemoteRow<T>={id:string;version:string;data:T};
export type RemoteRequest={query:GridQuery;cursor?:string;limit:number};
export type RemotePage<T>={rows:readonly RemoteRow<T>[];nextCursor?:string;total?:number;groups?:readonly GridGroup[];revision:string};
export type BulkItem={id:string;version:string};
export type BulkRequest={action:string;items:readonly BulkItem[];idempotencyKey:string};
export type BulkResult={id:string;status:'applied'|'conflict'|'forbidden'|'invalid'|'failed';version?:string};
export interface GridTransport<T>{read(request:RemoteRequest,signal:AbortSignal):Promise<RemotePage<T>>;bulk?(request:BulkRequest,signal:AbortSignal):Promise<readonly BulkResult[]>}
export type ReadState<T>={status:'idle'|'loading'|'ready'|'error';page?:RemotePage<T>;error?:unknown};
/** Host supplies authenticated transport. No credentials, scope or mutations are inferred by UI. */
export class RemoteGridController<T>{
 private generation=0; private active?:AbortController; private disposed=false;
 constructor(private transport:GridTransport<T>){}
 async read(request:RemoteRequest,emit:(s:ReadState<T>)=>void):Promise<void>{
  if(this.disposed)throw Error('Disposed controller');
  if(!Number.isSafeInteger(request.limit)||request.limit<1||request.limit>500)throw Error('Invalid page size');
  const generation=++this.generation;this.active?.abort();const abort=new AbortController();this.active=abort;
  emit({status:'loading'});
  try{
   const page=await this.transport.read(request,abort.signal);
   if(this.disposed||generation!==this.generation||abort.signal.aborted)return;
   if(!page.revision||page.rows.length>request.limit||new Set(page.rows.map(r=>r.id)).size!==page.rows.length||page.rows.some(r=>!r.id||!r.version)||page.nextCursor!==undefined&&(!page.nextCursor||page.nextCursor===request.cursor)||page.total!==undefined&&(!Number.isSafeInteger(page.total)||page.total<page.rows.length))throw Error('Invalid remote page');
   emit({status:'ready',page});
  }catch(error){if(!this.disposed&&generation===this.generation&&!abort.signal.aborted)emit({status:'error',error})}
 }
 cancel(){++this.generation;this.active?.abort()}
 dispose(){this.disposed=true;this.cancel()}
}
export function prepareBulk(action:string,items:readonly BulkItem[],idempotencyKey:string,confirmed:boolean):BulkRequest{
 if(!confirmed)throw Error('Explicit confirmation required');
 if(!action.trim()||!idempotencyKey.trim()||!items.length||items.length>500||new Set(items.map(i=>i.id)).size!==items.length||items.some(i=>!i.id||!i.version))throw Error('Invalid bulk request');
 return {action,items:items.map(i=>({...i})),idempotencyKey};
}
export async function executeBulk<T>(transport:GridTransport<T>,request:BulkRequest,signal:AbortSignal):Promise<readonly BulkResult[]>{
 if(!transport.bulk)throw Error('Bulk unsupported');
 if(signal.aborted)throw Error('Bulk aborted before dispatch');
 prepareBulk(request.action,request.items,request.idempotencyKey,true);
 const result=await transport.bulk(request,signal);
 const expected=new Set(request.items.map(i=>i.id));
 if(result.length!==expected.size||new Set(result.map(i=>i.id)).size!==expected.size||result.some(i=>!expected.has(i.id)||!['applied','conflict','forbidden','invalid','failed'].includes(i.status)))throw Error('Invalid bulk response; reconcile with server before retry');
 return result;
}
export function remainingSelection(items:readonly BulkItem[],result:readonly BulkResult[]){const applied=new Set(result.filter(r=>r.status==='applied').map(r=>r.id));return items.filter(i=>!applied.has(i.id))}
