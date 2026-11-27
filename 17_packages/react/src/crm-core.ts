import {instant,zonedMinuteLabel} from './resource-scheduler.js';
export type UiLocale='ru-RU'|'en-US';
export type CustomerSummary={id:string;version:string;displayName:string;status:string;contacts:readonly {id:string;label:string;value:string}[];facts?:readonly {id:string;label:string;value:string}[]};
export type ActivityItem={id:string;at:string;kind:string;title:string;description?:string};
export type CenterNotice={id:string;at:string;title:string;description?:string;read:boolean;kind?:'info'|'success'|'warning'|'error'};
export function chronological<T extends {id:string;at:string}>(rows:readonly T[]):T[]{return [...rows].sort((a,b)=>instant(b.at)-instant(a.at)||(a.id<b.id?-1:a.id>b.id?1:0))}
export function timeLabel(at:string,zone:string){return zonedMinuteLabel(instant(at),zone)}
export type FormValue=string|boolean;
export type FormValues=Readonly<Record<string,FormValue>>;
export type FormField={id:string;label:string;kind:'text'|'email'|'select'|'checkbox';required?:boolean;maxLength?:number;options?:readonly {value:string;label:string}[];when?:{field:string;equals:FormValue}};
export type FormStep={id:string;label:string;fields:readonly FormField[]};
export function validateSchema(steps:readonly FormStep[]){
 if(!steps.length)throw Error('Form requires steps');
 const ids=new Set<string>(),stepIds=new Set<string>();
 for(const step of steps){if(!step.id||stepIds.has(step.id))throw Error('Duplicate step');stepIds.add(step.id);
  for(const f of step.fields){if(!/^[A-Za-z][A-Za-z0-9_-]*$/.test(f.id)||['constructor','prototype'].includes(f.id)||ids.has(f.id)||!f.label)throw Error('Invalid field ID');if(f.when&&!ids.has(f.when.field))throw Error('Dependency must precede field');if(f.kind==='select'&&(!f.options?.length||new Set(f.options.map(o=>o.value)).size!==f.options.length||f.options.some(o=>!o.value)))throw Error('Invalid select');ids.add(f.id)}
 }
}
export function activeFields(steps:readonly FormStep[],values:FormValues){validateSchema(steps);const active=new Set<string>();return steps.flatMap(s=>s.fields).filter(f=>{const yes=!f.when||active.has(f.when.field)&&values[f.when.field]===f.when.equals;if(yes)active.add(f.id);return yes})}
export function formPayload(steps:readonly FormStep[],values:FormValues):Record<string,FormValue>{return Object.fromEntries(activeFields(steps,values).map(f=>[f.id,values[f.id]??(f.kind==='checkbox'?false:'')]))}
export type FieldError='required'|'invalid'|'tooLong';
export function formErrors(steps:readonly FormStep[],values:FormValues,stepId?:string):Record<string,FieldError>{
 const active=activeFields(steps,values);const filter=stepId?new Set(steps.find(s=>s.id===stepId)?.fields.map(f=>f.id)??[]):null;
 const result:Record<string,FieldError>={};
 for(const f of active){if(filter&&!filter.has(f.id))continue;const v=values[f.id]??(f.kind==='checkbox'?false:'');
  if(f.kind==='checkbox'){if(typeof v!=='boolean')result[f.id]='invalid';else if(f.required&&!v)result[f.id]='required';continue}
  if(typeof v!=='string'){result[f.id]='invalid';continue}
  const trimmed=v.trim();if(!trimmed){if(f.required)result[f.id]='required';continue}
  if(f.maxLength!==undefined&&v.length>f.maxLength)result[f.id]='tooLong';
  else if(f.kind==='email'&&!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed))result[f.id]='invalid';
  else if(f.kind==='select'&&!f.options?.some(o=>o.value===v))result[f.id]='invalid';
 }
 return result;
}
export type WorkspaceCommand={id:string;label:string;keywords?:readonly string[];disabled?:boolean};
export function searchCommands(commands:readonly WorkspaceCommand[],query:string,locale:UiLocale='ru-RU'){
 const words=query.trim().toLocaleLowerCase(locale).split(/\s+/).filter(Boolean);return commands.filter(c=>{const hay=[c.label,...(c.keywords??[])].join(' ').toLocaleLowerCase(locale);return words.every(w=>hay.includes(w))})
}

/** Only active known field IDs and whitelisted codes may cross the validation boundary. */
export function filterServerErrors(steps:readonly FormStep[],values:FormValues,errors:Record<string,FieldError>):Record<string,FieldError>{const ids=new Set(activeFields(steps,values).map(f=>f.id));return Object.fromEntries(Object.entries(errors).filter(([id,code])=>ids.has(id)&&['required','invalid','tooLong'].includes(code)))}
