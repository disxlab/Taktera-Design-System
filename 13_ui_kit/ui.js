/* Taktera UI alpha: accessible, framework-free preview behavior. No network, storage or CRM integration. */
'use strict';
(() => {
  const $=(id)=>document.getElementById(id);
  const S=window.TAKTERA_SCENARIOS;
  const allowed=Object.keys(S);
  const ico={
    dashboard:'<rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/>',
    calendar:'<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18"/><path d="m9 16 2 2 4-4"/>',
    layers:'<path d="m12 3 9 5-9 5-9-5 9-5Zm-9 9 9 5 9-5M3 16l9 5 9-5"/>',
    book:'<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z"/>',
    sun:'<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M2 12h2m16 0h2M4.93 19.07l1.42-1.42M17.65 6.35l1.42-1.42"/>',
    help:'<circle cx="12" cy="12" r="10"/><path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 2-3 4m.1 4h.01"/>',
    info:'<circle cx="12" cy="12" r="10"/><path d="M12 16v-4m0-4h.01"/>',
    plus:'<path d="M12 5v14M5 12h14"/>',
    filter:'<path d="M4 7h16M7 12h10m-7 5h4"/>',
    search:'<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
    download:'<path d="M12 3v12m-4-4 4 4 4-4M4 17v4h16v-4"/>',
    bell:'<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/>',
    sparkle:'<path d="m12 3 1.6 5.4L19 10l-5.4 1.6L12 17l-1.6-5.4L5 10l5.4-1.6L12 3Zm7 15 .8 2.2L22 21l-2.2.8L19 24l-.8-2.2L16 21l2.2-.8L19 18Z"/>',
    users:'<circle cx="9" cy="8" r="3"/><path d="M3 21v-2a6 6 0 0 1 12 0v2M17 5a3 3 0 0 1 0 6m4 10v-2a6 6 0 0 0-4-5.65"/>',
    chart:'<path d="M3 3v18h18M7 16v-4m5 4V7m5 9V5"/>',
    check:'<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
    refresh:'<path d="M20 7v5h-5M4 17v-5h5"/><path d="M5.6 9A7 7 0 0 1 18 6l2 1M4 17l2 1A7 7 0 0 0 18.4 15"/>',
    clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    activity:'<path d="M2 12h5l3-8 4 16 3-8h5"/>',
    inbox:'<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 13h5l2 3h4l2-3h5"/>',
    x:'<path d="M18 6 6 18M6 6l12 12"/>',
    alert:'<path d="m12 3 10 18H2L12 3Z"/><path d="M12 9v4m0 4h.01"/>',
    sort:'<path d="m8 10 4-4 4 4M8 14l4 4 4-4"/>'
  };
  function icon(name){return `<svg aria-hidden="true" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">${ico[name]||ico.info}</svg>`}
  function esc(value){return String(value).replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
  const statusName={confirmed:'Подтверждено',pending:'Ожидает',progress:'В работе',cancelled:'Отменено'};
  const statusClass={confirmed:'success',pending:'warning',progress:'info',cancelled:'error'};
  const state={product:'clinic',theme:'light',view:'overview',tab:'all',sort:'date',dir:'asc',page:1,rows:{}};
  const PPL=window.TAKTERA_DEMO_PEOPLE;
  for(const p of allowed){
    const c=S[p];state.rows[p]=Array.from({length:12},(_,i)=>({
      id:`TK-${String(i+101).padStart(4,'0')}`,contact:PPL[(i+(allowed.indexOf(p)*2))%PPL.length],
      service:c.services[i%c.services.length],date:`2026-11-${String(22+(i%7)).padStart(2,'0')}`,
      status:['confirmed','confirmed','pending','progress','confirmed','pending','confirmed','progress','pending','confirmed','confirmed','cancelled'][i]
    }));
  }
  function fmt(date){const [y,m,d]=date.split('-');return `${d}.${m}.${y}`}
  function toast(message,type='success'){
    const t=document.createElement('div');t.className='tk4-toast';t.dataset.type=type;
    const span=document.createElement('span');span.textContent=message;const close=document.createElement('button');close.type='button';close.setAttribute('aria-label','Закрыть уведомление');close.textContent='×';close.addEventListener('click',()=>t.remove());t.append(span,close);$('toast-stack').append(t);
    if($('toast-stack').children.length>3)$('toast-stack').firstElementChild.remove();
  }
  function product(){return S[state.product]}
  function setView(view){if(!['overview','records','components','guidelines'].includes(view))return;state.view=view;
    for(const name of ['overview','records','components','guidelines'])$('view-'+name).hidden=(name!==view);
    for(const btn of document.querySelectorAll('[data-view]')){if(!btn.classList.contains('tk4-nav-link'))continue;const active=btn.dataset.view===view;btn.classList.toggle('is-active',active);if(active)btn.setAttribute('aria-current','page');else btn.removeAttribute('aria-current');}
    $('crumb-page').textContent=({overview:'Обзор',records:product().nav,components:'Компоненты UI',guidelines:'Правила'})[view];
    if(view==='records')renderRecords();if(view==='guidelines')renderSwatches();
    document.getElementById('main').focus({preventScroll:true});window.scrollTo({top:0,behavior:'instant'});
  }
  function setTheme(v){state.theme=v==='dark'?'dark':'light';document.documentElement.dataset.theme=state.theme;$('theme-select').value=state.theme;syncLogo()}
  function setProduct(p){if(!allowed.includes(p))return;state.product=p;document.documentElement.dataset.product=p;$('product-select').value=p;syncLogo();renderProduct();setView(state.view)}
  function syncLogo(){$('logo').src=`../02_logos/products/ru/svg/${state.product}-ru-${state.theme}.svg`;$('logo').alt=`Taktera ${product().ru}`}
  function renderProduct(){const c=product();$('crumb-product').textContent=`Taktera ${c.en}`;$('hero-title').textContent=c.title;$('hero-subtitle').textContent=c.subtitle;$('workspace-name').textContent=`Taktera ${c.ru}`;$('records-nav-label').textContent=c.nav;$('records-title').textContent=c.nav+' и задачи';$('new-label').textContent=c.newLabel;$('schedule-title').textContent=c.schedule;$('schedule-caption').textContent=c.scheduleCaption;$('create-service-label').textContent=c.service;$('table-title').textContent='Ближайшие '+c.nav.toLowerCase();$('records-count').textContent=state.rows[state.product].length;
   $('metric-cards').innerHTML=c.metrics.map(([label,value,change,ic])=>`<article class="tk4-metric"><div class="tk4-metric-top"><span class="tk4-metric-label">${esc(label)}</span><span class="tk4-metric-icon">${icon(ic)}</span></div><div class="tk4-metric-value">${esc(value)}</div><div class="tk4-metric-foot"><span class="tk4-metric-change">${esc(change)}</span><span>Пример KPI</span></div></article>`).join('');
   $('schedule-rows').innerHTML=c.resources.map((r,i)=>`<div class="tk4-schedule-row"><span class="tk4-time">${String(9+i*2).padStart(2,'0')}:00</span><div class="tk4-appointment"><div class="tk4-appointment-body"><strong>${esc(c.services[(i+1)%c.services.length])}</strong><small>${esc(r)} · ${esc(PPL[i+1])}</small></div><span class="tk4-appointment-tag">${i===2?'60 мин':'45 мин'}</span></div></div>`).join('');
   $('notes').innerHTML=c.activities.map(([label,desc,ic])=>`<article class="tk4-note"><div class="tk4-note-icon">${icon(ic)}</div><div><strong>${esc(label)}</strong><small>${esc(desc)}</small></div></article>`).join('');
   renderOverview();renderRecords();
  }
  function filteredRows(query,tab='all'){
    const term=query.trim().toLocaleLowerCase('ru-RU');return state.rows[state.product].filter(r=> (tab==='all'||r.status===tab)&&[r.id,r.contact,r.service,r.date,statusName[r.status]].some(x=>x.toLocaleLowerCase('ru-RU').includes(term)));
  }
  function tableMarkup(rows){if(!rows.length)return `<div class="tk4-empty-table">${icon('inbox')}<strong>Записей не найдено</strong><span>Измените запрос или фильтр</span></div>`;
    return `<div class="tk4-table-scroll"><table class="tk4-table"><thead><tr><th scope="col"><button data-sort="id" type="button">Номер ${icon('sort')}</button></th><th scope="col"><button data-sort="contact" type="button">Контакт ${icon('sort')}</button></th><th scope="col">Услуга / задача</th><th scope="col"><button data-sort="date" type="button">Дата ${icon('sort')}</button></th><th scope="col">Статус</th><th scope="col">Действие</th></tr></thead><tbody>${rows.map(r=>`<tr><td>${esc(r.id)}</td><td>${esc(r.contact)}</td><td>${esc(r.service)}</td><td class="tk4-secondary-cell">${fmt(r.date)}</td><td><span class="tk4-status tk4-status-${statusClass[r.status]}">${statusName[r.status]}</span></td><td><button class="tk4-row-action" type="button" data-inspect="${esc(r.id)}">Открыть</button></td></tr>`).join('')}</tbody></table></div>`;
  }
  function renderTable(id,rows){$(id).innerHTML=tableMarkup(rows)}
  function renderOverview(){let rows=filteredRows($('quick-search').value);rows.sort((a,b)=>state.dir*a[state.sort].localeCompare(b[state.sort],'ru'));renderTable('table-container',rows.slice(0,5))}
  function renderRecords(){let rows=filteredRows($('records-search').value,state.tab);rows.sort((a,b)=>{const ax=a[state.sort],bx=b[state.sort];return state.dir*(ax.localeCompare(bx,'ru'));});const pages=Math.max(1,Math.ceil(rows.length/5));state.page=Math.min(pages,Math.max(1,state.page));const begin=(state.page-1)*5;renderTable('records-table',rows.slice(begin,begin+5));$('page-info').textContent=rows.length?`Показано ${begin+1}–${Math.min(begin+5,rows.length)} из ${rows.length}`:'Нет результатов';$('prev-page').disabled=state.page===1;$('next-page').disabled=state.page===pages;
    for(const b of document.querySelectorAll('[role="tab"]')){const sel=b.dataset.tab===state.tab;b.setAttribute('aria-selected',String(sel));b.tabIndex=sel?0:-1;}
  }
  function renderSwatches(){const styles=getComputedStyle(document.documentElement);const names=['accent','canvas','surface','text','border','status-success-text','status-warning-text','status-error-text'];$('swatches').innerHTML=names.map(n=>`<span title="--tk-${n}" class="tk4-swatch" style="background:${styles.getPropertyValue('--tk-'+n).trim()}"></span>`).join('')}
  function showDialog(id){const dlg=$(id);if(typeof dlg.showModal==='function')dlg.showModal();else dlg.setAttribute('open','');if(id==='create-dialog'){$('create-error').hidden=true;$('create-name').removeAttribute('aria-invalid');$('create-form').reset();$('create-date').value='2026-11-23';$('create-name').focus();}}
  function closeDialog(id){const dlg=$(id);if(typeof dlg.close==='function')dlg.close();else dlg.removeAttribute('open')}
  function exportCsv(){const header=['Номер','Контакт','Услуга','Дата','Статус'];const csv=[header,...state.rows[state.product].map(r=>[r.id,r.contact,r.service,r.date,statusName[r.status]])].map(row=>row.map(x=>{const t=String(x);const safe=/^[=+\-@\t\r]/.test(t)?`'${t}`:t;return `"${safe.replaceAll('"','""')}"`}).join(';')).join('\r\n');const blob=new Blob(['\uFEFF'+csv],{type:'text/csv;charset=utf-8'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=`taktera-demo-${state.product}.csv`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);toast('Демонстрационные записи экспортированы в CSV')}
  document.querySelectorAll('[data-icon]').forEach(node=>{node.innerHTML=icon(node.dataset.icon)});
  document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>setView(b.dataset.view)));
  document.querySelectorAll('[data-action="create"]').forEach(b=>b.addEventListener('click',()=>showDialog('create-dialog')));
  document.querySelectorAll('[data-close]').forEach(b=>b.addEventListener('click',()=>closeDialog(b.dataset.close)));
  $('product-select').addEventListener('change',e=>setProduct(e.target.value));$('theme-select').addEventListener('change',e=>setTheme(e.target.value));$('shortcut-theme').addEventListener('click',()=>setTheme(state.theme==='light'?'dark':'light'));
  for(const b of ['shortcut-help','top-info'])$(b).addEventListener('click',()=>toast('Taktera v4.0 alpha: данные вымышлены, никаких реальных записей и запросов нет'));
  $('open-filter').addEventListener('click',()=>setView('records'));
  $('quick-search').addEventListener('input',renderOverview);
  $('records-search').addEventListener('input',()=>{state.page=1;renderRecords()});
  document.querySelectorAll('[role="tab"]').forEach(b=>{b.addEventListener('click',()=>{state.tab=b.dataset.tab;state.page=1;renderRecords()});b.addEventListener('keydown',e=>{if(!['ArrowRight','ArrowLeft','Home','End'].includes(e.key))return;e.preventDefault();const tabs=[...document.querySelectorAll('[role="tab"]')];const i=tabs.indexOf(b);const idx=e.key==='Home'?0:e.key==='End'?tabs.length-1:(i+(e.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;tabs[idx].focus();tabs[idx].click()});});
  $('prev-page').addEventListener('click',()=>{state.page--;renderRecords()});$('next-page').addEventListener('click',()=>{state.page++;renderRecords()});
  document.addEventListener('click',e=>{const sort=e.target.closest('[data-sort]');if(sort){const field=sort.dataset.sort;if(!['id','contact','date'].includes(field))return;if(state.sort===field)state.dir*=-1;else{state.sort=field;state.dir=1}if(state.view==='overview')renderOverview();else renderRecords();}const inspect=e.target.closest('[data-inspect]');if(inspect){toast(`Карточка ${inspect.dataset.inspect}: прототип, открытие CRM не подключено`);}});
  $('download-csv').addEventListener('click',exportCsv);
  $('create-form').addEventListener('submit',e=>{e.preventDefault();const value=$('create-name').value.trim();if(value.length<2){$('create-error').hidden=false;$('create-name').setAttribute('aria-invalid','true');$('create-name').focus();return;}const row={id:`TK-${String(Math.max(100,...state.rows[state.product].map(r=>Number(r.id.replace('TK-',''))||0))+1).padStart(4,'0')}`,contact:value,service:$('create-service').value.trim()||product().services[0],date:$('create-date').value||'2026-11-23',status:$('create-status').value};state.rows[state.product].unshift(row);closeDialog('create-dialog');renderProduct();state.page=1;toast(`Запись ${row.id} создана в памяти демонстрации (не сохранена на сервере)`);});
  $('confirm-yes').addEventListener('click',()=>{closeDialog('confirm-dialog');toast('Действие подтверждено · демонстрация')});
  $('sample-confirm').addEventListener('click',()=>showDialog('confirm-dialog'));
  $('sample-toast').addEventListener('click',()=>toast('Данные обновлены · это демонстрация'));
  $('sample-action').addEventListener('click',()=>toast('Демонстрационная форма сохранена'));
  $('sample-secondary').addEventListener('click',()=>toast('Действие отменено'));
  $('sample-link').addEventListener('click',()=>toast('Смотрите документацию 13_ui_kit'));
  $('guideline-toast').addEventListener('click',()=>toast('Проверка уведомлений успешна'));
  $('sample-loading').addEventListener('click',e=>{const b=e.currentTarget;b.disabled=true;b.setAttribute('aria-busy','true');b.textContent='Выполняется…';setTimeout(()=>{b.disabled=false;b.removeAttribute('aria-busy');b.innerHTML=`${icon('refresh')} Загрузка`;toast('Демонстрационная операция завершена')},650)});
  $('today-date').textContent='22 НОЯБРЯ 2026';$('schedule-date').textContent='22.11.2026';
  renderProduct();setTheme('light');setView('overview');
  window.takteraDemo={state,selectProduct:setProduct,selectTheme:setTheme,setView,toast}; // QA-only surface
})();
