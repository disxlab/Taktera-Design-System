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
