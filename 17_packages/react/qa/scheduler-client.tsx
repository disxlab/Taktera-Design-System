import * as React from 'react';
import {hydrateRoot} from 'react-dom/client';
import {SchedulerFixture} from './scheduler-fixture.js';
import type {Product,Theme} from '../src/index.js';
const root=document.getElementById('root')!;
hydrateRoot(root,<SchedulerFixture product={root.dataset.product as Product} theme={root.dataset.theme as Theme} locale={root.dataset.locale as 'ru-RU'|'en-US'}/>,{onRecoverableError:e=>console.error('HYDRATION_RECOVERABLE',e)});
