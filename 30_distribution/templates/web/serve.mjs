import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const files={'/':['text/html; charset=utf-8',new URL('./index.html',import.meta.url)],'/app.js':['text/javascript',new URL('./app.js',import.meta.url)],'/core.js':['text/javascript',require.resolve('@taktera/ui-core/script.js')],'/styles.css':['text/css',require.resolve('@taktera/ui-core/styles.css')]};
const server=createServer(async(req,res)=>{const f=Object.hasOwn(files,req.url)&&files[req.url];if(req.method!=='GET'||!f){res.writeHead(404).end();return}try{const body=await readFile(f[1]);res.writeHead(200,{'Content-Type':f[0]}).end(body)}catch{res.writeHead(500).end()}});
server.listen(Number(process.env.PORT||4173),'127.0.0.1',()=>console.log('Taktera Web starter: http://127.0.0.1:'+server.address().port));
