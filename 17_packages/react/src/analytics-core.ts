import type {UiLocale} from './crm-core.js';
export type DailyMetric={date:string;revenueMinor:number;visits:number;completed:number;capacity:number;used:number};
export type KpiTotals={revenueMinor:number;visits:number;completed:number;capacity:number;used:number;completionRate:number|null;utilization:number|null;averageMinor:number|null};
export function aggregateMetrics(rows:readonly DailyMetric[]):KpiTotals{
 const sum={revenueMinor:0,visits:0,completed:0,capacity:0,used:0};const dates=new Set<string>();
 for(const r of rows){if(!/^\d{4}-\d\d-\d\d$/.test(r.date)||Number.isNaN(Date.parse(r.date+'T00:00:00Z'))||new Date(r.date+'T00:00:00Z').toISOString().slice(0,10)!==r.date||dates.has(r.date))throw Error('Invalid or duplicate date');dates.add(r.date);
 for(const k of Object.keys(sum) as (keyof typeof sum)[]){if(!Number.isSafeInteger(r[k])||r[k]<0||!Number.isSafeInteger(sum[k]+r[k]))throw Error('Invalid metric');sum[k]+=r[k]}
 if(r.completed>r.visits||r.used>r.capacity)throw Error('Invalid numerator');
 }
 return {...sum,completionRate:sum.visits?sum.completed/sum.visits:null,utilization:sum.capacity?sum.used/sum.capacity:null,averageMinor:sum.completed?sum.revenueMinor/sum.completed:null}
}
export function metricDelta(current:number|null,previous:number|null){return current===null||previous===null||previous===0?null:(current-previous)/Math.abs(previous)}
export function formatMetric(value:number|null,locale:UiLocale,kind:'count'|'ratio'|'money',currency:'RUB'|'USD'|'EUR'='RUB'){if(value===null)return '—';return new Intl.NumberFormat(locale,kind==='money'?{style:'currency',currency}:kind==='ratio'?{style:'percent',maximumFractionDigits:1}:{maximumFractionDigits:0}).format(kind==='money'?value/100:value)}

export type MetricKey='revenueMinor'|'visits'|'completionRate'|'utilization'|'averageMinor';
export const metricKeys:readonly MetricKey[]=['revenueMinor','visits','completionRate','utilization','averageMinor'];
export type Period={start:string;end:string};
const DAY=86400000;
function dateEpoch(date:string){if(!/^\d{4}-\d\d-\d\d$/.test(date))throw Error('Invalid date');const n=Date.parse(date+'T00:00:00Z');if(!Number.isFinite(n)||new Date(n).toISOString().slice(0,10)!==date)throw Error('Invalid date');return n}
function isoDate(n:number){const d=new Date(n).toISOString().slice(0,10);dateEpoch(d);return d}
export function periodLength(p:Period){const n=(dateEpoch(p.end)-dateEpoch(p.start))/DAY+1;if(n<1||n>366)throw Error('Period must be 1–366 days');return n}
export function previousPeriod(p:Period):Period{const n=periodLength(p),start=dateEpoch(p.start);return {start:isoDate(start-n*DAY),end:isoDate(start-DAY)}}
export function periodMetrics(rows:readonly DailyMetric[],period:Period){aggregateMetrics(rows);const days=periodLength(period),selected=rows.filter(r=>r.date>=period.start&&r.date<=period.end).sort((a,b)=>a.date.localeCompare(b.date));return {rows:selected,days,complete:selected.length===days,totals:aggregateMetrics(selected)}}
export function metricValue(totals:KpiTotals,key:MetricKey,complete:boolean):number|null{return complete?totals[key]:null}
export type KpiTarget={metric:MetricKey;value:number;direction:'atLeast'|'atMost'};
export function targetStatus(actual:number|null,target:KpiTarget){if(!metricKeys.includes(target.metric)||!Number.isFinite(target.value)||target.value<0||!['atLeast','atMost'].includes(target.direction)||(['completionRate','utilization'].includes(target.metric)&&target.value>1))throw Error('Invalid KPI target');return actual===null?'unavailable':(target.direction==='atLeast'?actual>=target.value:actual<=target.value)?'met':'missed'}
export function normalizeMetricLayout(input:readonly string[]):MetricKey[]{return [...new Set(input.filter((x):x is MetricKey=>metricKeys.includes(x as MetricKey)))]}
export function shiftMetric(layout:readonly MetricKey[],key:MetricKey,offset:-1|1){const next=[...layout],i=next.indexOf(key),j=i+offset;if(i>=0&&j>=0&&j<next.length)[next[i],next[j]]=[next[j],next[i]];return next}
/** Only validated dates and numbers enter CSV; no arbitrary spreadsheet formulas. */
export function metricsCsv(rows:readonly DailyMetric[],currency:'RUB'|'USD'|'EUR'){aggregateMetrics(rows);if(!['RUB','USD','EUR'].includes(currency))throw Error('Invalid currency');return ['date,currency,revenue_minor,visits,completed,capacity,used',...[...rows].sort((a,b)=>a.date.localeCompare(b.date)).map(r=>[r.date,currency,r.revenueMinor,r.visits,r.completed,r.capacity,r.used].join(','))].join('\r\n')+'\r\n'}
/** Consecutive points only; missing dates break lines instead of implying continuity. */
export function consecutiveSegments(rows:readonly DailyMetric[]){aggregateMetrics(rows);const groups:DailyMetric[][]=[];for(const row of [...rows].sort((a,b)=>a.date.localeCompare(b.date))){const last=groups.at(-1);if(last&&dateEpoch(row.date)-dateEpoch(last.at(-1)!.date)===DAY)last.push(row);else groups.push([row])}return groups}
