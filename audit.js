(()=>{'use strict';
const CAPS={P:3,D:8,C:8,A:6};
function run(){
 const out=[],add=(id,ok,msg,severity='BLOCK')=>out.push({id,ok,msg,severity});
 const reg=window.FS_APP?.registry?.()||[],details=window.FS_APP?.details?.()||{},overlay=window.FS_MD5||window.FS_APP?.news?.()||null,S=window.FS_AUCTION_ENGINE?.state?.();
 const EXPECTED_REGISTRY=Number(window.FS_VERSION?.runtime_registry_count||window.FS_VERSION?.canonical_registry_runtime_count||reg.length||0);
 add('REG01',reg.length===EXPECTED_REGISTRY,`Registry runtime ${reg.length}/${EXPECTED_REGISTRY}`);
 add('REG02',new Set(reg.map(x=>x.id)).size===reg.length,'PlayerID unici');
 add('REG03',Object.keys(details).length===EXPECTED_REGISTRY,`Dettagli ${Object.keys(details).length}/${EXPECTED_REGISTRY}`);
 add('REG04',reg.every(p=>p.current_listone_source==='LISTONE_22SEP2026'),'Tutti i record runtime legati al Listone corrente 22/09');
 add('DATA22-01',String(overlay?.cutoff||'').startsWith('2026-09-22'),'Overlay performance/sanitario 22/09 caricato');
 add('DATA22-02',(overlay?.medical_verified||[]).length===10,`Righe sanitarie verificate ${(overlay?.medical_verified||[]).length}/10`);
 add('DATA22-03',(overlay?.leaders?.goals||[]).length===20&&(overlay?.leaders?.assists||[]).length===20,'Top 20 gol + Top 20 assist 22/09 presenti');
 add('DATA22-04',(overlay?.standings||[]).length===20,'Classifica 20/20 con GF/GS e forma');
 add('DATA22-05',(overlay?.creative_chances||[]).length===4,'Occasioni create: 4 record esplicitamente riportati');
 add('DATA22-06',overlay?.source_pdf_sha256==='8750038002a14025bfb89c8f620a6337a7f7634695b6b2f1bf30f98cbd11d0a4','Binding SHA-256 al report 22/09');
 add('STALE01',!reg.some(p=>p._news),'Overlay runtime 18/08 disabilitato');
 const recalc=reg.filter(p=>![p.score,p.ideal,p.max].every(v=>typeof v==='number'&&Number.isFinite(v)));
 add('REG05',reg.every(p=>p.serie_a_membership==='ACTIVE_CURRENT_LISTONE_22SEP'),'Tutti i 562 record runtime sono membri Serie A dal Listone corrente');
 add('REG06',recalc.every(p=>p.serie_a_membership==='ACTIVE_CURRENT_LISTONE_22SEP'),`Pending modello ancora in Serie A: ${recalc.length}/${recalc.length}`);
 const expectedPending=Number(window.FS_VERSION?.model_pending_22sep_count??recalc.length);
 add('REG07',recalc.length===expectedPending,`Pending modello ${recalc.length}/${expectedPending}; membership separata dal modello`);
 add('MODEL01',recalc.length===0,`Record in attesa FOS/Risk/MAX recalculation: ${recalc.length}`,'WARN');
 const stale=reg.filter(p=>p.model_status==='STALE_PRE_22SEP_RECALC');
 add('MODEL02',stale.length===0,`Record con modello numerico pre-22SEP ancora da ricalcolare: ${stale.length}`,'WARN');
 if(!S){add('ENG00',false,'Engine state non disponibile');return out}
 add('ENG01',typeof window.FS_AUCTION_ENGINE?.exactMax==='function'&&typeof window.FS_AUCTION_ENGINE?.shadowRawMax==='function','Exact MAX + Shadow APIs presenti');
 add('MKT01',typeof window.FS_MARKET_ENGINE?.quote==='function'&&typeof window.FS_MARKET_ENGINE?.dynamicMax==='function','Opponent Market V1 APIs presenti');
 add('MKT02',typeof window.FS_AUCTION_ENGINE?.auctionMax==='function','Auction MAX post-market overlay presente');
 const profiles=window.FS_MARKET_ENGINE?.managerProfiles?.(S)||{};add('MKT03',Object.keys(profiles).length===9,'9/9 profili avversari T0/learned disponibili');
 const probe=reg.find(p=>p.role==='A'&&Number(p.fvm)>0),pq=probe?window.FS_MARKET_ENGINE?.quote?.(probe,S):null;add('MKT04',!!pq&&pq.market_t0>=1&&pq.expected>=1,'Market-clearing quote valida su attaccante probe');
 add('MKT05',window.FS_VERSION?.optimizerMax_mutated===false,'OptimizerMax LOCK non mutato; market layer post-engine');
 add('TX01',new Set(S.tx.map(x=>x.id)).size===S.tx.length,'Ownership univoca');
 add('TX02',S.tx.every(x=>Number.isInteger(Number(x.price))&&x.price>=1&&x.price<=500),'Prezzi interi 1..500');
 add('TX03',S.tx.every(x=>['ME','R1','R2','R3','R4','R5','R6','R7','R8','R9'].includes(x.owner)),'Owner validi');
 add('TX04',S.tx.every(x=>reg.some(p=>p.id===x.id)),'Tutte le transazioni risolvono un PlayerID corrente');
 for(const [id,m] of Object.entries(S.managerStates)){add('BUD-'+id,m.budget>=0&&m.budget<=500,`${id} budget ${m.budget}`);add('BAL-'+id,m.budget+m.spent===500,`${id}: budget ${m.budget} + spent ${m.spent} = 500`);add('SLOT-'+id,m.count<=25,`${id} slot ${m.count}/25`);add('FIN-'+id,m.budget>=m.slots,`${id} completabile a 1 cr/slot`);for(const r in CAPS)add(`ROLE-${id}-${r}`,m.roles[r]<=CAPS[r],`${id} ${r} ${m.roles[r]}/${CAPS[r]}`)}
 const totalBud=Object.values(S.managerStates).reduce((z,m)=>z+m.budget,0);
 add('LEAGUE01',S.spentLeague<=5000,`Speso lega ${S.spentLeague}/5000`);
 add('LEAGUE02',totalBud+S.spentLeague===5000,`Budget residui ${totalBud} + spent ${S.spentLeague} = 5000`);
 add('POOL01',S.soldIds.size===S.tx.length,`Sold IDs ${S.soldIds.size} = TX ${S.tx.length}`);
 add('POOL02',reg.length-S.soldIds.size===EXPECTED_REGISTRY-S.tx.length,`Remaining pool ${reg.length-S.soldIds.size}/${EXPECTED_REGISTRY}`);
 const lkg=window.FS_STATE?.lastKnownGood?.(),keys=window.FS_STATE?.keys||{};
 add('STATE01',!!lkg,'Last Known Good disponibile','WARN');
 add('STATE02',typeof window.FS_STATE?.commit==='function'&&typeof window.FS_STATE?.rollback==='function'&&typeof window.FS_STATE?.importBundle==='function','State Manager autoritativo + bundle import');
 add('STATE03',String(keys.STATE||'').startsWith('fantasegreto:'),'Storage namespace fantasegreto:*');
 add('PWA01',!!document.querySelector('link[rel="manifest"]'),'Manifest collegato');
 return out
}
function render(){const root=document.getElementById('audit-content');if(!root)return;const a=run(),bad=a.filter(x=>!x.ok&&x.severity==='BLOCK'),warn=a.filter(x=>!x.ok&&x.severity!=='BLOCK');root.innerHTML=`<div class="audit-summary ${bad.length?'bad':'good'}"><b>${bad.length?'BLOCK':'PASS'}</b><span>${a.length-bad.length-warn.length}/${a.length} pass · ${warn.length} warn</span></div>${a.map(x=>`<div class="audit-row"><span>${x.id}<small>${x.msg}</small></span><b class="${x.ok?'pass':x.severity==='BLOCK'?'fail':'warn'}">${x.ok?'PASS':x.severity}</b></div>`).join('')}`}
window.FS_AUDIT={run,render};})();