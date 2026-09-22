(()=>{'use strict';
const CAPS={P:3,D:8,C:8,A:6},EXPECTED_REGISTRY=531;
function run(){
 const out=[],add=(id,ok,msg,severity='BLOCK')=>out.push({id,ok,msg,severity});
 const reg=window.FS_APP?.registry?.()||[],details=window.FS_APP?.details?.()||{},overlay=window.FS_MD5||window.FS_APP?.news?.()||null,S=window.FS_AUCTION_ENGINE?.state?.();
 add('REG01',reg.length===EXPECTED_REGISTRY,`Registry runtime ${reg.length}/${EXPECTED_REGISTRY}`);
 add('REG02',new Set(reg.map(x=>x.id)).size===reg.length,'PlayerID unici');
 add('REG03',Object.keys(details).length===EXPECTED_REGISTRY,`Dettagli ${Object.keys(details).length}/${EXPECTED_REGISTRY}`);
 add('REG04',reg.every(p=>p.official_id&&p.canonical_source==='FANTACALCIO_OFFICIAL_07SEP2026'),'Binding official_id + canonical source presente');
 add('DATA22-01',String(overlay?.cutoff||'').startsWith('2026-09-22'),'Overlay performance/sanitario 22/09 caricato');
 add('DATA22-02',(overlay?.medical_verified||[]).length===6,`Medical verificati ${(overlay?.medical_verified||[]).length}/6`);
 add('DATA22-03',(overlay?.leaders?.goals||[]).length===4&&(overlay?.leaders?.assists||[]).length===3,'Leader gol/assist 22/09 presenti');
 add('STALE01',!reg.some(p=>p._news),'Overlay runtime 18/08 disabilitato');
 const recalc=reg.filter(p=>![p.score,p.ideal,p.max].every(v=>Number.isFinite(Number(v))));
 add('MODEL01',recalc.length===0,`Record in attesa FOS/Risk/MAX recalculation: ${recalc.length}`,'WARN');
 if(!S){add('ENG00',false,'Engine state non disponibile');return out}
 add('ENG01',typeof window.FS_AUCTION_ENGINE?.exactMax==='function'&&typeof window.FS_AUCTION_ENGINE?.shadowRawMax==='function','Exact MAX + Shadow APIs presenti');
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