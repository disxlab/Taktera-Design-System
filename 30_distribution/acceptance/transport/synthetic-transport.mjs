// BR8-03 synthetic host fixture; deliberately not an SDK API or real transport.
export function createSyntheticTransport() {
 const entries=new Map([["p1",{id:"p1",name:"Synthetic Alice",version:"1"}],["p2",{id:"p2",name:"Synthetic Bob",version:"1"}]]);
 const completed=new Map(), trace=[];
 let failNext=false;
 const clone=x=>JSON.parse(JSON.stringify(x));
 const read=id=>entries.has(id)?clone(entries.get(id)):null;
 function save(input){
  if(!input||typeof input.id!=="string"||typeof input.version!=="string"||typeof input.requestId!=="string"||!input.requestId.trim()||typeof input.name!=="string")throw Error("Invalid synthetic request");
  const req={id:input.id,version:input.version,requestId:input.requestId,name:input.name};
  const key=JSON.stringify(req);
  const done=completed.get(req.requestId);
  const emit=(result)=>{trace.push({requestId:req.requestId,id:req.id,status:result.status});return clone(result);};
  if(done)return emit(done.key===key?done.result:{status:"request-id-conflict"});
  if(failNext){failNext=false;return emit({status:"unavailable",retryable:true});}
  const current=entries.get(req.id);
  if(!current)return emit({status:"not-found"});
  if(current.version!==req.version)return emit({status:"conflict",current:clone(current)});
  const name=req.name.trim();
  if(!name||name.length>80||/[\u0000-\u001f\u007f]/u.test(name))return emit({status:"validation",fieldErrors:{name:"invalid-name"}});
  const next={id:req.id,name,version:String(Number(current.version)+1)};
  entries.set(req.id,next);
  const result={status:"applied",record:clone(next)};
  completed.set(req.requestId,{key,result:clone(result)});
  return emit(result);
 }
 return Object.freeze({read,save:async input=>save(input),failNext:()=>{failNext=true;},trace:()=>clone(trace)});
}
