import * as React from 'react';
import { hydrateRoot } from 'react-dom/client';
import { Fixture } from './react-fixture';
import type { Product, Theme } from '../src/index';
const root=document.getElementById('root')!;
hydrateRoot(root,<Fixture product={root.dataset.product as Product} theme={root.dataset.theme as Theme}/>,{onRecoverableError:error=>console.error('HYDRATION_RECOVERABLE',error)});
