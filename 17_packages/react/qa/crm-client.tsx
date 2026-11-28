import * as React from 'react';
import {hydrateRoot} from 'react-dom/client';
import {CrmFixture} from './crm-fixture.js';
import type {Product,Theme} from '../src/index.js';
const root=document.getElementById('root')!;
hydrateRoot(root,<CrmFixture product={root.dataset.product as Product} theme={root.dataset.theme as Theme} locale={root.dataset.locale as 'ru-RU'|'en-US'}/>,{onRecoverableError:e=>console.error('HYDRATION_RECOVERABLE',e)});
