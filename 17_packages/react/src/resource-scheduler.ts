/** UTC instants; half-open [start,end). Backend must recheck conflicts atomically. */
export type Booking={id:string;resourceId:string;start:string;end:string;version:string;status:'held'|'confirmed'|'cancelled'};
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
 return bookings.filter(b=>b.id!==candidate.id&&b.resourceId===candidate.resourceId&&b.status!=='cancelled'&&overlaps(span,interval(b.start,b.end)));
}
export function formatSlot(booking:Booking,timeZone:string,locale:'ru-RU'|'en-US'='ru-RU'){
 interval(booking.start,booking.end);const fmt=new Intl.DateTimeFormat(locale,{timeZone,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',timeZoneName:'shortOffset'});return {start:fmt.format(instant(booking.start)),end:fmt.format(instant(booking.end))};
}

/** Civil calendar arithmetic is independent of the browser's local timezone. Supported dates: 2000–2099. */
const DAY=86400000;
function civilEpoch(date:string){if(!/^20\d\d-\d\d-\d\d$/.test(date))throw Error('Unsupported civil date');return instant(date+'T00:00:00Z')}
export function addCivilDays(date:string,count:number){if(!Number.isSafeInteger(count))throw Error('Invalid day count');const result=new Date(civilEpoch(date)+count*DAY).toISOString().slice(0,10);civilEpoch(result);return result}
function partsAt(ms:number,zone:string){const f=new Intl.DateTimeFormat('en-CA',{timeZone:zone,calendar:'gregory',numberingSystem:'latn',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'});const p=Object.fromEntries(f.formatToParts(ms).map(x=>[x.type,x.value]));return {date:p.year+'-'+p.month+'-'+p.day,time:p.hour+':'+p.minute,seconds:p.second}}
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
 return rows.filter(b=>b.resourceId===resourceId&&b.status!=='cancelled'&&overlaps(interval(b.start,b.end),day)).sort((a,b)=>instant(a.start)-instant(b.start)||(a.id<b.id?-1:a.id>b.id?1:0));
}
export type SchedulerResource={id:string;label:string};
export type SchedulerBooking=Booking&{title:string};
export type SchedulerDraft={resourceId:string;title:string;start:string;end:string};
export type SchedulerMutation=
 |{kind:'create';draft:SchedulerDraft;idempotencyKey:string}
 |{kind:'update';id:string;version:string;draft:SchedulerDraft;idempotencyKey:string}
 |{kind:'cancel';id:string;version:string;idempotencyKey:string};
export type SchedulerResult={status:'applied'|'conflict'|'forbidden'|'invalid'};
/** The host commits and refreshes authoritative data; UI never writes optimistically. */
export type SchedulerTransport=(request:SchedulerMutation,signal:AbortSignal)=>Promise<SchedulerResult>;
export function validateDraft(draft:SchedulerDraft,resources:readonly SchedulerResource[],bookings:readonly SchedulerBooking[],editingId?:string){
 if(!resources.some(r=>r.id===draft.resourceId)||!draft.title.trim())throw Error('Resource and title required');
 const span=interval(draft.start,draft.end);
 return bookings.filter(b=>b.id!==editingId&&b.resourceId===draft.resourceId&&b.status!=='cancelled'&&overlaps(span,interval(b.start,b.end)));
}
