import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import {createRequire} from 'node:module';
import {createElement} from 'react';
import {renderToString} from 'react-dom/server';
import {build} from 'esbuild';
import {App} from './dist/App.js';
const require=createRequire(import.meta.url);
const bundle=await build({entryPoints:['client.tsx'],bundle:true,write:false,format:'iife',platform:'browser',jsx:'automatic',define:{'process.env.NODE_ENV':'"development"'}});
const assets={
 '/app.js':['text/javascript',bundle.outputFiles[0].contents],
 '/react.css':['text/css',await readFile(require.resolve('@taktera/ui-react/styles.css'))],
 '/web.css':['text/css',await readFile(require.resolve('@taktera/ui-core/styles.css'))],
 '/':['text/html; charset=utf-8','<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Taktera starter</title><link rel="stylesheet" href="/web.css"><link rel="stylesheet" href="/react.css"></head><body><div id="root">'+renderToString(createElement(App))+'</div><div id="web-core" class="tku-root"></div><script src="/app.js" defer></script></body></html>']
};
const server=createServer((req,res)=>{const item=Object.hasOwn(assets,req.url)&&assets[req.url];if(req.method!=='GET'||!item){res.writeHead(404).end();return}res.writeHead(200,{'Content-Type':item[0]}).end(item[1])});
server.listen(Number(process.env.PORT||4173),'127.0.0.1',()=>console.log('Taktera starter: http://127.0.0.1:'+server.address().port));
