/* Taktera i18n formatting utilities. Browser Intl, no dependency. Version 1. */
export const SUPPORTED_LOCALES = Object.freeze(['ru-RU','en-US']);
const assertLocale = l => { if(!SUPPORTED_LOCALES.includes(l)) throw new RangeError('Unsupported locale: '+l); return l; };
const assertDate = x => { const d = x instanceof Date ? new Date(x.getTime()) : typeof x === 'string' && /^\d{4}-\d\d-\d\d$/.test(x) ? new Date(x+'T12:00:00Z') : new Date(x); if(!Number.isFinite(d.getTime())) throw new RangeError('Invalid date'); return d; };
export function formatDate(value, locale='ru-RU', options={}) { return new Intl.DateTimeFormat(assertLocale(locale), {year:'numeric',month:'long',day:'numeric',timeZone:'UTC',...options}).format(assertDate(value)); }
export function formatDateTime(value, locale='ru-RU', options={}) { return new Intl.DateTimeFormat(assertLocale(locale), {dateStyle:'medium',timeStyle:'short',timeZone:'UTC',...options}).format(assertDate(value)); }
export function formatCurrency(amount, currency='RUB', locale='ru-RU', options={}) { if(typeof amount!=='number'||!Number.isFinite(amount)) throw new RangeError('Invalid amount'); return new Intl.NumberFormat(assertLocale(locale),{style:'currency',currency,...options}).format(amount); }
export function formatNumber(amount, locale='ru-RU', options={}) { if(typeof amount!=='number'||!Number.isFinite(amount)) throw new RangeError('Invalid number'); return new Intl.NumberFormat(assertLocale(locale),options).format(amount); }
export function formatPercent(ratio, locale='ru-RU', options={}) { return formatNumber(ratio,locale,{style:'percent',maximumFractionDigits:1,...options}); }
const ruWords={appointment:['запись','записи','записей'],client:['клиент','клиента','клиентов'],task:['задача','задачи','задач']};
const enWords={appointment:['appointment','appointments'],client:['client','clients'],task:['task','tasks']};
export function pluralize(count, key, locale='ru-RU') { assertLocale(locale); if(typeof count!=='number'||!Number.isFinite(count)) throw new RangeError('Invalid count'); const words=locale==='ru-RU'?ruWords[key]:enWords[key];if(!words)throw new RangeError('Unknown plural key'); const n=Math.abs(count); const cat=new Intl.PluralRules(locale).select(n); const i=locale==='ru-RU'?({one:0,few:1,many:2,other:2}[cat]):(cat==='one'?0:1);return `${formatNumber(count,locale)} ${words[i]}`; }
export const translations=Object.freeze({'ru-RU':{search:'Поиск',empty:'Нет данных',save:'Сохранить',cancel:'Отмена',loading:'Загрузка'},'en-US':{search:'Search',empty:'No data',save:'Save',cancel:'Cancel',loading:'Loading'}});
export function t(key,locale='ru-RU'){assertLocale(locale);if(!(key in translations[locale]))throw new RangeError('Unknown translation key');return translations[locale][key];}
