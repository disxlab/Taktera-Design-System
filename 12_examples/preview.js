const product = document.getElementById('product');
const theme = document.getElementById('theme');
const logo = document.getElementById('brand-logo');
const allowed = new Set(['platform','clinic','beauty','spa','fitness','travel']);
const names = { platform:'Платформа', clinic:'Клиника', beauty:'Красота', spa:'СПА', fitness:'Фитнес', travel:'Путешествия' };
function update() {
  const p = allowed.has(product.value) ? product.value : 'platform';
  const t = theme.value==='dark'?'dark':'light';
  document.documentElement.dataset.theme=t;
  document.documentElement.dataset.product=p;
  logo.src=`../02_logos/products/ru/svg/${p}-ru-${t}.svg`;
  logo.alt=`Taktera ${names[p]}`;
}
product.addEventListener('change',update);
theme.addEventListener('change',update);
for (const id of ['save','main-action']) {
  document.getElementById(id).addEventListener('click', () => {
    document.getElementById('notification').textContent='Демонстрация: действие выполнено (данные не сохраняются)';
  });
}
update();
