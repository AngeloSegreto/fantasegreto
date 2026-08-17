/* FS V4.1.1 Runtime Reset — preserved functional engine blocks from V4.1.0. Audit payloads removed. */
window.FS_NEWS_POLICY=Object.freeze({asOf:'2026-08-16',scope:'SERIE_A_ONLY',excludedPlayers:['Strefezza','Lukaku','Ondrejka','Athekame','Djimsiti','Angelino','Gutierrez'],excludedTeams:['Palermo'],rule:'OUT_OF_SERIE_A_OR_ASTERISK'});

/* SOURCE BLOCK: fs-live-auction-v393 */

(function(){
 const KEY='fs_gold_auction_v393', OLDKEYS=['fs_gold_auction_v390','fs_gold_auction_v389'];
 const START=500, LEAGUE_START=5000, TOTAL=25, LEAGUE_SLOTS=250, MIN_SLOT=1;
 const roleCaps={P:3,D:8,C:8,A:6};
 const owners=['ME','R1','R2','R3','R4','R5','R6','R7','R8','R9'];
 function load(){
   try{
     const cur=localStorage.getItem(KEY); if(cur)return JSON.parse(cur);
     for(const k of OLDKEYS){ const raw=localStorage.getItem(k); if(raw){ const old=JSON.parse(raw||'[]'); if(old.length){localStorage.setItem(KEY,JSON.stringify(old)); return old;} } }
   }catch(e){}
   return [];
 }
 function save(x){localStorage.setItem(KEY,JSON.stringify(x))}
 function money(n){return Number(n||0).toLocaleString('it-IT')}
 function allCards(){return [...document.querySelectorAll('.purchase-box')]}
 const uniq=new Map(); allCards().forEach(c=>{if(!uniq.has(c.dataset.playerId))uniq.set(c.dataset.playerId,c)});
 const players=[...uniq.values()].map(c=>({id:c.dataset.playerId,name:c.dataset.name,team:c.dataset.team,role:c.dataset.role,score:+c.dataset.score,ideal:+c.dataset.ideal,base:+c.dataset.baseMax}));
 const byId=Object.fromEntries(players.map(p=>[p.id,p]));
 function premiumSet(){let set=new Set(); for(const r of Object.keys(roleCaps)){const a=players.filter(p=>p.role===r).sort((x,y)=>y.score-x.score); const k=Math.max(1,Math.ceil(a.length*.10)); a.slice(0,k).forEach(p=>set.add(p.id));} return set}
 const PREMIUM=premiumSet();
 function ownerName(owner,tx){const a=tx.filter(x=>x.owner===owner && x.managerName); return a.length?a[a.length-1].managerName:(owner==='ME'?'IO':owner)}
 function ownerState(owner,tx){
   const a=tx.filter(x=>x.owner===owner), spent=a.reduce((s,x)=>s+x.price,0), roles={P:0,D:0,C:0,A:0}; a.forEach(x=>roles[x.role]=(roles[x.role]||0)+1);
   const needs={}; Object.keys(roleCaps).forEach(r=>needs[r]=Math.max(0,roleCaps[r]-roles[r]));
   const slots=Math.max(0,TOTAL-a.length), budget=START-spent, minClose=slots*MIN_SLOT, safeAny=Math.max(0,budget-Math.max(0,(slots-1)*MIN_SLOT));
   const premiumCount=a.filter(x=>PREMIUM.has(x.id)).length;
   const premiumByRole={P:0,D:0,C:0,A:0}; a.filter(x=>PREMIUM.has(x.id)).forEach(x=>premiumByRole[x.role]++);
   return {owner,name:ownerName(owner,tx),spent,budget,count:a.length,slots,roles,needs,minClose,safeAny,premiumCount,premiumByRole};
 }
 function state(){
   const tx=load(), soldIds=new Set(tx.map(x=>x.id)), spentLeague=tx.reduce((s,x)=>s+x.price,0), leagueBudget=LEAGUE_START-spentLeague;
   const leagueSold=tx.length, leagueSlots=LEAGUE_SLOTS-leagueSold, leagueMinClose=leagueSlots*MIN_SLOT, leagueExtra=Math.max(0,leagueBudget-leagueMinClose);
   const mine=tx.filter(x=>x.owner==='ME'), spent=mine.reduce((s,x)=>s+x.price,0), budget=START-spent, slots=TOTAL-mine.length, minComplete=slots*MIN_SLOT;
   const reserve=Math.min(Math.max(0,Math.round(budget*.07)),Math.max(0,budget-minComplete)), fire=Math.max(0,budget-minComplete-reserve);
   const top=mine.filter(x=>PREMIUM.has(x.id)).length, topLeft=players.filter(p=>PREMIUM.has(p.id)&&!soldIds.has(p.id)).length;
   const managerStates=Object.fromEntries(owners.map(o=>[o,ownerState(o,tx)]));
   return {tx,soldIds,spentLeague,leagueBudget,leagueSold,leagueSlots,leagueMinClose,leagueExtra,mine,spent,budget,slots,minComplete,reserve,fire,top,topLeft,managerStates};
 }
 function roleSupply(role,st){return players.filter(p=>p.role===role&&!st.soldIds.has(p.id)).length}
 function premiumRoleSupply(role,st){return players.filter(p=>p.role===role&&PREMIUM.has(p.id)&&!st.soldIds.has(p.id)).length}
 function opponentPressure(p,st){
   const supply=Math.max(1,roleSupply(p.role,st)), premiumSupply=Math.max(1,premiumRoleSupply(p.role,st));
   const totalDemand=owners.slice(1).reduce((z,o)=>z+st.managerStates[o].needs[p.role],0);
   const scarcity=Math.min(1.6,totalDemand/supply), premiumScarcity=PREMIUM.has(p.id)?Math.min(1.7,totalDemand/premiumSupply):1;
   const details=owners.slice(1).map(o=>{
     const m=st.managerStates[o], need=m.needs[p.role];
     if(need<=0||m.slots<=0||m.budget<=0)return {owner:o,name:m.name,score:0,need,safe:0,budget:m.budget,status:'OUT',canContest:false};
     const safe=Math.max(0,m.budget-Math.max(0,(m.slots-1)*MIN_SLOT));
     const cap=Math.min(1.25,safe/Math.max(1,p.ideal));
     const roleNeed=Math.min(1,need/Math.max(1,roleCaps[p.role]));
     const slotNeed=Math.min(1,m.slots/TOTAL);
     const tierNeed=PREMIUM.has(p.id)?Math.max(.25,1-Math.min(1,m.premiumCount/3)):.45;
     const scarcityFactor=Math.min(1,scarcity/1.25), ps=PREMIUM.has(p.id)?Math.min(1,premiumScarcity/1.25):scarcityFactor;
     let score=Math.round(100*(.40*Math.min(1,cap)+.25*roleNeed+.10*slotNeed+.15*tierNeed+.10*ps));
     if(safe<p.ideal)score=Math.round(score*.55);
     const canContest=safe>=Math.max(1,Math.round(p.ideal*.75));
     const status=!canContest?'LOW':score>=75?'HIGH':score>=50?'MEDIUM':'LOW';
     return {owner:o,name:m.name,score,need,safe,budget:m.budget,status,canContest,roles:m.roles};
   }).sort((a,b)=>b.score-a.score);
   const active=details.filter(x=>x.canContest), maxScore=details.length?details[0].score:0, avg=active.length?Math.round(active.reduce((s,x)=>s+x.score,0)/active.length):0;
   const pressure=Math.min(100,Math.round(maxScore*.60+avg*.40));
   return {pressure,activeCount:active.length,details,scarcity,premiumScarcity,totalDemand,supply,premiumSupply};
 }
 function liveMax(p,st){
   let adj=1; const topNeed=Math.max(0,3-st.top), scarcityTop=st.topLeft<=topNeed+2;
   if(PREMIUM.has(p.id)&&topNeed>0&&scarcityTop&&st.fire>p.base)adj=1.12;
   else if(PREMIUM.has(p.id)&&st.top>=3)adj=.92;
   else if(st.budget<st.minComplete+st.reserve+p.base)adj=.90;
   const op=opponentPressure(p,st);
   if(adj>=1&&!st.soldIds.has(p.id)) adj*=1+Math.min(.08,op.pressure/1250); // max +8%
   const myRoleNeed=st.managerStates.ME.needs[p.role]; if(myRoleNeed<=0)return 0;
   const safe=Math.max(1,st.budget-Math.max(0,(st.slots-1)*MIN_SLOT));
   return Math.max(1,Math.min(safe,Math.round(p.base*adj)));
 }
 function decision(price,p,lm){if(lm<=0)return 'PASS'; if(price<=p.ideal)return 'BUY'; if(price<=lm)return 'WAIT'; return 'PASS'}
 function pressureClass(s){return s>=75?'opp-high':s>=50?'opp-med':s>0?'opp-low':'opp-out'}
 function renderOpponent(card,p,st){
   let el=card.querySelector('.opp-board'); if(!el){el=document.createElement('div'); el.className='opp-board'; card.querySelector('.result-line')?.insertAdjacentElement('afterend',el)}
   const op=opponentPressure(p,st), top=op.details.slice(0,3);
   el.innerHTML='<div class="opp-title"><span>PRESSIONE AVVERSARI</span><span class="opp-score">'+op.pressure+'/100</span></div>'+
     '<div class="opp-sub">Competitori reali '+op.activeCount+'/9 · domanda ruolo '+op.totalDemand+' · supply '+op.supply+(PREMIUM.has(p.id)?' · premium supply '+op.premiumSupply:'')+'</div>'+
     '<div class="opp-rivals">'+top.map(x=>'<div class="opp-rival"><div><b>'+x.owner+' / '+x.name+'</b><small>'+x.budget+' cr · '+x.need+' '+p.role+' mancanti · safe ceiling '+x.safe+'</small></div><span class="'+pressureClass(x.score)+'">'+x.status+' '+x.score+'</span></div>').join('')+'</div>';
   return op;
 }
 function render(){
   const st=state();
   document.getElementById('k-budget').textContent=st.budget; document.getElementById('k-spent').textContent=st.spent; document.getElementById('k-slots').textContent=st.slots; document.getElementById('k-firepower').textContent=st.fire;
   document.getElementById('s-reserve').textContent=st.reserve; document.getElementById('s-top').textContent=st.top; document.getElementById('s-top-left').textContent=st.topLeft; document.getElementById('s-completion').textContent=st.budget>=st.minComplete?'SICURO':'CRITICO'; document.getElementById('s-aggr').textContent=(st.top<3&&st.topLeft<=Math.max(0,3-st.top)+2)?'ALTA':'NORMALE'; document.getElementById('s-recalc').textContent=players.length-st.tx.length;
   document.getElementById('l-spent').textContent=money(st.spentLeague); document.getElementById('l-budget').textContent=money(st.leagueBudget); document.getElementById('l-sold').textContent=st.leagueSold+' / '+LEAGUE_SLOTS; document.getElementById('l-slots').textContent=st.leagueSlots; document.getElementById('l-minclose').textContent=money(st.leagueMinClose); document.getElementById('l-extra').textContent=money(st.leagueExtra); document.getElementById('l-missing').textContent=money(st.leagueBudget);
   const lnk=document.getElementById('live-state-link'); if(lnk)lnk.textContent='🔥 '+st.budget+' CR · '+st.slots+' SLOT · LEGA '+money(st.leagueBudget);
   document.querySelectorAll('.prow').forEach(row=>row.classList.remove('sold-won','sold-lost')); document.querySelectorAll('.sold-badge').forEach(x=>x.remove());
   st.tx.forEach(t=>document.querySelectorAll('a[href="#'+t.id+'"]').forEach(a=>{const row=a.closest('.prow');if(!row)return;row.classList.add(t.owner==='ME'?'sold-won':'sold-lost');const foot=row.querySelector('.prow-foot');if(foot&&!foot.querySelector('.sold-badge')){const b=document.createElement('span');b.className='sold-badge '+(t.owner==='ME'?'won':'lost');b.textContent=t.owner==='ME'?'VINTO '+t.price:'PERSO '+t.owner+' · '+t.price;foot.insertBefore(b,a)}}));
   allCards().forEach(c=>{const p=byId[c.dataset.playerId];if(!p)return;const lm=liveMax(p,st),op=renderOpponent(c,p,st),el=c.querySelector('.live-max'),rs=c.querySelector('.live-reason');if(el){el.textContent=lm;el.className='live-max '+(lm>p.base?'live-up':lm<p.base?'live-down':'live-flat')}if(rs){rs.textContent=lm===0?'ruolo già completo':(lm>p.base?'↑ scarcity/opponent '+op.pressure:(lm<p.base?'↓ budget/coverage':'MAX BASE'))}
     const t=st.tx.find(x=>x.id===p.id),inp=c.querySelector('.purchase-price'),mn=c.querySelector('.manager-name'),sel=c.querySelector('.owner-select'),res=c.querySelector('.purchase-result');if(t){inp.value=t.price;if(mn)mn.value=t.managerName||'';sel.value=t.owner==='ME'?'':t.owner;res.textContent=t.owner==='ME'?'VINTO IO · '+t.price+' crediti':'PERSO · '+t.owner+' · '+t.price+' crediti';res.className='purchase-result '+(t.owner==='ME'?'won':'lost')}else{if(document.activeElement!==inp)inp.value='';if(mn&&document.activeElement!==mn)mn.value='';sel.value='';res.textContent='LIBERO';res.className='purchase-result'}});
   const root=document.getElementById('roster-list');if(root){let h='';for(const r of ['P','D','C','A']){const arr=st.mine.filter(x=>x.role===r);h+='<div class="roleblock"><h3>'+r+' · '+arr.length+'/'+roleCaps[r]+'</h3>';if(!arr.length)h+='<div class="empty">Nessun giocatore acquistato.</div>';arr.forEach(b=>h+='<div class="roster-row"><span class="role role-'+r+'">'+r+'</span><div><b>'+b.name+'</b><br><small>'+b.team+(PREMIUM.has(b.id)?' · PREMIUM':'')+'</small></div><span class="cost">'+b.price+'</span><button class="mini-btn undo" data-id="'+b.id+'">↩</button></div>');h+='</div>'}root.innerHTML=h;root.querySelectorAll('.undo').forEach(btn=>btn.onclick=()=>remove(btn.dataset.id))}
   const mt=document.getElementById('manager-table');if(mt){let h='<div class="manager-row"><span>Manager</span><span>Speso</span><span>Residuo</span><span>Slot</span></div>';owners.forEach(o=>{const m=st.managerStates[o];h+='<div class="manager-row"><span>'+(o==='ME'?'IO':o)+'</span><span>'+m.spent+'</span><span>'+m.budget+'</span><span>'+m.count+'/25</span></div>'});mt.innerHTML=h}
   const omt=document.getElementById('opp-manager-table');if(omt){let h='<div class="opp-manager-head"><span>Manager</span><span>P</span><span>D</span><span>C</span><span>A</span><span>Budget</span><span>Safe</span><span>Premium</span></div>';owners.forEach(o=>{const m=st.managerStates[o];h+='<div class="opp-manager-row"><span><b>'+(o==='ME'?'IO':o)+'</b><br>'+m.name+'</span><span>'+m.roles.P+'/3</span><span>'+m.roles.D+'/8</span><span>'+m.roles.C+'/8</span><span>'+m.roles.A+'/6</span><span>'+m.budget+'</span><span>'+m.safeAny+'</span><span>'+m.premiumCount+'</span></div>'});omt.innerHTML=h}
   const log=document.getElementById('auction-log');if(log){let run=0;log.className='';log.innerHTML=st.tx.length?st.tx.map((t,i)=>{run+=t.price;const esito=t.owner==='ME'?'VINTO IO':'PERSO '+t.owner,mgr=t.managerName?' · '+t.managerName:'';return '<div class="log-row">#'+String(i+1).padStart(3,'0')+' · '+t.name+' · '+t.role+' · '+esito+mgr+' · '+t.price+' cr · lega residua '+(LEAGUE_START-run)+'</div>'}).join(''):'<div class="empty">Nessun acquisto registrato.</div>'}
 }
 function register(card,result){const p=byId[card.dataset.playerId],inp=card.querySelector('.purchase-price'),sel=card.querySelector('.owner-select'),price=parseInt(inp.value,10);if(!price||price<1)return alert('Inserisci il prezzo di aggiudicazione.');const owner=result==='WON'?'ME':sel.value,managerName=(card.querySelector('.manager-name')?.value||'').trim();if(result==='LOST'&&!owner)return alert('Se il giocatore è PERSO, scegli quale dei 9 rivali lo ha acquistato.');let tx=load(),other=tx.filter(x=>x.id!==p.id),ownerOther=other.filter(x=>x.owner===owner),ownerSpent=ownerOther.reduce((s,x)=>s+x.price,0),leagueSpent=other.reduce((s,x)=>s+x.price,0);if(ownerSpent+price>START)return alert((owner==='ME'?'Il tuo budget':'Il budget di '+owner)+' supererebbe 500 crediti.');if(leagueSpent+price>LEAGUE_START)return alert('Tetto lega superato: massimo 5.000 crediti.');if(ownerOther.length>=TOTAL)return alert('Il manager ha già 25 giocatori.');const rc=ownerOther.filter(x=>x.role===p.role).length;if(rc>=roleCaps[p.role])return alert('Slot '+p.role+' già completi per questo manager.');const now={id:p.id,name:p.name,team:p.team,role:p.role,price,owner,result,managerName,ts:new Date().toISOString()};tx=[...other,now];save(tx);render();location.hash='my-roster'}
 function remove(id){save(load().filter(x=>x.id!==id));render()}
 document.addEventListener('click',e=>{const b=e.target.closest('.purchase-btn');if(b)register(b.closest('.purchase-box'),b.dataset.result)});
 document.addEventListener('input',e=>{if(!e.target.classList.contains('purchase-price'))return;const c=e.target.closest('.purchase-box'),p=byId[c.dataset.playerId],st=state(),lm=liveMax(p,st),v=parseInt(e.target.value||'0',10),d=c.querySelector('.live-decision');if(v>0)d.dataset.currentDecision=decision(v,p,lm)});
 window.FS_AUCTION_ENGINE={state,opponentPressure,liveMax,ownerState}; render();
})();


/* SOURCE BLOCK: fs-plan25-engine-v394 */

(function(){
 const PLAN={
  P:[
   ['P1',['p-maignan-milan','p-svilar-roma','p-carnesecchi-atalanta']],
   ['P2',['p-butez-como','p-carnesecchi-atalanta','p-martinez-jo-inter']],
   ['P3',['p-carnesecchi-atalanta','p-de-gea-fiorentina','p-di-gregorio-juventus']]
  ],
  D:[
   ['D1',['p-dimarco-inter','p-bastoni-inter','p-bremer-juventus']],
   ['D2',['p-bastoni-inter','p-mancini-roma','p-pavlovic-milan']],
   ['D3',['p-bremer-juventus','p-mancini-roma','p-pavlovic-milan']],
   ['D4',['p-zappacosta-atalanta','p-cambiaso-juventus','p-dodo-fiorentina']],
   ['D5',['p-cambiaso-juventus','p-molina-n-roma','p-dodo-fiorentina','p-spinazzola-napoli']],
   ['D6',['p-mancini-roma','p-n-dicka-roma','p-pavlovic-milan']],
   ['D7',['p-pavlovic-milan','p-rrahmani-napoli','p-buongiorno-napoli']],
   ['D8',['p-akanji-inter','p-spence-inter','p-carlos-augusto-inter','p-obrador-sassuolo','p-kalulu-juventus']]
  ],
  C:[
   ['C1',['p-mctominay-napoli','p-calhanoglu-inter','p-de-bruyne-napoli']],
   ['C2',['p-calhanoglu-inter','p-mctominay-napoli','p-pulisic-milan']],
   ['C3',['p-orsolini-bologna','p-pulisic-milan','p-vlasic-torino']],
   ['C4',['p-pulisic-milan','p-paz-n-como','p-zaccagni-lazio']],
   ['C5',['p-de-bruyne-napoli','p-zaniolo-udinese','p-rabiot-milan']],
   ['C6',['p-zaniolo-udinese','p-vlasic-torino','p-baturina-como']],
   ['C7',['p-paz-n-como','p-pulisic-milan','p-orsolini-bologna']],
   ['C8',['p-rabiot-milan','p-baturina-como','p-frattesi-lazio','p-vlasic-torino']]
  ],
  A:[
   ['A1',['p-martinez-l-inter','p-malen-roma','p-hojlund-napoli']],
   ['A2',['p-malen-roma','p-thuram-inter','p-hojlund-napoli']],
   ['A3',['p-ramos-g-milan','p-kolo-muani-juventus','p-hojlund-napoli']],
   ['A4',['p-thuram-inter','p-kolo-muani-juventus','p-yildiz-juventus']],
   ['A5',['p-kolo-muani-juventus','p-yildiz-juventus','p-kean-fiorentina']],
   ['A6',['p-yildiz-juventus','p-douvikas-como','p-davis-k-udinese','p-romero-d-parma']]
  ]
 };
 const roleNames={P:'PORTIERI',D:'DIFENSORI',C:'CENTROCAMPISTI',A:'ATTACCANTI'};
 function card(id){return document.querySelector('.purchase-box[data-player-id="'+id+'"]')}
 function pObj(id){const c=card(id);if(!c)return null;return {id,name:c.dataset.name,team:c.dataset.team,role:c.dataset.role,score:+c.dataset.score,ideal:+c.dataset.ideal,base:+c.dataset.baseMax}}
 function txById(st,id){return st.tx.find(x=>x.id===id)}
 function esc(s){return String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}
 function renderPlan(){
  const root=document.getElementById('plan-body'); if(!root||!window.FS_AUCTION_ENGINE)return;
  const st=window.FS_AUCTION_ENGINE.state(); let html='',done=0,active=0,fallback=0,critical=0,alerts=[];
  for(const role of ['P','D','C','A']){
   html+='<h3 class="plan-role">'+roleNames[role]+'</h3>';
   for(const [slot,ids] of PLAN[role]){
    const owned=ids.map(id=>txById(st,id)).find(x=>x&&x.owner==='ME');
    let activeIdx=-1;
    if(!owned){for(let i=0;i<ids.length;i++){const x=txById(st,ids[i]);if(!x){activeIdx=i;break}}}
    const isCritical=!owned&&activeIdx<0; if(owned)done++; else if(isCritical){critical++;alerts.push(slot+' senza alternative disponibili');} else {active++; if(activeIdx>0)fallback++;}
    html+='<div class="plan-slot '+(owned?'done':isCritical?'critical':'')+'"><div class="plan-slot-head"><div class="plan-slot-id">'+slot+'</div><div><b>'+roleNames[role].slice(0,-1)+' '+slot.slice(1)+'</b><small>'+(owned?'Slot coperto da '+esc(owned.name):(isCritical?'Catena esaurita':'Target corrente: priorità '+(activeIdx+1)))+'</small></div><span class="plan-state '+(owned?'done':isCritical?'critical':'target')+'">'+(owned?'COPERTO':isCritical?'CRITICO':'TARGET')+'</span></div><div class="plan-chain">';
    ids.forEach((id,i)=>{const p=pObj(id),tx=txById(st,id),isOwned=tx&&tx.owner==='ME',isLost=tx&&tx.owner!=='ME',isActive=!owned&&i===activeIdx;let lm='—';if(p&&!tx){try{lm=window.FS_AUCTION_ENGINE.liveMax(p,st)}catch(e){lm=p.base||'—'}};const nm=p?p.name:id.replace(/^p-/,'').replaceAll('-',' '),team=p?p.team:'NON RISOLTO';html+='<div class="plan-choice '+(isOwned?'owned':isLost?'lost':isActive?'active':'')+'"><span class="plan-prio">P'+(i+1)+'</span><div><b>'+esc(nm)+'</b><small>'+esc(team)+(tx?' · '+(isOwned?'VINTO '+tx.price:'PERSO '+tx.owner+' · '+tx.price):(isActive?' · PROSSIMO TARGET':''))+'</small></div><span class="plan-max">'+(tx?'—':lm)+' <small>MAX</small></span>'+(p?'<a class="plan-link" href="#'+id+'">VALUTA</a>':'<span class="plan-link">N/D</span>')+'</div>'});
    html+='</div></div>';
   }
  }
  root.innerHTML=html; document.getElementById('plan-done').textContent=done+'/25';document.getElementById('plan-active').textContent=active;document.getElementById('plan-fallback').textContent=fallback;document.getElementById('plan-critical').textContent=critical;const al=document.getElementById('plan-alert');if(alerts.length){al.classList.add('show');al.textContent='⚠ '+alerts.join(' · ')}else{al.classList.remove('show');al.textContent=''}
 }
 // keep synchronized with auction engine render cycles / localStorage changes
 const obs=new MutationObserver(()=>{if(location.hash==='#fs-plan25')renderPlan()});obs.observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:['class']});
 window.addEventListener('hashchange',()=>{if(location.hash==='#fs-plan25')renderPlan()});window.addEventListener('storage',renderPlan);setTimeout(renderPlan,0);window.FS_PLAN25={data:PLAN,render:renderPlan};
})();


/* SOURCE BLOCK: fs-v4-engine */

(function(){
 const TEAMS=new Set(['Atalanta','Bologna','Cagliari','Como','Fiorentina','Frosinone','Genoa','Inter','Juventus','Lazio','Lecce','Milan','Monza','Napoli','Parma','Roma','Sassuolo','Torino','Udinese','Venezia']);
 const OUT_IDS=new Set(['p-ondrejka-parma']);
 const ROLE_CAP={P:3,D:8,C:8,A:6}, ROLE_BUDGET={P:38,D:92,C:145,A:225}, TOTAL=25;
 let current=null;
 function cards(){return [...document.querySelectorAll('.purchase-box')].map(c=>({c,id:c.dataset.playerId,name:c.dataset.name,team:c.dataset.team,role:c.dataset.role,score:+c.dataset.score,ideal:+c.dataset.ideal,base:+c.dataset.baseMax}));}
 function truth(p){if(!p||!TEAMS.has(p.team)||OUT_IDS.has(p.id))return {ok:false,status:'OUT_OF_SERIE_A'};return {ok:true,status:'ACTIVE'};}
 function applyTruth(){cards().forEach(p=>{const t=truth(p);const arts=[...document.querySelectorAll('[href="#'+p.id+'"], [data-player-id="'+p.id+'"]')];if(!t.ok){arts.forEach(el=>el.classList?.add('truth-blocked'));const box=p.c;if(box&&!box.querySelector('.truth-badge'))box.querySelector('b')?.insertAdjacentHTML('afterend','<span class="truth-badge">OUT</span>')}})}
 function st(){return window.FS_AUCTION_ENGINE?.state?.()||null;}
 function remaining(role,S){return cards().filter(p=>p.role===role&&truth(p).ok&&!S.soldIds.has(p.id));}
 function roleSpent(role,S){return S.mine.filter(x=>x.role===role).reduce((a,x)=>a+x.price,0);}
 function roleTarget(role,S){const remainingRoleSlots=S.managerStates.ME.needs[role], remSlots=S.slots||1;const dynamic=Math.round(S.budget*(remainingRoleSlots/Math.max(1,remSlots)));return Math.max(remainingRoleSlots,Math.round((ROLE_BUDGET[role]*.55)+(dynamic*.45)));}
 function modifierProxy(p){if(p.role!=='D')return 'N/A';const v=Math.max(0,Math.min(100,Math.round((p.score-45)*1.4)));return v>=70?'ALTO '+v:v>=45?'MEDIO '+v:'BASSO '+v;}
 function cleanSheetProxy(p){if(p.role!=='P')return 'N/A';const v=Math.max(0,Math.min(100,Math.round((p.score-40)*1.45)));return v>=70?'ALTO '+v:v>=45?'MEDIO '+v:'BASSO '+v;}
 function topTier(p,role,S){const arr=remaining(role,S).sort((a,b)=>b.score-a.score);const cut=Math.max(1,Math.ceil(arr.length*.10));return arr.slice(0,cut).some(x=>x.id===p.id);}
 function roleScarcity(role,S){const demand=Object.values(S.managerStates).reduce((z,m)=>z+m.needs[role],0), supply=Math.max(1,remaining(role,S).length);return {ratio:demand/supply,demand,supply};}
 function oppLearning(S){const tx=S.tx.filter(x=>x.owner!=='ME');const by={};for(const t of tx){const p=cards().find(x=>x.id===t.id);if(!p)continue;(by[t.owner]??=[]).push({t,p,over:t.price-Math.max(1,p.ideal)});}let best={name:'—',score:0,over:0};for(const [o,a] of Object.entries(by)){const m=S.managerStates[o];const avg=a.reduce((z,x)=>z+x.over,0)/a.length;const freq=a.length;const sc=Math.round(Math.min(100,35*(m.spent/500)+35*Math.min(1,freq/8)+30*Math.max(0,Math.min(1,(avg+10)/35))));if(sc>best.score)best={name:(m.name||o),score:sc,over:avg};}const roleCounts={P:0,D:0,C:0,A:0};tx.forEach(x=>roleCounts[x.role]++);const hot=Object.entries(roleCounts).sort((a,b)=>b[1]-a[1])[0];return {...best,hot:hot?.[0]||'—'};}
 function costOfPass(p,S){const alt=remaining(p.role,S).filter(x=>x.id!==p.id).sort((a,b)=>b.score-a.score).slice(0,5);if(!alt.length)return {score:100,label:'CRITICO',best:null};const best=alt[0], gap=Math.max(0,p.score-best.score);const sc=roleScarcity(p.role,S);const top=topTier(p,p.role,S)?20:0;const v=Math.round(Math.min(100,gap*2.5+Math.min(45,sc.ratio*22)+top));return {score:v,label:v>=75?'ALTO':v>=50?'MEDIO':'BASSO',best};}
 function v4Max(p,S){if(!truth(p).ok||S.managerStates.ME.needs[p.role]<=0)return 0;const old=window.FS_AUCTION_ENGINE.liveMax(p,S);const op=window.FS_AUCTION_ENGINE.opponentPressure(p,S), cop=costOfPass(p,S), sc=roleScarcity(p.role,S);let mult=1;const needTop=Math.max(0,3-S.top);if(topTier(p,p.role,S)&&needTop>0)mult+=Math.min(.12,.035*needTop+.025*Math.max(0,sc.ratio-1));if(S.top>=3&&topTier(p,p.role,S))mult-=.05;if(cop.score>=75)mult+=.05;else if(cop.score<35)mult-=.03;mult+=Math.min(.05,op.pressure/2000);const target=roleTarget(p.role,S), spent=roleSpent(p.role,S);if(spent>target)mult-=Math.min(.08,(spent-target)/Math.max(1,target)*.12);if(p.role==='D')mult+=Math.max(0,(Math.min(100,Math.max(0,(p.score-45)*1.4))-55)/1000);if(p.role==='P')mult+=Math.max(0,(Math.min(100,Math.max(0,(p.score-40)*1.45))-55)/1200);const safe=Math.max(1,S.budget-Math.max(0,(S.slots-1)));return Math.max(1,Math.min(safe,Math.round(old*mult)));}
 function utility(p,S){const lm=v4Max(p,S), op=window.FS_AUCTION_ENGINE.opponentPressure(p,S), cop=costOfPass(p,S), sc=roleScarcity(p.role,S);const value=p.score/Math.max(1,p.ideal);const budgetFit=Math.max(-1,Math.min(1,(roleTarget(p.role,S)-roleSpent(p.role,S))/Math.max(1,roleTarget(p.role,S))));return value*26 + p.score*.55 + cop.score*.18 + Math.min(20,sc.ratio*8) - op.pressure*.06 + budgetFit*8 + (topTier(p,p.role,S)&&S.top<3?12:0) + (lm>=p.ideal?4:-4);}
 function candidates(S,role='AUTO'){let arr=cards().filter(p=>truth(p).ok&&!S.soldIds.has(p.id)&&S.managerStates.ME.needs[p.role]>0);if(role!=='AUTO')arr=arr.filter(p=>p.role===role);return arr.sort((a,b)=>utility(b,S)-utility(a,S));}
 function pivots(p,S){return candidates(S,p.role).filter(x=>x.id!==p.id).slice(0,4);}
 function decision(price,p,lm){if(!price)return 'WAIT';if(price<=p.ideal)return 'BUY';if(price<=lm)return 'WAIT';return 'PASS';}
 function render(){applyTruth();const S=st();if(!S)return;const role=document.getElementById('v4-role')?.value||'AUTO';const arr=candidates(S,role);current=arr[0]||null;document.getElementById('v4-budget').textContent=S.budget;document.getElementById('v4-slots').textContent=S.slots;document.getElementById('v4-fire').textContent=S.fire;document.getElementById('v4-top').textContent=S.top+'/3';document.getElementById('v4-reserve').textContent=S.reserve;
 ['P','D','C','A'].forEach(r=>document.getElementById('v4-b'+r.toLowerCase()).textContent=roleTarget(r,S));
 if(!current){document.getElementById('v4-player').textContent='ROSA COMPLETA / NESSUN TARGET';return;}const p=current,lm=v4Max(p,S),op=window.FS_AUCTION_ENGINE.opponentPressure(p,S),cop=costOfPass(p,S),sc=roleScarcity(p.role,S),learn=oppLearning(S),price=parseInt(document.getElementById('v4-price').value||'0',10),dec=decision(price,p,lm);document.getElementById('v4-player').textContent=p.name;document.getElementById('v4-meta').textContent=p.team+' · '+p.role+' · Score '+p.score.toFixed(1);document.getElementById('v4-ideal').textContent=p.ideal;document.getElementById('v4-base').textContent=p.base;document.getElementById('v4-live').textContent=lm;document.getElementById('v4-after').textContent=price?Math.max(0,S.budget-price):S.budget;const d=document.getElementById('v4-decision');d.textContent=dec;d.className='v4-decision '+dec.toLowerCase();document.getElementById('v4-opp').textContent=op.pressure+'/100 · '+op.activeCount+'/9';document.getElementById('v4-cop').textContent=cop.label+' '+cop.score+'/100';const topRisk=(S.top>=3?'COPERTO':S.topLeft<=Math.max(0,3-S.top)+2?'CRITICO':'APERTO');document.getElementById('v4-toprisk').textContent=topRisk;document.getElementById('v4-scarcity').textContent=sc.ratio.toFixed(2)+' ('+sc.demand+'/'+sc.supply+')';document.getElementById('v4-mod').textContent=modifierProxy(p);document.getElementById('v4-cs').textContent=cleanSheetProxy(p);document.getElementById('v4-role-delta').textContent=(roleSpent(p.role,S)-roleTarget(p.role,S));document.getElementById('v4-threat-name').textContent=learn.name;document.getElementById('v4-threat').textContent=learn.score+'/100';document.getElementById('v4-overpay').textContent=(learn.over>=0?'+':'')+learn.over.toFixed(1)+' cr';document.getElementById('v4-hotrole').textContent=learn.hot;const pv=pivots(p,S);document.getElementById('v4-pivots').innerHTML=pv.map((x,i)=>'<div class="v4-pivot"><div><b>'+String(i+1)+'. '+x.name+'</b><small>'+x.team+' · Score '+x.score.toFixed(1)+' · ideale '+x.ideal+'</small></div><span>MAX '+v4Max(x,S)+'</span></div>').join('')||'<div class="v4-note">Nessuna alternativa disponibile.</div>';
 // upgrade every visible live-decision band with V4 boundary
 document.querySelectorAll('.purchase-box').forEach(c=>{const q={id:c.dataset.playerId,name:c.dataset.name,team:c.dataset.team,role:c.dataset.role,score:+c.dataset.score,ideal:+c.dataset.ideal,base:+c.dataset.baseMax};if(!truth(q).ok)return;const ml=v4Max(q,S),inp=c.querySelector('.purchase-price'),v=parseInt(inp?.value||'0',10),de=decision(v,q,ml),box=c.querySelector('.live-decision');if(box){box.innerHTML='V4 · IDEALE <strong>'+q.ideal+'</strong> · MAX LIVE <strong class="live-max">'+ml+'</strong> · <span class="live-reason">'+de+'</span>';box.dataset.currentDecision=de;}});
 }
 document.addEventListener('click',e=>{const b=e.target.closest('.purchase-btn');if(!b)return;const c=b.closest('.purchase-box');const q=c?{id:c.dataset.playerId,name:c.dataset.name,team:c.dataset.team,role:c.dataset.role,score:+c.dataset.score,ideal:+c.dataset.ideal,base:+c.dataset.baseMax}:null;if(q&&!truth(q).ok){e.preventDefault();e.stopImmediatePropagation();alert('DATA TRUTH GATE: giocatore non acquistabile nel perimetro Serie A.');}},true);document.addEventListener('input',e=>{if(e.target.id==='v4-price'||e.target.id==='v4-role'||e.target.classList.contains('purchase-price'))setTimeout(render,0)});document.addEventListener('change',e=>{if(e.target.id==='v4-role')render()});document.getElementById('v4-refresh')?.addEventListener('click',render);document.getElementById('v4-reset')?.addEventListener('click',()=>{if(confirm('Azzero tutta l’asta registrata su questo dispositivo?')){localStorage.removeItem('fs_gold_auction_v393');localStorage.removeItem('fs_gold_auction_v390');localStorage.removeItem('fs_gold_auction_v389');location.reload();}});window.addEventListener('hashchange',()=>{if(location.hash==='#v4-cockpit')render()});window.addEventListener('storage',render);setTimeout(render,50);window.FS_V4={truth,v4Max,costOfPass,candidates,pivots,render};
})();


/* SOURCE BLOCK: v409-js */

(function(){
 "use strict";
 function cards(){
   return Array.from(document.querySelectorAll(".purchase-box")).map(function(c){
     return {id:c.dataset.playerId,name:c.dataset.name,team:c.dataset.team,role:c.dataset.role,
             score:+c.dataset.score||0,ideal:+c.dataset.ideal||0,base:+c.dataset.baseMax||0};
   });
 }
 function qOwned(S,role){
   return (S.mine||[]).filter(function(x){return x.role===role;}).map(function(x){
     var p=cards().find(function(z){return z.id===x.id;}); return p?p.score:0;
   }).sort(function(a,b){return b-a;});
 }
 function teamEnv(p){
   var arr=cards().filter(function(x){return x.team===p.team && (x.role==="P"||x.role==="D");});
   if(!arr.length)return 50;
   arr.sort(function(a,b){return b.score-a.score;});
   var top=arr.slice(0,Math.min(6,arr.length));
   return Math.max(25,Math.min(90,Math.round(top.reduce(function(z,x){return z+x.score;},0)/top.length)));
 }
 function modifierMarginal(p,S){
   if(p.role!=="D")return {score:0,delta:0,label:"N/A",fit:"N/A"};
   var owned=qOwned(S,"D"), fourth=owned.length>=4?owned[3]:0;
   var quality=Math.max(0,Math.min(100,Math.round((p.score-42)*1.55)));
   var marginal=Math.max(0,p.score-fourth);
   var rosterNeed=Math.max(0,4-owned.length);
   var score=Math.round(Math.min(100,quality*.62+Math.min(30,marginal*1.8)+rosterNeed*6));
   var delta=score>=80?4:score>=65?3:score>=50?2:score>=35?1:0;
   if(owned.length>=5 && fourth>=p.score)delta=Math.max(0,delta-2);
   return {score:score,delta:delta,label:(score>=70?"ALTO ":score>=45?"MEDIO ":"BASSO ")+score+"/100",fit:owned.length<4?"COSTRUZIONE":"MARGINALE"};
 }
 function cleanSheetMarginal(p,S){
   if(p.role!=="P")return {score:0,delta:0,label:"N/A",fit:"N/A"};
   var env=teamEnv(p), owned=qOwned(S,"P");
   var starterNeed=Math.max(0,1-owned.length);
   var quality=Math.max(0,Math.min(100,Math.round((p.score-38)*1.5)));
   var score=Math.round(Math.min(100,quality*.55+env*.35+starterNeed*10));
   var delta=score>=80?4:score>=65?3:score>=50?2:score>=35?1:0;
   if(owned.length>=2)delta=Math.max(0,delta-2);
   return {score:score,delta:delta,label:(score>=70?"ALTO ":score>=45?"MEDIO ":"BASSO ")+score+"/100",fit:owned.length===0?"TITOLARE":"BLOCCO"};
 }
 function apply(){
   if(!window.FS_V4||!window.FS_AUCTION_ENGINE)return;
   var oldMax=window.FS_V4.v4Max;
   function max409(p,S){
     var v=oldMax(p,S), m=modifierMarginal(p,S), c=cleanSheetMarginal(p,S);
     var safe=Math.max(1,S.budget-Math.max(0,S.slots-1));
     return Math.max(0,Math.min(safe,v+m.delta+c.delta));
   }
   window.FS_V4.v4Max=max409;
   window.FS_V4.modifierMarginal=modifierMarginal;
   window.FS_V4.cleanSheetMarginal=cleanSheetMarginal;
   var oldRender=window.FS_V4.render;
   window.FS_V4.render=function(){
     oldRender();
     var S=window.FS_AUCTION_ENGINE.state();
     var name=document.getElementById("v4-player")?.textContent||"";
     var p=cards().find(function(x){return x.name===name;});
     if(!p)return;
     var m=modifierMarginal(p,S), c=cleanSheetMarginal(p,S);
     var a=document.getElementById("v409-mod"),b=document.getElementById("v409-cs"),
         f=document.getElementById("v409-fit"),d=document.getElementById("v409-dmax");
     if(a)a.textContent=m.label;if(b)b.textContent=c.label;
     if(f)f.textContent=(p.role==="D"?m.fit:p.role==="P"?c.fit:"N/A");
     if(d)d.textContent="+"+(m.delta+c.delta);
     var live=document.getElementById("v4-live"); if(live)live.textContent=max409(p,S);
   };
   setTimeout(window.FS_V4.render,80);
 }
 if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",apply,{once:true});else setTimeout(apply,0);
})();


/* SOURCE BLOCK: v410-js */

(function(){
 "use strict";
 function all(){
   return Array.from(document.querySelectorAll(".purchase-box")).map(function(c){
     return {id:c.dataset.playerId,name:c.dataset.name,team:c.dataset.team,role:c.dataset.role,
             score:+c.dataset.score||0,ideal:+c.dataset.ideal||0,base:+c.dataset.baseMax||0};
   });
 }
 function bestReplacement(p,S){
   var arr=all().filter(function(x){return x.role===p.role && x.id!==p.id && !S.soldIds.has(x.id);})
     .sort(function(a,b){return (b.score/Math.max(1,b.ideal))-(a.score/Math.max(1,a.ideal));});
   return arr[0]||null;
 }
 function rosterDelta(p,price,S){
   var r=bestReplacement(p,S);
   var repl=r?r.score:Math.max(35,p.score*.70);
   var qualityGap=p.score-repl;
   var costPenalty=Math.max(0,price-p.ideal)*.65;
   var fitBonus=0;
   if(window.FS_V4.modifierMarginal)fitBonus+=window.FS_V4.modifierMarginal(p,S).delta*2.5;
   if(window.FS_V4.cleanSheetMarginal)fitBonus+=window.FS_V4.cleanSheetMarginal(p,S).delta*2.5;
   var scarcity=window.FS_AUCTION_ENGINE.opponentPressure(p,S).scarcity||1;
   return qualityGap*1.9 + fitBonus + Math.max(0,scarcity-1)*5 - costPenalty;
 }
 function shadowMax(p,S){
   var safe=Math.max(1,S.budget-Math.max(0,S.slots-1));
   var lo=1,hi=safe,best=1;
   while(lo<=hi){
     var m=Math.floor((lo+hi)/2);
     if(rosterDelta(p,m,S)>=0){best=m;lo=m+1;}else hi=m-1;
   }
   var live=window.FS_V4.v4Max(p,S);
   return Math.max(1,Math.min(safe,Math.max(live,best)));
 }
 function apply(){
   if(!window.FS_V4||!window.FS_AUCTION_ENGINE)return;
   window.FS_V4.bestReplacement=bestReplacement;
   window.FS_V4.rosterDelta=rosterDelta;
   window.FS_V4.shadowMax=shadowMax;
   var prev=window.FS_V4.v4Max;
   window.FS_V4.v4Max=function(p,S){return Math.min(Math.max(1,S.budget-Math.max(0,S.slots-1)),Math.max(prev(p,S),shadowMax(p,S)));};
   var r0=window.FS_V4.render;
   window.FS_V4.render=function(){
     r0();
     var S=window.FS_AUCTION_ENGINE.state(), name=document.getElementById("v4-player")?.textContent||"";
     var p=all().find(function(x){return x.name===name;}); if(!p)return;
     var price=parseInt(document.getElementById("v4-price")?.value||"0",10)||p.ideal, repl=bestReplacement(p,S);
     var a=document.getElementById("v410-shadowmax"),d=document.getElementById("v410-delta"),rr=document.getElementById("v410-repl");
     if(a)a.textContent=shadowMax(p,S);
     if(d)d.textContent=rosterDelta(p,price,S).toFixed(1);
     if(rr)rr.textContent=repl?(repl.name+" · "+repl.score.toFixed(1)):"NESSUNO";
     var live=document.getElementById("v4-live");if(live)live.textContent=window.FS_V4.v4Max(p,S);
   };
   setTimeout(window.FS_V4.render,100);
 }
 if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",apply,{once:true});else setTimeout(apply,0);
})();


/* SOURCE BLOCK: v411-js */

(function(){
 "use strict";
 function survival(p,S){
   var op=window.FS_AUCTION_ENGINE.opponentPressure(p,S), supply=Math.max(1,op.supply||1), demand=Math.max(0,op.totalDemand||0);
   var scarcity=Math.min(1,demand/supply);
   var pressure=(op.pressure||0)/100;
   var premium=Math.max(0,Math.min(1,(p.score-75)/20));
   var prob=Math.round(100*(1-(.48*scarcity+.32*pressure+.20*premium)));
   return Math.max(5,Math.min(95,prob));
 }
 function apply(){
   if(!window.FS_V4)return;
   window.FS_V4.pivotSurvival=survival;
   var rp=window.FS_V4.pivots;
   window.FS_V4.pivots=function(p,S){
     return rp(p,S).map(function(x){x.survival=survival(x,S);return x;})
       .sort(function(a,b){return (b.survival+b.score)-(a.survival+a.score);});
   };
   var rr=window.FS_V4.render;
   window.FS_V4.render=function(){
     rr();
     var S=window.FS_AUCTION_ENGINE.state();
     var name=document.getElementById("v4-player")?.textContent||"";
     var cards=Array.from(document.querySelectorAll(".purchase-box"));
     var c=cards.find(function(z){return z.dataset.name===name;}); if(!c)return;
     var p={id:c.dataset.playerId,name:c.dataset.name,team:c.dataset.team,role:c.dataset.role,score:+c.dataset.score,ideal:+c.dataset.ideal,base:+c.dataset.baseMax};
     var pv=window.FS_V4.pivots(p,S);
     var el=document.getElementById("v411-survival");
     if(el)el.textContent=pv.length?(pv[0].name+" "+pv[0].survival+"%"):"nessun pivot";
     var box=document.getElementById("v4-pivots");
     if(box)box.innerHTML=pv.slice(0,4).map(function(x,i){
       return '<div class="v4-pivot"><div><b>'+(i+1)+'. '+x.name+'</b><small>'+x.team+' · Score '+x.score.toFixed(1)+' · survival '+x.survival+'%</small></div><span>MAX '+window.FS_V4.v4Max(x,S)+'</span></div>';
     }).join("")||'<div class="v4-note">Nessuna alternativa disponibile.</div>';
   };
   setTimeout(window.FS_V4.render,120);
 }
 if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",apply,{once:true});else setTimeout(apply,0);
})();


/* SOURCE BLOCK: v412-js */

(function(){
 "use strict";
 function learn(S){
   var groups={};
   (S.tx||[]).filter(function(t){return t.owner!=="ME";}).forEach(function(t){(groups[t.owner]||(groups[t.owner]=[])).push(t);});
   var best={owner:"—",name:"—",score:0,over:0,role:"—"};
   Object.keys(groups).forEach(function(o){
     var a=groups[o], m=S.managerStates[o], roleCount={P:0,D:0,C:0,A:0}, over=0;
     a.forEach(function(t){
       roleCount[t.role]=(roleCount[t.role]||0)+1;
       var c=document.querySelector('.purchase-box[data-player-id="'+t.id+'"]');
       var ideal=c?(+c.dataset.ideal||1):1; over+=t.price-ideal;
     });
     var avg=a.length?over/a.length:0;
     var hot=Object.keys(roleCount).sort(function(x,y){return roleCount[y]-roleCount[x];})[0]||"—";
     var need=m.needs[hot]||0;
     var sc=Math.round(Math.min(100,30*Math.min(1,a.length/7)+25*Math.min(1,m.spent/350)+25*Math.max(0,Math.min(1,(avg+6)/25))+20*Math.min(1,need/6)));
     if(sc>best.score)best={owner:o,name:m.name||o,score:sc,over:avg,role:hot};
   });
   return best;
 }
 function apply(){
   if(!window.FS_V4)return;
   window.FS_V4.behavioralOpponent=learn;
   var r=window.FS_V4.render;
   window.FS_V4.render=function(){
     r();
     var S=window.FS_AUCTION_ENGINE.state(),x=learn(S);
     var a=document.getElementById("v412-rival"),b=document.getElementById("v412-over"),c=document.getElementById("v412-role"),d=document.getElementById("v412-threat");
     if(a)a.textContent=x.name;if(b)b.textContent=(x.over>=0?"+":"")+x.over.toFixed(1);
     if(c)c.textContent=x.role;if(d)d.textContent=x.score+"/100";
   };
   setTimeout(window.FS_V4.render,120);
 }
 if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",apply,{once:true});else setTimeout(apply,0);
})();


/* SOURCE BLOCK: v413-js */

(function(){
 "use strict";
 var KEY="fs_gold_auction_v393", HIST="fs_gold_v413_history", FUT="fs_gold_v413_future";
 function tx(){try{return JSON.parse(localStorage.getItem(KEY)||"[]");}catch(e){return [];}}
 function put(a){localStorage.setItem(KEY,JSON.stringify(a));}
 function hist(){try{return JSON.parse(localStorage.getItem(HIST)||"[]");}catch(e){return [];}}
 function fut(){try{return JSON.parse(localStorage.getItem(FUT)||"[]");}catch(e){return [];}}
 function setStatus(t){var e=document.getElementById("v413-status");if(e)e.textContent=t;}
 function snapshot(){return {build:"V4.0.13",ts:new Date().toISOString(),tx:tx()};}
 function download(){
   var blob=new Blob([JSON.stringify(snapshot(),null,2)],{type:"application/json"});
   var a=document.createElement("a");a.href=URL.createObjectURL(blob);
   var d=new Date(),z=function(n){return String(n).padStart(2,"0");};
   a.download="FS_ASTA_"+d.getFullYear()+z(d.getMonth()+1)+z(d.getDate())+"_"+z(d.getHours())+z(d.getMinutes())+".json";
   document.body.appendChild(a);a.click();setTimeout(function(){URL.revokeObjectURL(a.href);a.remove();},0);
   setStatus("Backup esportato.");
 }
 function undo(){
   var a=tx();if(!a.length){setStatus("Niente da annullare.");return;}
   var h=hist(),f=fut();h.push(a.slice(0,-1));f.push(a);localStorage.setItem(HIST,JSON.stringify(h.slice(-30)));localStorage.setItem(FUT,JSON.stringify(f.slice(-30)));put(a.slice(0,-1));location.reload();
 }
 function redo(){
   var f=fut();if(!f.length){setStatus("Niente da ripristinare.");return;}
   var next=f.pop(),h=hist();h.push(tx());localStorage.setItem(HIST,JSON.stringify(h.slice(-30)));localStorage.setItem(FUT,JSON.stringify(f));put(next);location.reload();
 }
 function restore(file){
   var r=new FileReader();r.onload=function(){
     try{var x=JSON.parse(r.result);if(!x||!Array.isArray(x.tx))throw new Error("Formato non valido");
       localStorage.setItem(HIST,JSON.stringify((hist().concat([tx()])).slice(-30)));localStorage.removeItem(FUT);put(x.tx);location.reload();
     }catch(e){setStatus("Restore fallito: "+e.message);}
   };r.readAsText(file);
 }
 function bind(){
   document.getElementById("v413-save")?.addEventListener("click",download);
   document.getElementById("v413-undo")?.addEventListener("click",undo);
   document.getElementById("v413-redo")?.addEventListener("click",redo);
   document.getElementById("v413-file")?.addEventListener("change",function(e){if(e.target.files&&e.target.files[0])restore(e.target.files[0]);});
 }
 if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",bind,{once:true});else bind();
})();


/* SOURCE BLOCK: v414-js */

(function(){
 "use strict";
 function bind(){
   if(!window.FS_V4)return;
   var r=window.FS_V4.render;
   window.FS_V4.render=function(){
     r();
     var S=window.FS_AUCTION_ENGINE.state(), name=document.getElementById("v4-player")?.textContent||"";
     var c=Array.from(document.querySelectorAll(".purchase-box")).find(function(z){return z.dataset.name===name;});
     if(!c)return;
     var p={id:c.dataset.playerId,name:c.dataset.name,team:c.dataset.team,role:c.dataset.role,score:+c.dataset.score,ideal:+c.dataset.ideal,base:+c.dataset.baseMax};
     var pv=window.FS_V4.pivots(p,S),learn=window.FS_V4.behavioralOpponent?window.FS_V4.behavioralOpponent(S):null;
     var top=document.getElementById("v414-top"),th=document.getElementById("v414-threat"),pi=document.getElementById("v414-pivot"),su=document.getElementById("v414-survival");
     if(top)top.textContent=S.top+"/3 "+(S.top>=3?"COPERTO":"APERTO");
     if(th)th.textContent=learn?(learn.score+"/100"):"—";
     if(pi)pi.textContent=pv[0]?pv[0].name:"—";
     if(su)su.textContent=pv[0]&&pv[0].survival!=null?(pv[0].survival+"%"):"—";
   };
   setTimeout(window.FS_V4.render,150);
 }
 if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",bind,{once:true});else setTimeout(bind,0);
})();


/* SOURCE BLOCK: v4016-ddt-js */

(function(){
  "use strict";
  var EVENTS = {
    "Spence": {pct:8, action:"BUY moderato", confidence:.99},
    "Stones": {pct:5, action:"BUY/HOLD", confidence:.96},
    "Leao": {pct:-8, action:"WAIT", confidence:.97},
    "Ramos G.": {pct:7, action:"BUY", confidence:.96},
    "Atta": {pct:3, action:"HOLD", confidence:.94},
    "Joao Mario": {pct:2, action:"HOLD", confidence:.91},
    "Adams A.": {pct:10, action:"BUY forte", confidence:.97},
    "Davis K.": {pct:6, action:"BUY", confidence:.96},
    "Dybala": {pct:4, action:"HOLD/BUY", confidence:.96},
    "Cristante": {pct:3, action:"HOLD", confidence:.94},
    "Comuzzo": {pct:-5, action:"WAIT", confidence:.95},
    "Gimenez": {pct:-18, action:"PASS", confidence:.92}
  };

  function safeCeiling(S){
    return Math.max(1, S.budget - Math.max(0, S.slots-1));
  }

  function apply(){
    if(!window.FS_V4 || !window.FS_AUCTION_ENGINE) return;

    var previous = window.FS_V4.v4Max;
    window.FS_V4.newsOverlay = function(p){
      return EVENTS[p.name] || null;
    };

    window.FS_V4.v4Max = function(p,S){
      var base = previous(p,S);
      var ev = EVENTS[p.name];
      if(!ev) return base;
      var adjusted = Math.round(base * (1 + ev.pct/100));
      return Math.max(1, Math.min(safeCeiling(S), adjusted));
    };

    var oldRender = window.FS_V4.render;
    window.FS_V4.render = function(){
      oldRender();
      var S = window.FS_AUCTION_ENGINE.state();
      var name = document.getElementById("v4-player")?.textContent || "";
      var card = Array.from(document.querySelectorAll(".purchase-box")).find(function(c){return c.dataset.name===name;});
      if(!card) return;
      var p = {
        id:card.dataset.playerId,name:card.dataset.name,team:card.dataset.team,role:card.dataset.role,
        score:+card.dataset.score||0,ideal:+card.dataset.ideal||0,base:+card.dataset.baseMax||0
      };
      var live = document.getElementById("v4-live");
      if(live) live.textContent = window.FS_V4.v4Max(p,S);
    };

    setTimeout(window.FS_V4.render, 180);
  }

  if(document.readyState==="loading"){
    document.addEventListener("DOMContentLoaded", apply, {once:true});
  } else {
    setTimeout(apply,0);
  }
})();


/* SOURCE BLOCK: fs-v419-atomic-engine */

(function(){
 "use strict";
 const AKEY="fs_v419_atomic_ledger", PKEY="fs_v419_pending_control", TXKEY="fs_gold_auction_v393";
 const ROLE_CAP={P:3,D:8,C:8,A:6};
 let pending=null;
 function read(k,d){try{return JSON.parse(localStorage.getItem(k)||JSON.stringify(d));}catch(e){return d;}}
 function write(k,v){localStorage.setItem(k,JSON.stringify(v));}
 function cards(){const m=new Map();document.querySelectorAll('.purchase-box').forEach(c=>{if(!m.has(c.dataset.playerId))m.set(c.dataset.playerId,c)});return [...m.values()];}
 const PLAYER_COUNT=cards().length;
 function pObj(c){return c?{id:c.dataset.playerId,name:c.dataset.name,team:c.dataset.team,role:c.dataset.role,score:+c.dataset.score,ideal:+c.dataset.ideal,base:+c.dataset.baseMax}:null;}
 function txRaw(){return read(TXKEY,[])}
 function sig(a){return JSON.stringify(a.map(x=>[x.id,x.owner,x.price,x.ts]))}
 function planSummary(S){
   const plan=window.FS_PLAN25?.data;if(!plan)return null;let done=0,active=0,critical=0,fallback=0;
   for(const role of ['P','D','C','A'])for(const [,ids] of plan[role]||[]){const owned=ids.map(id=>S.tx.find(x=>x.id===id)).find(x=>x&&x.owner==='ME');if(owned){done++;continue}let ix=-1;for(let i=0;i<ids.length;i++){if(!S.soldIds.has(ids[i])){ix=i;break}}if(ix<0)critical++;else{active++;if(ix>0)fallback++;}}
   return {done,active,critical,fallback};
 }
 function snap(p,S){
   if(!S)return null;const rs={};for(const r of ['P','D','C','A'])rs[r]=cards().filter(c=>c.dataset.role===r&&!S.soldIds.has(c.dataset.playerId)).length;
   let op=null,maxLive=null,pivots=[];try{if(p){op=window.FS_AUCTION_ENGINE.opponentPressure(p,S);maxLive=window.FS_V4?.v4Max?window.FS_V4.v4Max(p,S):window.FS_AUCTION_ENGINE.liveMax(p,S);pivots=(window.FS_V4?.pivots?.(p,S)||[]).slice(0,4).map(x=>({id:x.id,name:x.name,score:x.score,max:window.FS_V4.v4Max(x,S)}));}}catch(e){}
   const managers={};for(const [k,m] of Object.entries(S.managerStates||{}))managers[k]={budget:m.budget,slots:m.slots,needs:m.needs,safeAny:m.safeAny,premiumCount:m.premiumCount};
   const topStatus=S.top>=3?'COPERTO':S.topLeft<=Math.max(0,3-S.top)+2?'CRITICO':'APERTO';
   return {ts:new Date().toISOString(),budget:S.budget,slots:S.slots,fire:S.fire,spent:S.spent,leagueBudget:S.leagueBudget,leagueSlots:S.leagueSlots,remainingPool:PLAYER_COUNT-S.tx.length,roleSupply:rs,top:S.top,topLeft:S.topLeft,topProtection:topStatus,managers,player:p?{id:p.id,name:p.name,role:p.role}:null,maxLive,opponent:op?{pressure:op.pressure,activeCount:op.activeCount,scarcity:op.scarcity,totalDemand:op.totalDemand,supply:op.supply}:null,pivots,plan25:planSummary(S)};
 }
 function invariant(S){if(!S)return {ok:false,errors:['NO_STATE']};const e=[];if(S.budget<0)e.push('ME_BUDGET_NEG');if(S.leagueBudget<0)e.push('LEAGUE_BUDGET_NEG');if(S.slots<0)e.push('ME_SLOTS_NEG');if(S.leagueSlots<0)e.push('LEAGUE_SLOTS_NEG');for(const [o,m] of Object.entries(S.managerStates||{})){if(m.budget<0)e.push(o+'_BUDGET_NEG');if(m.slots<0)e.push(o+'_SLOTS_NEG');for(const r of ['P','D','C','A'])if((m.roles?.[r]||0)>ROLE_CAP[r])e.push(o+'_'+r+'_OVER')}const ids=S.tx.map(x=>x.id);if(new Set(ids).size!==ids.length)e.push('DUPLICATE_PLAYER');return {ok:!e.length,errors:e};}
 function ledger(){return read(AKEY,[])}
 function add(rec){const a=ledger();a.push(rec);write(AKEY,a.slice(-1000));render();}
 function finalizePurchase(){
   if(!pending)return;const nowTx=txRaw();if(sig(nowTx)===pending.txSig){pending=null;return}const p=pending.player,S=window.FS_AUCTION_ENGINE?.state?.();if(!S){pending=null;return}const t=S.tx.find(x=>x.id===p.id),post=snap(p,S),inv=invariant(S),a=ledger();
   add({seq:a.length+1,txId:'TX-'+String(a.length+1).padStart(4,'0'),type:'PURCHASE',ts:t?.ts||new Date().toISOString(),result:t?.owner==='ME'?'VINTO':'PERSO',transaction:t||null,pre:pending.pre,post,invariant:inv,observations:[{phase:'PRE',state:pending.pre},{phase:'POST',state:post}]});
   try{window.FS_PLAN25?.render?.();window.FS_V4?.render?.();}catch(e){} pending=null;
 }
 function captureControl(type){const S=window.FS_AUCTION_ENGINE?.state?.();write(PKEY,{type,ts:new Date().toISOString(),pre:S?snap(null,S):null,txSig:sig(txRaw())});}
 function finalizeControl(){const q=read(PKEY,null);if(!q)return;localStorage.removeItem(PKEY);setTimeout(()=>{const S=window.FS_AUCTION_ENGINE?.state?.();if(!S)return;const post=snap(null,S);if(q.txSig===sig(txRaw()))return;const inv=invariant(S),a=ledger();add({seq:a.length+1,txId:'CTL-'+String(a.length+1).padStart(4,'0'),type:q.type,ts:new Date().toISOString(),transaction:null,pre:q.pre,post,invariant:inv,observations:[{phase:'PRE',state:q.pre},{phase:'POST',state:post}]});},60);}
 function dl(name,text,type){const b=new Blob([text],{type}),a=document.createElement('a');a.href=URL.createObjectURL(b);a.download=name;document.body.appendChild(a);a.click();setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove()},0)}
 function exportJson(){dl('FS_V419_ATOMIC_LEDGER_'+new Date().toISOString().slice(0,10)+'.json',JSON.stringify({build:'V4.0.19',registry:PLAYER_COUNT,ledger:ledger()},null,2),'application/json')}
 function exportCsv(){const a=ledger(),h=['seq','txId','type','ts','player','role','owner','price','budgetPre','budgetPost','slotsPre','slotsPost','poolPost','maxLivePre','oppPre','topPre','topPost','planDonePost','invariant'];const rows=[h.join(',')];for(const r of a){const t=r.transaction||{},pre=r.pre||{},post=r.post||{};rows.push([r.seq,r.txId,r.type,r.ts,t.name||'',t.role||'',t.owner||'',t.price??'',pre.budget??'',post.budget??'',pre.slots??'',post.slots??'',post.remainingPool??'',pre.maxLive??'',pre.opponent?.pressure??'',pre.topProtection??'',post.topProtection??'',post.plan25?.done??'',r.invariant?.ok?'PASS':'FAIL'].map(x=>'"'+String(x).replaceAll('"','""')+'"').join(','));}dl('FS_V419_ATOMIC_LEDGER_'+new Date().toISOString().slice(0,10)+'.csv',rows.join('\n'),'text/csv')}
 function render(){const a=ledger(),commits=a.filter(x=>x.type==='PURCHASE').length,obs=a.reduce((z,x)=>z+(x.observations?.length||0),0),S=window.FS_AUCTION_ENGINE?.state?.(),fails=a.filter(x=>x.invariant&&!x.invariant.ok).length;const q=id=>document.getElementById(id);if(q('v419-commits'))q('v419-commits').textContent=commits;if(q('v419-obs'))q('v419-obs').textContent=Math.min(obs,500)+' / 500';if(q('v419-pool'))q('v419-pool').textContent=S?PLAYER_COUNT-S.tx.length:PLAYER_COUNT;if(q('v419-fails'))q('v419-fails').textContent=fails;const gate=q('v419-replay-gate');if(gate){gate.textContent=obs>=500?'READY FOR REAL REPLAY':'COLLECTING '+obs+'/500';gate.className=obs>=500?'fs-gate-pass':'fs-gate-pending'}const last=q('v419-last');if(last){const z=a.slice(-12).reverse();last.innerHTML=z.length?z.map(r=>{const t=r.transaction||{};return '<div class="v419-row"><span>'+String(r.seq).padStart(3,'0')+'</span><span><b>'+r.type+(t.name?' · '+t.name:'')+'</b><small>'+(t.owner||'')+(t.price?' · '+t.price+' cr':'')+' · obs '+(r.observations?.length||0)+'</small></span><span class="'+(r.invariant?.ok?'v419-ok':'v419-bad')+'">'+(r.invariant?.ok?'PASS':'FAIL')+'</span></div>'}).join(''):'<div class="v419-row"><span>—</span><span><b>Nessun commit registrato</b><small>Il collector partirà al primo VINTO/PERSO.</small></span><span class="v419-warn">COLLECTING</span></div>';}}
 document.addEventListener('click',e=>{const b=e.target.closest('.purchase-btn');if(b){const c=b.closest('.purchase-box'),p=pObj(c),S=window.FS_AUCTION_ENGINE?.state?.();pending={player:p,pre:S?snap(p,S):null,txSig:sig(txRaw())};setTimeout(finalizePurchase,0);return}if(e.target.closest('#v413-undo'))captureControl('UNDO');else if(e.target.closest('#v413-redo'))captureControl('REDO');},true);
 document.addEventListener('change',e=>{if(e.target.id==='v413-file'&&e.target.files?.length)captureControl('RESTORE')},true);
 document.getElementById('v419-json')?.addEventListener('click',exportJson);document.getElementById('v419-csv')?.addEventListener('click',exportCsv);document.getElementById('v419-refresh')?.addEventListener('click',()=>{try{window.FS_PLAN25?.render?.();window.FS_V4?.render?.()}catch(e){}render()});document.getElementById('v419-clear-audit')?.addEventListener('click',()=>{if(confirm('Azzero solo il ledger V4.0.19? Lo stato dell’asta non verrà cancellato.')){localStorage.removeItem(AKEY);render()}});
 window.addEventListener('hashchange',()=>{if(location.hash==='#v419-ledger')render()});window.addEventListener('storage',render);finalizeControl();setTimeout(render,120);window.FS_V419={ledger,snapshot:snap,invariant,render,exportJson,exportCsv};
})();


/* SOURCE BLOCK: fs-v420-exact-runtime */

(function(){'use strict';
 function cardPlayer(c){return c?{id:c.dataset.playerId,name:c.dataset.name,team:c.dataset.team,role:c.dataset.role,score:+c.dataset.score||0,ideal:+c.dataset.ideal||0,base:+c.dataset.baseMax||0}:null}
 function exactMax(p,S){if(!p||!S||!window.FS_V4?.v4Max)return 0;var safe=Math.max(0,S.budget-Math.max(0,S.slots-1));var raw=Number(window.FS_V4.v4Max(p,S));if(!Number.isFinite(raw))return 0;return Math.max(0,Math.min(safe,raw));}
 function decide(price,p,S){var m=exactMax(p,S);if(m<=0)return 'PASS';if(price<=p.ideal)return 'BUY';if(price<=m)return 'WAIT';return 'PASS';}
 function paint(c){var p=cardPlayer(c),S=window.FS_AUCTION_ENGINE?.state?.();if(!p||!S)return;var m=exactMax(p,S),inp=c.querySelector('.purchase-price'),price=parseFloat(inp?.value||'0'),d=c.querySelector('.live-decision');if(d){let x=d.querySelector('.v420-exact');if(!x){x=document.createElement('span');x.className='v420-exact';d.appendChild(x)}x.textContent='MAX ESATTO '+m.toFixed(2)+' · '+(price>0?decide(price,p,S):'—')+' · SAFE '+Math.max(0,S.budget-Math.max(0,S.slots-1)).toFixed(2);}}
 document.addEventListener('input',function(e){if(e.target.classList.contains('purchase-price'))paint(e.target.closest('.purchase-box'))},true);
 document.addEventListener('click',function(e){var b=e.target.closest('.purchase-btn.win-btn');if(!b)return;var c=b.closest('.purchase-box'),p=cardPlayer(c),S=window.FS_AUCTION_ENGINE?.state?.(),price=parseFloat(c.querySelector('.purchase-price')?.value||'0');if(!p||!S||!price)return;var m=exactMax(p,S);if(price>m+1e-9){e.preventDefault();e.stopImmediatePropagation();c.classList.add('v420-blocked');setTimeout(()=>c.classList.remove('v420-blocked'),900);alert('PASS: '+price.toFixed(2)+' supera MAX BID ESATTO '+m.toFixed(2)+'. Transazione VINTO bloccata.');}},true);
 function apply(){if(!window.FS_V4||!window.FS_AUCTION_ENGINE)return;window.FS_V4.exactMax=exactMax;window.FS_V4.exactDecision=decide;document.querySelectorAll('.purchase-box').forEach(paint);var old=window.FS_V4.render;if(!old.__v420){var w=function(){old();document.querySelectorAll('.purchase-box').forEach(paint);var S=window.FS_AUCTION_ENGINE.state(),name=document.getElementById('v4-player')?.textContent||'',c=[...document.querySelectorAll('.purchase-box')].find(z=>z.dataset.name===name);if(c){var p=cardPlayer(c),m=exactMax(p,S),price=parseFloat(document.getElementById('v4-price')?.value||'0'),d=document.getElementById('v4-decision');var live=document.getElementById('v4-live');if(live)live.textContent=m.toFixed(2);if(d&&price>0){var q=decide(price,p,S);d.textContent=q;d.className='v4-decision '+q.toLowerCase();}}};w.__v420=true;window.FS_V4.render=w;setTimeout(w,80)}}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',apply,{once:true});else setTimeout(apply,0);window.FS_V420={exactMax,decide};
})();


/* SOURCE BLOCK: fs-v421-real-rules */

(function(){'use strict';function status(p,S){var m=window.FS_V4?.modifierMarginal?.(p,S)||{score:0,delta:0,label:'N/A'},c=window.FS_V4?.cleanSheetMarginal?.(p,S)||{score:0,delta:0,label:'N/A'};return {modifier:m,cleanSheet:c,deltaMax:(m.delta||0)+(c.delta||0),inputClass:'MODEL_DERIVED',ruleEffect:'REAL_MAX_MARGINAL'}}window.FS_V421={status};})();


/* SOURCE BLOCK: fs-v422-recovery-plus */

(function(){'use strict';const TX='fs_gold_auction_v393',LED='fs_v419_atomic_ledger',H='fs_v422_history',F='fs_v422_future',SCHEMA='FS_ASTA_STATE_V4_0_22';
 function rd(k,d){try{return JSON.parse(localStorage.getItem(k)||JSON.stringify(d))}catch(e){return d}}function wr(k,v){localStorage.setItem(k,JSON.stringify(v))}
 function hash(x){var s=JSON.stringify(x),h=2166136261;for(var i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619)}return ('00000000'+(h>>>0).toString(16)).slice(-8)}
 function bundle(){var b={schema:SCHEMA,build:'V4.0.22',ts:new Date().toISOString(),registry:document.querySelectorAll('.purchase-box').length,tx:rd(TX,[]),ledger:rd(LED,[])};b.checksum=hash({tx:b.tx,ledger:b.ledger,registry:b.registry});return b}
 function apply(b){if(!b||b.schema!==SCHEMA||!Array.isArray(b.tx)||!Array.isArray(b.ledger))throw new Error('Bundle non valido');if(b.registry!==document.querySelectorAll('.purchase-box').length)throw new Error('Registry incompatibile');var ck=hash({tx:b.tx,ledger:b.ledger,registry:b.registry});if(ck!==b.checksum)throw new Error('Checksum non valido');wr(TX,b.tx);wr(LED,b.ledger)}
 function snapHistory(){var a=rd(H,[]);a.push(bundle());wr(H,a.slice(-50));wr(F,[])}
 document.addEventListener('click',function(e){if(e.target.closest('.purchase-btn'))snapHistory()},true);
 function dl(){var b=bundle(),a=document.createElement('a'),blob=new Blob([JSON.stringify(b,null,2)],{type:'application/json'});a.href=URL.createObjectURL(blob);a.download='FS_ASTA_BACKUP_'+new Date().toISOString().replace(/[:.]/g,'-')+'.json';document.body.appendChild(a);a.click();setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove()},0);document.getElementById('v422-status').textContent='Backup completo creato · checksum '+b.checksum}
 function undo(){var a=rd(H,[]);if(!a.length)return document.getElementById('v422-status').textContent='Nessun undo disponibile.';var f=rd(F,[]);f.push(bundle());var b=a.pop();wr(H,a);wr(F,f.slice(-50));apply(b);location.reload()}
 function redo(){var f=rd(F,[]);if(!f.length)return document.getElementById('v422-status').textContent='Nessun redo disponibile.';var a=rd(H,[]);a.push(bundle());var b=f.pop();wr(H,a.slice(-50));wr(F,f);apply(b);location.reload()}
 function restore(file){var r=new FileReader();r.onload=function(){try{var b=JSON.parse(r.result);snapHistory();apply(b);location.reload()}catch(e){document.getElementById('v422-status').textContent='Restore bloccato: '+e.message}};r.readAsText(file)}
 function bind(){document.getElementById('v422-save')?.addEventListener('click',dl);document.getElementById('v422-undo')?.addEventListener('click',undo);document.getElementById('v422-redo')?.addEventListener('click',redo);document.getElementById('v422-file')?.addEventListener('change',e=>{if(e.target.files?.[0])restore(e.target.files[0])})}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',bind,{once:true});else bind();window.FS_V422={bundle,apply,undo,redo};
})();


/* SOURCE BLOCK: v4231-ios-runtime-js */

(function(){
"use strict";
const AKEY="fs_v419_atomic_ledger";
const PFX="[V4.0.23.1]";
const $=id=>document.getElementById(id);

function setState(id,text,cls){
  const e=$(id); if(!e)return; e.textContent=text; e.className=cls||"";
}
function msg(text,kind){
  const e=$("v4231-msg"); if(!e)return;
  e.textContent=text;
  e.style.color=kind==="fail"?"var(--red)":kind==="pass"?"var(--green)":"var(--muted)";
}
function canLocalStorage(){
  try{
    const k="__fs4231_test__"+Date.now();
    localStorage.setItem(k,"1");
    const ok=localStorage.getItem(k)==="1";
    localStorage.removeItem(k);
    return ok;
  }catch(e){return false;}
}
function runtimeCheck(){
  setState("v4231-js","PASS","v4231-pass");
  const ls=canLocalStorage();
  setState("v4231-ls",ls?"PASS":"FAIL",ls?"v4231-pass":"v4231-fail");
  const share=!!(navigator.share);
  setState("v4231-share",share?"AVAILABLE":"NO","v4231-pass");
  const blob=!!(window.Blob && window.URL && URL.createObjectURL);
  setState("v4231-blob",blob?"AVAILABLE":"NO",blob?"v4231-pass":"v4231-fail");
  const badge=document.querySelector('[data-v4231="runtime-badge"]');
  if(badge){
    badge.textContent=ls?"RUNTIME PASS":"VIEWER LIMITATO";
    badge.style.color=ls?"var(--green)":"var(--red)";
  }
  msg(ls?"Runtime JavaScript + storage operativo. Testa ora i 4 comandi del Ledger.":"Viewer limitato: JavaScript gira, ma localStorage è bloccato. Il Ledger non può essere certificato qui.",ls?"pass":"fail");
  return {ls,share,blob};
}
function getLedger(){
  try{return JSON.parse(localStorage.getItem(AKEY)||"[]")}catch(e){return []}
}
function exportPayload(kind){
  const a=getLedger();
  if(kind==="json"){
    return {
      name:"FS_V4231_ATOMIC_LEDGER_"+new Date().toISOString().slice(0,10)+".json",
      mime:"application/json",
      text:JSON.stringify({build:"V4.0.23.1",registry:document.querySelectorAll(".purchase-box[data-player-id]").length,ledger:a},null,2)
    };
  }
  const h=["seq","txId","type","ts","player","role","owner","price","budgetPre","budgetPost","slotsPre","slotsPost","poolPost","invariant"];
  const rows=[h.join(",")];
  for(const r of a){
    const t=r.transaction||{},pre=r.pre||{},post=r.post||{};
    rows.push([r.seq,r.txId,r.type,r.ts,t.name||"",t.role||"",t.owner||"",t.price??"",pre.budget??"",post.budget??"",pre.slots??"",post.slots??"",post.remainingPool??"",r.invariant?.ok?"PASS":"FAIL"]
      .map(x=>'"'+String(x).replace(/"/g,'""')+'"').join(","));
  }
  return {name:"FS_V4231_ATOMIC_LEDGER_"+new Date().toISOString().slice(0,10)+".csv",mime:"text/csv",text:rows.join("\n")};
}
function openFallback(payload,why){
  const sec=$("v4231-export-fallback"), ta=$("v4231-export-text"), ti=$("v4231-export-title"), no=$("v4231-export-note");
  if(!sec||!ta)return;
  ti.textContent="Export · "+payload.name;
  no.textContent=why||"Export aperto in modalità compatibile.";
  ta.value=payload.text;
  sec.classList.add("open");
}
async function shareFile(payload){
  if(!navigator.share)return false;
  try{
    const f=new File([payload.text],payload.name,{type:payload.mime});
    if(navigator.canShare && navigator.canShare({files:[f]})){
      await navigator.share({files:[f],title:payload.name});
      return true;
    }
  }catch(e){}
  try{
    await navigator.share({title:payload.name,text:payload.text});
    return true;
  }catch(e){}
  return false;
}
function blobDownload(payload){
  try{
    const b=new Blob([payload.text],{type:payload.mime});
    const u=URL.createObjectURL(b);
    const a=document.createElement("a");
    a.href=u;a.download=payload.name;a.rel="noopener";
    document.body.appendChild(a);a.click();
    setTimeout(()=>{URL.revokeObjectURL(u);a.remove()},500);
    return true;
  }catch(e){return false}
}
async function exportCompat(kind){
  const payload=exportPayload(kind);
  msg("Export "+kind.toUpperCase()+" in corso…","warn");
  if(await shareFile(payload)){
    msg("Export "+kind.toUpperCase()+": Share Sheet aperto.","pass");return;
  }
  if(blobDownload(payload)){
    // On iOS embedded viewers click can be ignored. Keep fallback accessible anyway.
    setTimeout(()=>openFallback(payload,"Se il download non compare nel viewer iOS, usa COPIA CONTENUTO o CONDIVIDI TESTO."),300);
    msg("Export preparato. Se il viewer blocca il download, usa il pannello fallback.","pass");return;
  }
  openFallback(payload,"Download/Share non disponibili in questo viewer. Usa copia manuale.");
  msg("Viewer limitato: export aperto nel fallback testuale.","fail");
}
function recalcCompat(){
  let ok=true, err="";
  try{
    window.FS_PLAN25?.render?.();
    window.FS_V4?.render?.();
    window.FS_V419?.render?.();
  }catch(e){ok=false;err=e.message||String(e)}
  const ts=new Date().toLocaleTimeString("it-IT");
  msg(ok?"RICALCOLA PASS · "+ts:"RICALCOLA FAIL · "+err,ok?"pass":"fail");
}
function clearAuditCompat(){
  try{
    const before=getLedger().length;
    localStorage.removeItem(AKEY);
    const after=getLedger().length;
    window.FS_V419?.render?.();
    msg(after===0?"AUDIT AZZERATO · "+before+" record rimossi":"AZZERA FAIL",after===0?"pass":"fail");
  }catch(e){msg("AZZERA FAIL · "+(e.message||e),"fail")}
}
async function copyText(){
  const ta=$("v4231-export-text"); if(!ta)return;
  try{
    await navigator.clipboard.writeText(ta.value);
    msg("Contenuto copiato negli appunti.","pass");
  }catch(e){
    ta.focus();ta.select();
    try{document.execCommand("copy");msg("Contenuto copiato negli appunti.","pass")}
    catch(_){msg("Copia automatica bloccata: seleziona manualmente il testo.","fail")}
  }
}
async function shareText(){
  const ta=$("v4231-export-text"), ti=$("v4231-export-title"); if(!ta)return;
  if(navigator.share){
    try{await navigator.share({title:ti?.textContent||"FS Export",text:ta.value});msg("Share Sheet aperto.","pass");return}catch(e){}
  }
  msg("Share Sheet non disponibile: usa COPIA CONTENUTO.","fail");
}
function bind(){
  runtimeCheck();
  const j=$("v419-json"), c=$("v419-csv"), r=$("v419-refresh"), z=$("v419-clear-audit");
  if(j){const n=j.cloneNode(true);j.replaceWith(n);n.addEventListener("click",e=>{e.preventDefault();exportCompat("json")})}
  if(c){const n=c.cloneNode(true);c.replaceWith(n);n.addEventListener("click",e=>{e.preventDefault();exportCompat("csv")})}
  if(r){const n=r.cloneNode(true);r.replaceWith(n);n.addEventListener("click",e=>{e.preventDefault();recalcCompat()})}
  if(z){const n=z.cloneNode(true);z.replaceWith(n);n.addEventListener("click",e=>{e.preventDefault();clearAuditCompat()})}
  $("v4231-export-close")?.addEventListener("click",()=>$("v4231-export-fallback")?.classList.remove("open"));
  $("v4231-copy")?.addEventListener("click",copyText);
  $("v4231-share-text")?.addEventListener("click",shareText);
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",bind,{once:true});else setTimeout(bind,0);
})();
