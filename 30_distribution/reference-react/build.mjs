// Compile the typed package-only host and stage its separately typed JS runtime.
import {spawnSync} from 'node:child_process';
import {readFile,copyFile,mkdir} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
const cwd=fileURLToPath(new URL('./',import.meta.url));
const tsc=fileURLToPath(new URL('./node_modules/typescript/bin/tsc',import.meta.url));
const result=spawnSync(process.execPath,[tsc,'-p','tsconfig.json'],{cwd,stdio:'inherit'});
if(result.error)throw result.error;
if(result.status!==0)process.exit(result.status??1);
await mkdir(new URL('./dist/',import.meta.url),{recursive:true});
const source=new URL('./synthetic-transport.mjs',import.meta.url);
const target=new URL('./dist/synthetic-transport.mjs',import.meta.url);
await copyFile(source,target);
assert.deepEqual(await readFile(target),await readFile(source),'Synthetic transport runtime bytes differ');
