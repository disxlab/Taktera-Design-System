/** UTC instants; half-open [start,end). Backend must recheck conflicts atomically. */
export type Booking={id:string;resourceId:string;additionalResourceIds?:readonly string[];start:string;end:string;version:string;status:'held'|'confirmed'|'cancelled'};
export type Interval={start:number;end:number};
export function instant(value:string):number{
 if(!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?(?:Z|[+-]\d{2}:\d{2})$/.test(value))throw Error('Explicit ISO offset required');
 const time=Date.parse(value);if(!Number.isFinite(time))throw Error('Invalid instant');
 const [y,m,d]=value.slice(0,10).split('-').map(Number);const day=new Date(0);day.setUTCFullYear(y,m-1,d);if(day.getUTCFullYear()!==y||day.getUTCMonth()!==m-1||day.getUTCDate()!==d||Number(value.slice(11,13))>23||Number(value.slice(14,16))>59||Number(value.slice(17,19))>59)throw Error('Invalid calendar date');
 return time;
}
export function interval(start:string,end:string):Interval{const a=instant(start),b=instant(end);if(a>=b)throw Error('End must follow start');return {start:a,end:b}}
export function overlaps(a:Interval,b:Interval){return a.start<b.end&&b.start<a.end}
export function conflicts(candidate:Booking,bookings:readonly Booking[]):Booking[]{
 const span=interval(candidate.start,candidate.end);if(!candidate.id||!candidate.resourceId||!candidate.version)throw Error('Missing booking identity');
 if(candidate.status==='cancelled')return [];
 return bookings.filter(b=>b.id!==candidate.id&&resourceIds(b).some(id=>resourceIds(candidate).includes(id))&&b.status!=='cancelled'&&overlaps(span,interval(b.start,b.end)));
}
export function formatSlot(booking:Booking,timeZone:string,locale:'ru-RU'|'en-US'='ru-RU'){
 interval(booking.start,booking.end);const fmt=new Intl.DateTimeFormat(locale,{timeZone,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',timeZoneName:'shortOffset'});return {start:fmt.format(instant(booking.start)),end:fmt.format(instant(booking.end))};
}

/** Civil calendar arithmetic is independent of the browser's local timezone. Supported dates: 2000–2099. */
const DAY=86400000;
function civilEpoch(date:string){if(!/^20\d\d-\d\d-\d\d$/.test(date))throw Error('Unsupported civil date');return instant(date+'T00:00:00Z')}
export function addCivilDays(date:string,count:number){if(!Number.isSafeInteger(count))throw Error('Invalid day count');const result=new Date(civilEpoch(date)+count*DAY).toISOString().slice(0,10);civilEpoch(result);return result}
const formatters=new Map<string,Intl.DateTimeFormat>();
function partsAt(ms:number,zone:string){let f=formatters.get(zone);if(!f){f=new Intl.DateTimeFormat('en-CA',{timeZone:zone,calendar:'gregory',numberingSystem:'latn',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'});if(formatters.size>=32)formatters.clear();formatters.set(zone,f)}const p=Object.fromEntries(f.formatToParts(ms).map(x=>[x.type,x.value]));return {date:p.year+'-'+p.month+'-'+p.day,time:p.hour+':'+p.minute,seconds:p.second}}
export function localMinute(ms:number,zone:string){const p=partsAt(ms,zone);return p.date+'T'+p.time}
export function localCandidates(value:string,zone:string):number[]{
 if(!/^20\d\d-\d\d-\d\dT\d\d:\d\d$/.test(value))throw Error('Invalid local minute');
 const naive=instant(value+':00Z');const offsets=new Set<number>();
 for(let delta=-36;delta<=36;delta+=6){const sample=naive+delta*3600000,p=partsAt(sample,zone);offsets.add(instant(p.date+'T'+p.time+':'+p.seconds+'Z')-sample)}
 return [...offsets].map(o=>naive-o).filter(ms=>localMinute(ms,zone)===value).sort((a,b)=>a-b);
}
export function resolveLocal(value:string,zone:string,fold:'earlier'|'later'|'reject'='reject'):string{
 const matches=localCandidates(value,zone);
 if(!matches.length)throw Error('Nonexistent local time');
 if(matches.length>1&&fold==='reject')throw Error('Ambiguous local time');
 return new Date(fold==='later'?matches[matches.length-1]:matches[0]).toISOString();
}
/** Lower bound of civil day. Search a bounded UTC interval; skipped dates have zero duration. */
function dayBoundary(date:string,zone:string){const t=civilEpoch(date);let lo=t-2*DAY,hi=t+2*DAY;while(lo<hi){const mid=Math.floor((lo+hi)/2);if(partsAt(mid,zone).date<date)lo=mid+1;else hi=mid}return lo}
export type CalendarDay={date:string;start:number;end:number};
export function calendarDays(date:string,mode:'day'|'week',zone:string):CalendarDay[]{
 const t=civilEpoch(date),weekday=(new Date(t).getUTCDay()+6)%7;
 const first=mode==='week'?addCivilDays(date,-weekday):date;
 return Array.from({length:mode==='week'?7:1},(_,i)=>{const d=addCivilDays(first,i);return {date:d,start:dayBoundary(d,zone),end:dayBoundary(addCivilDays(d,1),zone)}});
}
export function bookingsForDay<T extends Booking>(rows:readonly T[],resourceId:string,day:CalendarDay):T[]{
 if(day.start===day.end)return [];
 return rows.filter(b=>resourceIds(b).includes(resourceId)&&b.status!=='cancelled'&&overlaps(interval(b.start,b.end),day)).sort((a,b)=>instant(a.start)-instant(b.start)||(a.id<b.id?-1:a.id>b.id?1:0));
}
export type SchedulerResource={id:string;label:string;schedule?:WorkingSchedule};
export type SchedulerBooking=Booking&{title:string;seriesId?:string};
export type SchedulerDraft={resourceId:string;additionalResourceIds?:readonly string[];title:string;start:string;end:string};
export type SchedulerMutation=
 |{kind:'create';draft:SchedulerDraft;idempotencyKey:string}
 |{kind:'create-series';draft:SchedulerDraft;rule:RecurrenceRule;occurrences:readonly SchedulerDraft[];idempotencyKey:string}
 |{kind:'update';id:string;version:string;draft:SchedulerDraft;idempotencyKey:string}
 |{kind:'cancel';id:string;version:string;idempotencyKey:string};
export type SchedulerResult={status:'applied'|'conflict'|'forbidden'|'invalid'};
/** The host commits and refreshes authoritative data; UI never writes optimistically. */
export type SchedulerTransport=(request:SchedulerMutation,signal:AbortSignal)=>Promise<SchedulerResult>;
export function validateDraft(draft:SchedulerDraft,resources:readonly SchedulerResource[],bookings:readonly SchedulerBooking[],editingId?:string){
 const ids=resourceIds(draft);
 if(!draft.title.trim()||new Set(ids).size!==ids.length||ids.some(id=>!resources.some(r=>r.id===id)))throw Error('Valid unique resources and title required');
 const span=interval(draft.start,draft.end);
 if(span.end-span.start>31*DAY)throw Error('Booking longer than 31 days');
 if(ids.some(id=>!isWorking(resources.find(r=>r.id===id)!,span)))throw Error('Outside working hours');
 return bookings.filter(b=>b.id!==editingId&&resourceIds(b).some(id=>ids.includes(id))&&b.status!=='cancelled'&&overlaps(span,interval(b.start,b.end)));
}

/** Stable time label distinguishes repeated wall-clock hours, without locale-dependent SSR punctuation. */
export function zonedMinuteLabel(ms:number,zone:string){const p=partsAt(ms,zone);const offset=(instant(p.date+'T'+p.time+':'+p.seconds+'Z')-Math.floor(ms/1000)*1000)/60000;const sign=offset<0?'-':'+';const minutes=Math.abs(Math.round(offset));return p.date+' '+p.time+' UTC'+sign+String(Math.floor(minutes/60)).padStart(2,'0')+':'+String(minutes%60).padStart(2,'0')}
/** Keep exact original instant when a minute-resolution editor did not change the endpoint. */
export function resolveEditedLocal(value:string,zone:string,fold:'earlier'|'later'|'reject',original?:string){const resolved=resolveLocal(value,zone,fold);if(original){const before=instant(original);if(Math.floor(before/60000)===Math.floor(instant(resolved)/60000))return new Date(before).toISOString()}return resolved}

export function resourceIds(row:{resourceId:string;additionalResourceIds?:readonly string[]}){return [row.resourceId,...(row.additionalResourceIds??[])]}
export type WorkWindow={start:string;end:string};
export type WorkingSchedule={timeZone:string;weekly:Readonly<Partial<Record<0|1|2|3|4|5|6,readonly WorkWindow[]>>>;exceptions?:Readonly<Record<string,readonly WorkWindow[]>>};
function workEndpoint(date:string,time:string,zone:string,fold:'earlier'|'later'){
 if(time==='24:00')return instant(resolveLocal(addCivilDays(date,1)+'T00:00',zone,fold));
 if(!/^([01]\d|2[0-3]):[0-5]\d$/.test(time))throw Error('Invalid working time');
 return instant(resolveLocal(date+'T'+time,zone,fold));
}
export function workingIntervals(resource:SchedulerResource,span:Interval):Interval[]{
 if(!resource.schedule)return span.start<span.end?[span]:[];
 const schedule=resource.schedule;if(span.start>=span.end||span.end-span.start>32*DAY)return [];
 const first=localMinute(span.start,schedule.timeZone).slice(0,10),last=localMinute(span.end-1,schedule.timeZone).slice(0,10);
 const windows:Interval[]=[];
 for(let date=first,n=0;n<35&&date<=last;date=addCivilDays(date,1),n++){
  const weekday=new Date(civilEpoch(date)).getUTCDay() as 0|1|2|3|4|5|6;
  const entries=schedule.exceptions?.[date]??schedule.weekly[weekday]??[];
  for(const w of entries){if(w.start==='24:00'||w.start>=w.end)throw Error('Invalid working window; split overnight at midnight');
   const start=workEndpoint(date,w.start,schedule.timeZone,'earlier'),end=workEndpoint(date,w.end,schedule.timeZone,'later');
   if(start>=end)throw Error('Invalid working interval');
   const a=Math.max(start,span.start),b=Math.min(end,span.end);if(a<b)windows.push({start:a,end:b});
  }
 }
 windows.sort((a,b)=>a.start-b.start);const merged:Interval[]=[];
 for(const w of windows){const prev=merged.at(-1);if(prev&&w.start<=prev.end)prev.end=Math.max(prev.end,w.end);else merged.push({...w})}
 return merged;
}
export function isWorking(resource:SchedulerResource,span:Interval){return workingIntervals(resource,span).some(w=>w.start<=span.start&&w.end>=span.end)}
export type RecurrenceRule={frequency:'daily'|'weekly';count:number;timeZone:string;excludeDates?:readonly string[];startFold?:'earlier'|'later'|'reject';endFold?:'earlier'|'later'|'reject'};
export function expandRecurrence(draft:SchedulerDraft,rule:RecurrenceRule):SchedulerDraft[]{
 if(!Number.isSafeInteger(rule.count)||rule.count<2||rule.count>52||!['daily','weekly'].includes(rule.frequency))throw Error('Invalid recurrence');
 const start=instant(draft.start),end=instant(draft.end);interval(draft.start,draft.end);
 if(start%60000||end%60000)throw Error('Recurrence requires minute precision');
 const a=localMinute(start,rule.timeZone),b=localMinute(end,rule.timeZone),excluded=new Set(rule.excludeDates??[]);
 if(excluded.size!==(rule.excludeDates??[]).length)throw Error('Duplicate exclusions');
 for(const x of excluded)civilEpoch(x);
 const result:SchedulerDraft[]=[],seen=new Set<string>();
 for(let i=0;i<rule.count;i++){const delta=i*(rule.frequency==='weekly'?7:1),date=addCivilDays(a.slice(0,10),delta);seen.add(date);if(excluded.has(date))continue;
  const next={...draft,start:i===0?draft.start:resolveLocal(date+a.slice(10),rule.timeZone,rule.startFold),end:i===0?draft.end:resolveLocal(addCivilDays(b.slice(0,10),delta)+b.slice(10),rule.timeZone,rule.endFold)};
  interval(next.start,next.end);result.push(next);
 }
 if(!result.length||[...excluded].some(d=>!seen.has(d)))throw Error('Invalid recurrence exclusions');
 return result;
}
export function validateSeries(drafts:readonly SchedulerDraft[],resources:readonly SchedulerResource[],bookings:readonly SchedulerBooking[]){
 if(!drafts.length||drafts.length>52)throw Error('Invalid series size');
 const accepted:SchedulerBooking[]=[];
 for(let i=0;i<drafts.length;i++){const d=drafts[i];if(validateDraft(d,resources,[...bookings,...accepted]).length)throw Error('Series conflict');accepted.push({...d,id:'series-validation-'+i,version:'preview',status:'confirmed'})}
}
export function timelinePosition(span:Interval,day:CalendarDay){const start=Math.max(span.start,day.start),end=Math.min(span.end,day.end);if(end<=start||day.end<=day.start)return null;return {left:100*(start-day.start)/(day.end-day.start),width:100*(end-start)/(day.end-day.start)}}
export function moveBooking(booking:SchedulerBooking,from:string,to:string,start:number):SchedulerDraft{
 const ids=resourceIds(booking);if(!ids.includes(from)||!to||!Number.isFinite(start)||start%60000||instant(booking.start)%60000||instant(booking.end)%60000)throw Error('Invalid move; use editor for second-precision bookings');
 const next=ids.map(id=>id===from?to:id);if(new Set(next).size!==next.length)throw Error('Duplicate resource');
 return {resourceId:next[0],additionalResourceIds:next.slice(1),title:booking.title,start:new Date(start).toISOString(),end:new Date(start+instant(booking.end)-instant(booking.start)).toISOString()};
}
export function dropInstant(day:CalendarDay,fraction:number,stepMinutes=15){
 if(!Number.isFinite(fraction)||day.end<=day.start||!Number.isSafeInteger(stepMinutes)||stepMinutes<1)throw Error('Invalid drop');
 const step=stepMinutes*60000;const slots=Math.ceil((day.end-day.start)/step);
 return day.start+Math.min(slots-1,Math.max(0,Math.round(fraction*(day.end-day.start)/step)))*step;
}
