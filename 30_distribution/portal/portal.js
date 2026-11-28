'use strict';
const main=document.querySelector('main'),search=document.getElementById('search'),cards=[...document.querySelectorAll('[data-doc]')],count=document.getElementById('count'),theme=document.getElementById('theme');
function filter(){const words=search.value.toLowerCase().trim().split(/\s+/).filter(Boolean);let shown=0;for(const card of cards){card.hidden=!words.every(w=>card.textContent.toLowerCase().includes(w));if(!card.hidden)shown++}count.textContent=shown+' of '+cards.length+' documentation sections'}
search.addEventListener('input',filter);theme.addEventListener('click',()=>{const dark=main.dataset.theme!=='dark';main.dataset.theme=dark?'dark':'light';theme.setAttribute('aria-pressed',String(dark))});filter();
