/* Taktera UI Core v4.0 alpha.5 | DOM-first, dependency-free, text-safe. */
(function (global) {
  'use strict';
  const PRODUCTS = Object.freeze(['platform', 'clinic', 'beauty', 'spa', 'fitness', 'travel']);
  const THEMES = Object.freeze(['light', 'dark']);
  let seq = 0;
  const uid = (prefix) => `tku-${prefix}-${++seq}`;
  const LOCALES = Object.freeze({
    ru: Object.freeze({cancel:'Отмена',save:'Сохранить',previous:'Назад',next:'Далее',tablePages:'Страницы таблицы',empty:'Нет записей',of:'из',notifications:'Уведомления',dismiss:'Закрыть уведомление',close:'Закрыть'}),
    en: Object.freeze({cancel:'Cancel',save:'Save',previous:'Previous',next:'Next',tablePages:'Table pages',empty:'No records',of:'of',notifications:'Notifications',dismiss:'Dismiss notification',close:'Dismiss'})
  });
  function labelsFor(locale, labels) {
    if (!Object.prototype.hasOwnProperty.call(LOCALES,locale)) throw new RangeError('Unsupported locale');
    if (labels!==undefined && (!labels || typeof labels!=='object' || Array.isArray(labels))) throw new TypeError('labels must be an object');
    const merged={...LOCALES[locale], ...(labels || {})};
    for(const [key,value] of Object.entries(merged)) if(typeof value!=='string') throw new TypeError(`labels.${key} must be a string`);
    return merged;
  }
  const el = (tag, className = '', text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = String(text);
    return node;
  };
  const contentNode = value => value instanceof Node ? value : document.createTextNode(String(value ?? ''));
  function setTheme(root, { product = 'platform', theme = 'light' } = {}) {
    if (!PRODUCTS.includes(product) || !THEMES.includes(theme)) throw new RangeError('Unknown Taktera product or theme');
    if (!(root instanceof HTMLElement)) throw new TypeError('Theme root must be an HTMLElement');
    root.dataset.product = product; root.dataset.theme = theme;
    return root;
  }
  function button({ label, variant = 'primary', disabled = false, loading = false, onClick, type = 'button' } = {}) {
    if(!['button','submit','reset'].includes(type)) throw new RangeError('Unknown button type');
    if (!['primary', 'secondary', 'ghost', 'danger'].includes(variant)) throw new RangeError('Unknown button variant');
    const node = el('button', `tku-button tku-button--${variant}`, label ?? '');
    node.type = type; node.disabled = Boolean(disabled || loading);
    if (loading) { node.setAttribute('aria-busy', 'true'); node.setAttribute('data-loading', ''); }
    if (typeof onClick === 'function') node.addEventListener('click', onClick);
    return node;
  }
  function field({ label, value = '', placeholder = '', type = 'text', required = false, error = '', onInput, name } = {}) {
    if (!label) throw new TypeError('Field requires a visible label');
    const id = uid('input'), wrap = el('div', 'tku-field'), heading = el('label','tku-field__label',label);
    heading.htmlFor = id;
    const input = el('input','tku-input'); input.id = id; input.type = type; input.value = String(value);
    input.placeholder = placeholder; input.required = Boolean(required);
    if (name) input.name = name;
    const errorNode = el('div','tku-field__error',error); errorNode.id = `${id}-error`;
    errorNode.hidden = !error;
    function setError(message = '') { errorNode.textContent = message; errorNode.hidden = !message;
      if (message) { input.setAttribute('aria-invalid','true'); input.setAttribute('aria-describedby',errorNode.id); }
      else { input.removeAttribute('aria-invalid'); input.removeAttribute('aria-describedby'); }
    }
    if (typeof onInput === 'function') input.addEventListener('input', e => onInput(e.currentTarget.value, e));
    wrap.append(heading,input,errorNode); setError(error);
    return { element: wrap, input, setError };
  }
  function select({ label, options = [], value, onChange, name } = {}) {
    if (!label) throw new TypeError('Select requires a label');
    const id = uid('select'), wrap = el('div','tku-field'), heading = el('label','tku-field__label',label);
    heading.htmlFor=id; const input=el('select','tku-input'); input.id=id; if(name)input.name=name;
    for (const opt of options) { const option = el('option','',opt.label); option.value=String(opt.value);input.append(option); }
    if(value!==undefined)input.value=String(value);
    if(typeof onChange==='function')input.addEventListener('change',e=>onChange(e.currentTarget.value,e));
    wrap.append(heading,input); return {element:wrap,input};
  }
  function checkbox({ label, checked = false, onChange, switchRole = false } = {}) {
    const wrap = el('label','tku-check'), input = el('input'); input.type = 'checkbox'; input.checked = Boolean(checked);
    if(switchRole) input.setAttribute('role','switch');
    const text = el('span','',label ?? '');
    wrap.append(input,text);
    if(typeof onChange === 'function') input.addEventListener('change', e => onChange(e.currentTarget.checked, e));
    return {element:wrap,input};
  }
  function status({tone='info',label='' }={}) {
    if(!['info','success','warning','error'].includes(tone))throw new RangeError('Unknown status');
    return el('span',`tku-status tku-status--${tone}`,label);
  }
  function alert({tone='info',title='',message='' }={}) {
    if(!['info','success','warning','error'].includes(tone))throw new RangeError('Unknown alert tone');
    const wrap=el('section',`tku-alert tku-alert--${tone}`);wrap.setAttribute('role',tone==='error'?'alert':'status');
    if(title)wrap.append(el('strong','',title));wrap.append(el('p','',message));return wrap;
  }
  function card({title='',children=[]}={}) {
    const wrap=el('section','tku-card'); if(title)wrap.append(el('h3','tku-card__title',title));
    for(const child of children)wrap.append(contentNode(child));return wrap;
  }
  function tabs({items,activeId,onChange}={}) {
    if(!Array.isArray(items)||!items.length)throw new TypeError('Tabs require items');
    const shell=el('div','tku-tabs'),list=el('div','tku-tablist');list.setAttribute('role','tablist');
    const panel=el('div','tku-tabpanel');panel.setAttribute('role','tabpanel');panel.tabIndex=0;
    const buttons=[];let selected=items.some(i=>i.id===activeId)?activeId:items[0].id;
    for(const item of items){const tab=el('button','tku-tab',item.label);tab.type='button';tab.id=uid('tab');tab.setAttribute('role','tab');tab.setAttribute('aria-controls',panel.id|| (panel.id=uid('panel')));buttons.push(tab);list.append(tab);tab.addEventListener('click',()=>activate(item.id));}
    function activate(id, focus=false){const index=items.findIndex(i=>i.id===id);if(index<0)return;
      selected=id;buttons.forEach((tab,i)=>{const active=i===index;tab.setAttribute('aria-selected',String(active));tab.tabIndex=active?0:-1;});
      panel.replaceChildren(contentNode(items[index].content??''));panel.setAttribute('aria-labelledby',buttons[index].id);
      if(focus)buttons[index].focus();if(typeof onChange==='function')onChange(id);
    }
    list.addEventListener('keydown',e=>{const i=buttons.indexOf(document.activeElement);if(i<0)return;
      let n;switch(e.key){case 'ArrowRight':n=(i+1)%items.length;break;case 'ArrowLeft':n=(i+items.length-1)%items.length;break;
      case 'Home':n=0;break;case 'End':n=items.length-1;break;default:return;}
      e.preventDefault();activate(items[n].id,true);
    });shell.append(list,panel);activate(selected);return {element:shell,activate,get selected(){return selected;}};
  }
  function dialog({title='',content='',confirmLabel,onConfirm,onClose,locale='ru',labels}={}){
    const lang=labelsFor(locale,labels);
    const node=el('dialog','tku-dialog'),heading=el('h2','tku-dialog__title',title);heading.id=uid('dialog-title');
    node.setAttribute('aria-labelledby',heading.id);
    const body=el('div','tku-dialog__body');body.append(contentNode(content));
    const footer=el('div','tku-dialog__footer');
    const cancel=button({label:lang.cancel,variant:'secondary',onClick:()=>node.close('cancel')});
    const confirm=button({label:confirmLabel??lang.save,onClick:()=>{
      const result=typeof onConfirm==='function'?onConfirm():true;
      if(result!==false)node.close('confirm');
    }});footer.append(cancel,confirm);node.append(heading,body,footer);
    let opener=null;
    node.addEventListener('close',()=>{if(opener?.isConnected)opener.focus();if(typeof onClose==='function')onClose(node.returnValue);});
    return {element:node,open(){opener=document.activeElement instanceof HTMLElement?document.activeElement:null;if(!node.isConnected) throw new Error('Attach the dialog to the DOM before opening');
      if(node.open)return;node.showModal();cancel.focus();},close(){if(node.open)node.close('cancel');}};
  }
  function table({columns,rows=[],rowKey=(row,i)=>String(i),pageSize=5,emptyText,locale='ru',labels}={}) {
    const lang=labelsFor(locale,labels);
    emptyText=emptyText??lang.empty;
    if(!Array.isArray(columns)||!columns.length)throw new TypeError('Columns are required');
    if(!Array.isArray(rows))throw new TypeError('rows must be an array');
    if(!Number.isInteger(pageSize)||pageSize<1)throw new RangeError('pageSize must be a positive integer');
    const shell=el('div','tku-table-shell'),scroll=el('div','tku-table-scroll'),grid=el('table','tku-table');
    const head=el('thead'),headRow=el('tr'),body=el('tbody'),pager=el('nav','tku-pager'),result=el('span','tku-pager__info');
    pager.setAttribute('aria-label',lang.tablePages);result.setAttribute('aria-live','polite');
    const prev=button({label:lang.previous,variant:'secondary'}),next=button({label:lang.next,variant:'secondary'});
    let sortKey=null,sortDirection='asc',page=0,data=[...rows];
    function toggleSort(key){if(sortKey===key)sortDirection=sortDirection==='asc'?'desc':'asc';else{sortKey=key;sortDirection='asc';}page=0;render();}
    for(const col of columns){const th=el('th','');th.scope='col';th.dataset.key=String(col.key);
      if(col.sortable){const b=button({label:col.label,variant:'ghost',onClick:()=>toggleSort(col.key)});th.append(b);}else th.textContent=col.label;
      headRow.append(th);
    }
    head.append(headRow);grid.append(head,body);scroll.append(grid);
    prev.addEventListener('click',()=>{page=Math.max(0,page-1);render();});
    next.addEventListener('click',()=>{page=Math.min(Math.ceil(data.length/pageSize)-1,page+1);render();});
    pager.append(prev,result,next);shell.append(scroll,pager);
    function sorted(){const clone=[...data];if(!sortKey)return clone;
      clone.sort((a,b)=>{const left=a[sortKey],right=b[sortKey];
        if(left==null&&right==null)return 0;if(left==null)return 1;if(right==null)return -1;
        if(typeof left==='number'&&typeof right==='number')return left-right;
        return String(left).localeCompare(String(right),locale,{numeric:true});});
      return sortDirection==='desc'?clone.reverse():clone;
    }
    function render(){body.replaceChildren();const list=sorted();const maxPage=Math.max(0,Math.ceil(list.length/pageSize)-1);page=Math.min(maxPage,page);
      const view=list.slice(page*pageSize,(page+1)*pageSize);
      if(!view.length){const tr=el('tr'),td=el('td','tku-table__empty',emptyText);td.colSpan=columns.length;tr.append(td);body.append(tr);}
      for(const [index,row] of view.entries()){
        const tr=el('tr');tr.dataset.rowKey=String(rowKey(row,page*pageSize+index));
        for(const col of columns){const td=el('td','',row[col.key] ?? '');tr.append(td);}body.append(tr);
      }
      headRow.querySelectorAll('th').forEach(th=>{if(th.dataset.key===sortKey)th.setAttribute('aria-sort',sortDirection==='asc'?'ascending':'descending');else th.removeAttribute('aria-sort');});
      result.textContent=`${list.length ? page*pageSize+1:0}–${Math.min((page+1)*pageSize,list.length)} ${lang.of} ${list.length}`;
      prev.disabled=page===0;next.disabled=page===maxPage;
    }
    render();return{element:shell,setRows(rows){if(!Array.isArray(rows))throw new TypeError('rows must be an array');data=[...rows];page=0;render();},get sort(){return{key:sortKey,direction:sortDirection};}};
  }
  function toastRegion({locale='ru',labels}={}){
    const lang=labelsFor(locale,labels);
    const region=el('div','tku-toasts');region.setAttribute('role','region');region.setAttribute('aria-label',lang.notifications);
    const live=el('div','tku-toasts__live');live.setAttribute('role','status');live.setAttribute('aria-live','polite');region.append(live);
    return{element:region,push(message,tone='info'){
      if(!['info','success','warning','error'].includes(tone))throw new RangeError('Unknown toast tone');
      const notice=el('div',`tku-toast tku-toast--${tone}`),text=el('span','',message),close=button({label:lang.close,variant:'ghost',onClick:()=>notice.remove()});
      close.setAttribute('aria-label',lang.dismiss);notice.append(text,close);region.append(notice);live.textContent=String(message);return notice;
    }};
  }
  global.TakteraUI=Object.freeze({PRODUCTS,THEMES,setTheme,button,field,select,checkbox,status,alert,card,tabs,dialog,table,toastRegion});
})(globalThis);
