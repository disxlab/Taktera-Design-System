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
