/** Browser DOM components, Taktera Design System Web Core v4.0 alpha.4.
 *  All data passed to label/value/message is output as text, not interpreted as HTML.
 */
export type Product = 'platform' | 'clinic' | 'beauty' | 'spa' | 'fitness' | 'travel';
export type Theme = 'light' | 'dark';
export type Tone = 'info' | 'success' | 'warning' | 'error';
export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
export type ThemeOptions = { product?: Product; theme?: Theme };
export const PRODUCTS: ReadonlyArray<Product>;
export const THEMES: ReadonlyArray<Theme>;
export function setTheme(root: HTMLElement, options?: ThemeOptions): HTMLElement;
export interface ButtonOptions {
  label?: string; variant?: ButtonVariant; disabled?: boolean; loading?: boolean;
  type?: 'button' | 'submit' | 'reset'; onClick?: (event: MouseEvent) => void;
}
export function button(options?: ButtonOptions): HTMLButtonElement;
export interface FieldOptions {
  label: string; value?: string; placeholder?: string; type?: string;
  required?: boolean; error?: string; name?: string;
  onInput?: (value: string, event: Event) => void;
}
export interface FieldInstance { element: HTMLDivElement; input: HTMLInputElement; setError(message?: string): void }
export function field(options: FieldOptions): FieldInstance;
export interface SelectOptions {
  label: string; options?: ReadonlyArray<{label:string; value:string | number}>;
  value?: string | number; onChange?: (value: string, event: Event) => void; name?:string;
}
export interface SelectInstance { element: HTMLDivElement; input: HTMLSelectElement }
export function select(options: SelectOptions): SelectInstance;
export interface CheckboxOptions {
  label: string; checked?: boolean; switchRole?: boolean;
  onChange?: (checked: boolean, event: Event) => void;
}
export interface CheckboxInstance { element: HTMLLabelElement; input: HTMLInputElement }
export function checkbox(options: CheckboxOptions): CheckboxInstance;
export function status(options?: {tone?: Tone; label?:string}): HTMLSpanElement;
export function alert(options?: {tone?: Tone; title?:string; message?:string}): HTMLElement;
export function card(options?: {title?:string; children?: ReadonlyArray<Node | string | number | null | undefined>}): HTMLElement;
export interface TabsOptions {
  items: ReadonlyArray<{id:string; label:string; content?:Node | string | number}>;
  activeId?:string; onChange?: (id:string) => void;
}
export interface TabsInstance { element: HTMLDivElement; activate(id:string):void; readonly selected:string }
export function tabs(options: TabsOptions): TabsInstance;
export type Locale = 'ru' | 'en';
export type LocalizedLabels = Partial<Record<'cancel'|'save'|'previous'|'next'|'tablePages'|'empty'|'of', string>>;
export interface DialogOptions {
  title?:string; content?:Node | string | number; confirmLabel?:string;
  onConfirm?:()=>boolean | void; onClose?: (returnValue:string)=>void;
  locale?:Locale;labels?:LocalizedLabels;
}
export interface DialogInstance { element: HTMLDialogElement; open():void; close():void }
export function dialog(options?:DialogOptions):DialogInstance;
export interface TableColumn<T> { key:keyof T & string; label:string; sortable?:boolean }
export interface TableOptions<T extends object> {
  columns:ReadonlyArray<TableColumn<T>>;rows?:ReadonlyArray<T>;
  rowKey?:(row:T,index:number)=>string;pageSize?:number;emptyText?:string;locale?:Locale;labels?:LocalizedLabels;
}
export interface TableInstance<T extends object> {
  element: HTMLDivElement;setRows(rows:ReadonlyArray<T>):void;
  readonly sort:{key:string | null;direction:'asc' | 'desc'};
}
export function table<T extends object>(options:TableOptions<T>):TableInstance<T>;
export interface ToastRegionInstance {element:HTMLDivElement;push(message:string,tone?:Tone):HTMLElement}
export function toastRegion(options?:{locale?:'ru'|'en';labels?:Record<string,string>}):ToastRegionInstance;
declare const api: Readonly<{
  PRODUCTS:typeof PRODUCTS;THEMES:typeof THEMES;setTheme:typeof setTheme;
  button:typeof button;field:typeof field;select:typeof select;checkbox:typeof checkbox;
  status:typeof status;alert:typeof alert;card:typeof card;
  tabs:typeof tabs;dialog:typeof dialog;table:typeof table;toastRegion:typeof toastRegion;
}>;
export default api;
