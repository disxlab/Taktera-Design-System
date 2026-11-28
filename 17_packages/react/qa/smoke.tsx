/** Server-render smoke test. Does not replace browser interaction or screen-reader testing. */
import * as React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { strict as assert } from 'node:assert';
import { TakteraProvider, Button, Field, Card, Status, Tabs, DataTable } from '../src/index';
const products=['platform','clinic','beauty','spa','fitness','travel'] as const;
const themes=['light','dark'] as const;
let cases=0;
for(const product of products) for(const theme of themes){
  const html=renderToStaticMarkup(<TakteraProvider product={product} theme={theme}>
    <Card title="Пилот"><Field label="Клиент" defaultValue="Тест"/><Button>Сохранить</Button><Status tone="success">OK</Status></Card>
  </TakteraProvider>);
  assert.match(html,new RegExp(`data-product="${product}"`));
  assert.match(html,new RegExp(`data-theme="${theme}"`));
  assert.match(html,/tku-button/);assert.match(html,/<label/);cases++;
}
const escaped=renderToStaticMarkup(<DataTable columns={[{key:'name',label:'Название'}]} rows={[{name:'<script>alert(1)</script>'}]} rowKey={r=>r.name}/>);
assert(!escaped.includes('<script>'));assert(escaped.includes('&lt;script&gt;'));cases++;
const tabs=renderToStaticMarkup(<Tabs items={[{id:'first',label:'Основное',panel:<p>Контент</p>}]}/>);
assert(tabs.includes('role="tablist"') && tabs.includes('role="tabpanel"'));cases++;
console.log(`React SSR smoke: ${cases}/${cases} PASS (no hydration/browser checks)`);
