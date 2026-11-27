import * as React from 'react';
import {hydrateRoot} from 'react-dom/client';
import {App} from './App.js';
import {setTheme,button} from '@taktera/ui-core';
hydrateRoot(document.getElementById('root')!,<App/>,{onRecoverableError:e=>console.error('HYDRATION_RECOVERABLE',e)});
const core=document.getElementById('web-core')!;
setTheme(core,{product:'platform',theme:'light'});
core.append(button({label:'Web Core action',onClick:()=>{core.dataset.clicked='yes'}}));
