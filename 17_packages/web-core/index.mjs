/* ES module entrypoint for hosted applications. Script entrypoint also supports file:// demos. */
import './taktera-ui.js';
const api=globalThis.TakteraUI;
export const { PRODUCTS, THEMES, setTheme, button, field, select, checkbox, status, alert, card, tabs, dialog, table, toastRegion }=api;
export default api;
