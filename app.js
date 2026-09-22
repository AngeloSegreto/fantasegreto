(()=>{'use strict';
const S={registry:[],details:{},news:null,filtered:[],role:'ALL',q:'',shown:24,selected:null,bound:false};
const $=s=>document.querySelector(s),esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const CAPS={P:3,D:8,C:8,A:6};
const num=x=>Number.isFinite(Number(x))?Number(x):null;
function normName(s){return String(s??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'')}
function applyCurrentOverlay(base,details,overlay){
 const players=base.map(p=>({...p})),byId=new Map(players.map(p=>[p.id,p]));
 const outDetails={};
 for(const [id,d] of Object.entries(details||{}))outDetails[id]={...d,metrics:{...(d.metrics||{})},blocks:[...(d.blocks||[])]};
 const aliases=new Map([
  ['Roma|Malen','p-malen-roma'],
  ['Frosinone|Raimondo','p-raimondo-frosinone'],
  ['Monza|Varela','p-varela-g-monza'],
  ['Inter|Lautaro Martinez','p-martinez-l-inter'],
  ['Roma|Dybala','p-dybala-roma'],
  ['Frosinone|Schmid','p-fc-7551'],
  ['Inter|Diouf','p-diouf-inter'],
  ['Juventus|Grabara','p-fc-7603'],
  ['Juventus|Boga','p-boga-juventus'],
  ['Juventus|Locatelli','p-locatelli-juventus'],
  ['Juventus|Yildiz','p-yildiz-juventus'],
  ['Juventus|Thuram K.','p-thuram-k-juventus'],
  ['Juventus|Kolo Muani','p-kolo-muani-juventus']
 ]);
 const find=(name,team)=>{
   const aid=aliases.get(`${team}|${name}`);
   if(aid&&byId.has(aid))return byId.get(aid);
   const nn=normName(name),nt=normName(team);
   const exact=players.filter(p=>normName(p.team)===nt&&normName(p.name)===nn);
   return exact.length===1?exact[0]:null;
 };
 const addBlock=(p,title,text)=>{
   if(!p)return;
   const d=outDetails[p.id]||{id:p.id,name:p.name,subtitle:`${p.team} · ${p.role}`,role:p.role,metrics:{},instruction:'',blocks:[]};
   d.blocks=[...(d.blocks||[]).filter(x=>x.title!==title),{title,text}];
   outDetails[p.id]=d;
 };
 for(const g of overlay?.leaders?.goals||[]){
   const p=find(g.name,g.team); if(!p)continue;
   p._performance22={...(p._performance22||{}),goals:g.value,cutoff:overlay.cutoff};
   addBlock(p,'Performance 22/09',`Dato verificato al 22/09/2026: ${g.value} gol. Overlay informativo; FOS/Risk/MAX base non vengono riscritti automaticamente.`);
 }
 for(const a of overlay?.leaders?.assists||[]){
   const p=find(a.name,a.team); if(!p)continue;
   p._performance22={...(p._performance22||{}),assists:a.value,cutoff:overlay.cutoff};
   const perf=p._performance22;
   const bits=[]; if(perf.goals!=null)bits.push(`${perf.goals} gol`); if(perf.assists!=null)bits.push(`${perf.assists} assist`);
   addBlock(p,'Performance 22/09',`Dato verificato al 22/09/2026: ${bits.join(' · ')}. Overlay informativo; FOS/Risk/MAX base non vengono riscritti automaticamente.`);
 }
 for(const m of overlay?.medical_verified||[]){
   const p=find(m.name,m.team); if(!p)continue;
   p._medical22={status:m.status,issue:m.issue,cutoff:overlay.cutoff};
   addBlock(p,'Disponibilità 22/09',`${m.status} · ${m.issue}. Fonte corrente verificata; nessuna percentuale MAX viene inventata.`);
 }
 for(const p of players)if(!outDetails[p.id])outDetails[p.id]={id:p.id,name:p.name,subtitle:`${p.team} · ${p.role}`,role:p.role,metrics:{},instruction:'',blocks:[]};
 return{players,details:outDetails};
}
async function fetchData(){
 const [r,d,o,v]=await Promise.all([
  fetch('./registry.json',{cache:'no-store'}).then(x=>{if(!x.ok)throw Error('registry.json '+x.status);return x.json()}),
  fetch('./player-details.json',{cache:'no-store'}).then(x=>{if(!x.ok)throw Error('player-details.json '+x.status);return x.json()}),
  fetch('./md5-22sep2026.json',{cache:'no-store'}).then(x=>{if(!x.ok)throw Error('md5-22sep2026.json '+x.status);return x.json()}),
  fetch('./version.json',{cache:'no-store'}).then(x=>{if(!x.ok)throw Error('version.json '+x.status);return x.json()})
 ]);
 const expected=Number(v.runtime_registry_count||v.canonical_registry_runtime_count||r.count||0);
 if(!expected||Number(r.count)!==expected||(r.players||[]).length!==expected)throw Error('Registry runtime non riconciliato al target '+expected);
 if(Number(d.count)!==expected||Object.keys(d.details||{}).length!==expected)throw Error('Player details runtime non riconciliati al target '+expected);
 const merged=applyCurrentOverlay(r.players||[],d.details||{},o);
 S.registry=merged.players;S.details=merged.details;S.news=o;
 window.FS_MD5=o;window.FS_VERSION=v;
 window.FS_APP={registry:()=>S.registry,details:()=>S.details,news:()=>S.news,refresh:refreshAll,open,close,selected:()=>S.selected,player:id=>S.registry.find(x=>x.id===id)};
 window.dispatchEvent(new CustomEvent('fs:registry-ready',{detail:{players:S.registry.length,base_players:(r.players||[]).length,overlay:'MD5_22SEP2026',news_additions:0}}));
}
function finishBoot(){if(S.bound)return;S.bound=true;bind();filter();refreshAll();document.body.dataset.ready='1';window.dispatchEvent(new CustomEvent('fs:ready',{detail:{players:S.registry.length}}));}
function bind(){$('#q').addEventListener('input',e=>{S.q=e.target.value.trim().toLowerCase();S.shown=24;filter()});$('#clear').onclick=()=>{$('#q').value='';S.q='';S.shown=24;filter()};document.querySelectorAll('[data-role]').forEach(b=>b.onclick=()=>{document.querySelectorAll('[data-role]').forEach(x=>x.classList.remove('on'));b.classList.add('on');S.role=b.dataset.role;S.shown=24;filter()});$('#more').onclick=()=>{S.shown+=24;renderList()};$('#list').addEventListener('click',e=>{const row=e.target.closest('.row');if(row)open(row.dataset.id)});$('#shade').onclick=close;$('#close').onclick=close;$('#sheet').addEventListener('click',e=>{const b=e.target.closest('[data-act]');if(b)transact(b.dataset.act)});$('#nav-list').onclick=()=>{showMain();close();window.scrollTo({top:$('.toolbar').offsetTop-6,behavior:'smooth'})};$('#nav-auction').onclick=()=>{showMain();const p=S.filtered.find(p=>!soldIds().has(p.id))||S.registry[0];if(p)open(p.id)};$('#nav-managers').onclick=()=>openPanel('managers');$('#nav-roster').onclick=()=>openPanel('roster');$('#nav-more').onclick=()=>openPanel('more');document.querySelectorAll('[data-panel-close]').forEach(b=>b.onclick=closePanels);window.addEventListener('fs:state-changed',refreshAll);window.addEventListener('storage',refreshAll)}
function showMain(){closePanels();document.querySelectorAll('.bottom button').forEach(x=>x.classList.remove('primary'));$('#nav-list').classList.add('primary')}
function openPanel(name){close();document.querySelectorAll('.panel').forEach(x=>x.classList.remove('open'));const p=$('#panel-'+name);if(p)p.classList.add('open');document.body.style.overflow='hidden';document.querySelectorAll('.bottom button').forEach(x=>x.classList.remove('primary'));$('#nav-'+name)?.classList.add('primary');refreshAll()}
function closePanels(){document.querySelectorAll('.panel').forEach(x=>x.classList.remove('open'));document.body.style.overflow='';document.querySelectorAll('.bottom button').forEach(x=>x.classList.remove('primary'));$('#nav-list')?.classList.add('primary')}
function filter(){let a=S.registry.filter(p=>S.role==='ALL'||p.role===S.role);if(S.q)a=a.filter(p=>(p.name+' '+p.team+' '+(p.list_meta||'')+' '+(p._medical22?.issue||'')+' '+(p._medical22?.status||'')).toLowerCase().includes(S.q));a.sort((x,y)=>(num(y.score)??-999)-(num(x.score)??-999));S.filtered=a;renderList()}
function state(){try{return window.FS_AUCTION_ENGINE?.state?.()}catch(e){return null}}
function soldIds(){const st=state();return st?st.soldIds:new Set()}
function dynamicMax(p,st){try{return window.FS_AUCTION_ENGINE?.exactMax?.(p,st)??0}catch(e){return 0}}
function runtimeLabel(p,st){const lm=st?dynamicMax(p,st):0,med=p._medical22?.status;let label;if(!st)label=p.decision||'—';else if(lm<=0)label='PASS · RECALC';else{const ideal=Number(p.ideal||0);label=lm<=ideal?`BUY/WAIT ≤ ${lm}`:`BUY ≤ ${ideal} · WAIT ≤ ${lm}`}return med?`${label} · ${med}`:label}
function renderList(){const sold=soldIds(),avail=S.filtered.filter(p=>!sold.has(p.id)),a=avail.slice(0,S.shown);$('#count').textContent=`${avail.length} disponibili · ${a.length} renderizzati`;const st=state();$('#list').innerHTML=a.map(p=>{const label=runtimeLabel(p,st),k=label.startsWith('BUY')?'BUY':label.startsWith('PASS')?'PASS':'WAIT',lm=st?dynamicMax(p,st):0,score=num(p.score);return `<article class="row" data-id="${esc(p.id)}"><span class="role ${esc(p.role)}">${esc(p.role)}</span><div class="name"><b>${esc(p.name)}</b><small>${esc(p.team)} · ${esc((p.list_meta||'').replace(p.team+' · ','')||p.role)}</small><span class="decision ${k}">${esc(label)}</span></div><div class="nums"><b>${score===null?'—':esc(score.toFixed(1))}</b><small>${lm>0?'MAX LIVE '+esc(lm):'MAX RECALC'}</small></div></article>`}).join('')||'<div class="empty">Nessun giocatore disponibile.</div>';$('#more').hidden=a.length>=avail.length}
function syncState(){const st=state();if(!st)return;$('#budget').textContent=st.budget??500;$('#slots-total').textContent=st.slots??25;for(const r of ['P','D','C','A']){const need=st.managerStates?.ME?.needs?.[r]??CAPS[r];$('#slot-'+r).textContent=`${CAPS[r]-need}/${CAPS[r]}`}$('#league-budget').textContent=st.leagueBudget??5000;$('#league-sold').textContent=st.leagueSold??0}
function open(id){const p=S.registry.find(x=>x.id===id),d=S.details[id];if(!p||!d)return;S.selected=p;const st=state();$('#s-role').className='role '+p.role;$('#s-role').textContent=p.role;$('#s-name').textContent=p.name;$('#s-sub').textContent=d.subtitle||`${p.team} · ${p.role}`;const lm=st?dynamicMax(p,st):0,metrics={'FS Score':num(p.score)===null?'RECALC':Number(p.score).toFixed(1),'Prezzo ideale':num(p.ideal)===null?'RECALC':p.ideal,'MAX base':num(p.max)===null?'RECALC':p.max,'Quotazione':num(p.quote)===null?'—':p.quote,'FVM':num(p.fvm)===null?'—':p.fvm,'Rischio':num(p.risk)===null?'—':p.risk,'Confidence':p.confidence||'—'};if(p._performance22?.goals!=null)metrics['Gol 22/09']=p._performance22.goals;if(p._performance22?.assists!=null)metrics['Assist 22/09']=p._performance22.assists;if(p._medical22)metrics['Medical 22/09']=p._medical22.status;if(st){metrics['MAX LIVE']=lm>0?lm:'RECALC';const op=window.FS_AUCTION_ENGINE?.opponentPressure?.(p,st);if(op){metrics['Pressione']=op.pressure+'/100';metrics['Rivali attivi']=op.activeCount+'/9'}}$('#metrics').innerHTML=Object.entries(metrics).map(([k,v])=>`<div class="metric"><small>${esc(k)}</small><b>${esc(v)}</b></div>`).join('');const inst=window.FS_AUCTION_ENGINE?.instruction?.(p,st)||(d.instruction||p.decision);$('#instruction').innerHTML=`<b>Istruzione d’asta LIVE</b><p>${esc(inst)}</p>`;$('#blocks').innerHTML=(d.blocks||[]).map(x=>`<div class="block"><b>${esc(x.title)}</b><p>${esc(x.text)}</p></div>`).join('');renderPressure(p,st);$('#price').value='';renderOwnerOptions();$('#owner').value='';$('#runtime').textContent='Engine V4.0.23.1 LINEAGE · V4.1.9 22SEP RUNTIME · SHADOW GUARD · '+(lm>0?'MAX ESATTO '+lm:'MAX RECALC');$('#sheet').classList.add('open');document.body.style.overflow='hidden';setTimeout(()=>$('#price').focus({preventScroll:true}),80)}
function renderOwnerOptions(){const names=window.FS_STATE?.managerNames?.()||{};$('#owner').innerHTML='<option value="">Se PERSO: scegli rivale</option>'+Array.from({length:9},(_,i)=>{const id='R'+(i+1);return `<option value="${id}">${esc(names[id]||('Manager '+(i+1)))}</option>`}).join('')}
function renderPressure(p,st){const el=$('#pressure');if(!st){el.innerHTML='';return}const op=window.FS_AUCTION_ENGINE?.opponentPressure?.(p,st);if(!op){el.innerHTML='';return}const top=op.details.slice(0,3);el.innerHTML=`<div class="pressure-head"><b>PRESSIONE LIVE</b><strong>${op.pressure}/100</strong></div><div class="pressure-sub">${op.activeCount}/9 rivali possono competere · domanda ${op.totalDemand} · supply ${op.supply}</div>${top.map(x=>`<div class="pressure-rival"><span><b>${esc(x.name||x.owner)}</b><small>${x.budget} cr · ${x.need} ${p.role} mancanti · ceiling ${x.safe}</small></span><strong>${x.score}</strong></div>`).join('')}`}
function close(){$('#sheet').classList.remove('open');document.body.style.overflow='';S.selected=null}
function transact(result){const p=S.selected;if(!p)return;const price=parseInt($('#price').value||'0',10);if(!price||price<1){$('#runtime').textContent='Inserisci il prezzo di aggiudicazione.';return}const owner=result==='LOST'?$('#owner').value:'';if(result==='LOST'&&!owner){$('#runtime').textContent='Se PERSO scegli il rivale.';return}const res=window.FS_AUCTION_ENGINE?.transaction?.({playerId:p.id,result,owner,price});if(!res?.ok){$('#runtime').textContent=res?.error||'Transazione non riuscita.';return}close();S.shown=Math.max(24,S.shown);filter();refreshAll();window.scrollTo({top:$('.toolbar').offsetTop-6,behavior:'smooth'})}
function renderRoster(){const st=state(),root=$('#roster-content');if(!st||!root)return;let h='';for(const r of ['P','D','C','A']){const arr=st.mine.filter(x=>x.role===r);h+=`<h3>${r} · ${arr.length}/${CAPS[r]}</h3>`+(arr.length?arr.map(x=>`<div class="roster-item"><span class="role ${r}">${r}</span><div><b>${esc(x.name)}</b><small>${esc(x.team)}</small></div><strong>${x.price}</strong></div>`).join(''):'<div class="empty compact">Nessun acquisto.</div>')}root.innerHTML=h}
function renderLedger(){const st=state(),root=$('#ledger-content');if(!st||!root)return;root.innerHTML=st.tx.length?st.tx.slice().reverse().map((t,i)=>`<div class="ledger-row"><span>#${String(st.tx.length-i).padStart(3,'0')} · ${esc(t.name)}<small>${esc(t.team)} · ${t.role} · ${new Date(t.ts).toLocaleTimeString('it-IT',{hour:'2-digit',minute:'2-digit'})}</small></span><b>${t.owner==='ME'?'IO':esc(window.FS_STATE?.managerNames?.()?.[t.owner]||t.owner)} · ${t.price}</b></div>`).join(''):'<div class="empty compact">Nessuna transazione.</div>'}
function refreshAll(){syncState();renderList();renderRoster();renderLedger();window.FS_OPPONENTS?.render?.();window.FS_PLAN25?.render?.();window.FS_AUDIT?.render?.()}
window.addEventListener('fs:engine-ready',finishBoot,{once:true});fetchData().catch(e=>{document.body.dataset.bootError='1';window.dispatchEvent(new CustomEvent('fs:boot-error',{detail:{message:e.message}}))});
})();
