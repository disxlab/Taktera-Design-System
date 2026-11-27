const root=document.getElementById('root'),ui=globalThis.TakteraUI;
ui.setTheme(root,{product:'platform',theme:'light'});
root.append(ui.button({label:'Test action',onClick:()=>{document.getElementById('result').textContent='Action completed'}}));
