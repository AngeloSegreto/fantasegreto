(()=>{'use strict';
const CAPS={P:3,D:8,C:8,A:6},BASE_REGISTRY=492;
function run(){
 const out=[],add=(id,ok,msg,severity='BLOCK')=>out.push({id,ok,msg,severity});
 const reg=window.FS_APP?.registry?.()||[],details=window.FS_APP?.details?.()||{},news=window.FS_APP?.news?.()||window.FS_NEWS||null,S=window.FS_AUCTION_ENGINE?.state?.();
 const newsAdds=(news?.events||[]).filter(e=>e.canonical_write==='ADD').length,expected=BASE_REGISTRY+newsAdds;
 add('REG01',reg.length===expected,`Registry effettivo ${reg.length}/${expected} · base ${BASE_REGISTRY} + canonical ADD ${newsAdds}`);
 add('REG02',new Set(reg.map(x=>x.id)).size===reg.length,'PlayerID unici');
 add('REG03',Object.keys(details).length>=reg.length,`Dettagli ${Object.keys(details).length} / registry ${reg.length}`);
 const knownBroken=reg.filter(p=>p.registry_status==='CANONICAL_SOURCE_QUOTE'&&(!(p.quote>0)||!(p.fvm>0)));
 add('REGQ01',knownBroken.length===0,knownBroken.length?`Quote canoniche strutturate mancanti: ${knownBroken.map(x=>x.name).join(', ')}`:'Quote canoniche strutturate coerenti');
 add('NEWS01',!!news&&news.canonical_registry_writes===1&&news.calibration_writes===0,'FS NEWS 18/08 19:45 · canonical writes 1 · calibration writes 0');
 const vic=reg.find(p=>p.id==='p-vicario-juventus'),dg=reg.find(p=>p.id==='p-di-gregorio-juventus'),luc=reg.find(p=>p.id==='p-lucumi-bologna'),kel=reg.find(p=>p.id==='p-kelly-l-juventus');
 add('NEWS02',!!vic&&vic.team==='Juventus'&&Number(vic.quote)===16&&Number(vic.fvm)===55,'Vicario canonical JUV · QI16/FVM55');
 add('NEWS03',!!dg&&Number(dg.fvm)===10&&dg._valuation?.hard_cap===true,'Di Gregorio FVM10 + derived hard cap');
 add('NEWS04',!!luc&&luc.team==='Bologna'&&luc._news?.context_team==='Juventus','Lucumì: canonical Bologna preservato, Juventus solo contesto tattico');
 add('NEWS05',!!kel&&Number(kel.fvm)===10&&Number(kel._news?.applied_max_pct)===-7,'Kelly FVM10 · overlay MAX -7% conservativo');
 if(!S){add('ENG00',false,'Engine state non disponibile');return out}
 add('ENG01',typeof window.FS_AUCTION_ENGINE?.exactMax==='function'&&typeof window.FS_AUCTION_ENGINE?.shadowRawMax==='function','Exact MAX + Shadow raw/guarded APIs presenti');
 const newsPlayers=[vic,dg,luc,kel].filter(Boolean),shadowChecks=newsPlayers.map(p=>window.FS_AUCTION_ENGINE.parityLayers(p,S)),shadowOk=shadowChecks.every(x=>x.shadow_guarded>=x.mod_cs&&x.shadow_guarded-x.mod_cs<=x.shadow_delta_cap&&x.shadow_delta_cap<=8);
 add('ENG02',shadowOk,'Shadow safety guard: uplift ≤ min(8 cr, 8% MOD+CS) sui record delta');
 add('ENG03',newsPlayers.every(p=>{const m=window.FS_AUCTION_ENGINE.exactMax(p,S);return Number.isFinite(m)&&m>=0&&m<=Math.max(0,S.budget-Math.max(0,S.slots-1))}),'Exact MAX entro safe ceiling');
 add('TX01',new Set(S.tx.map(x=>x.id)).size===S.tx.length,'Ownership univoca');
 add('TX02',S.tx.every(x=>Number.isInteger(Number(x.price))&&x.price>=1&&x.price<=500),'Prezzi interi 1..500');
 add('TX03',S.tx.every(x=>['ME','R1','R2','R3','R4','R5','R6','R7','R8','R9'].includes(x.owner)),'Owner validi');
 add('TX04',S.tx.every(x=>reg.some(p=>p.id===x.id)),'Tutte le transazioni risolvono un PlayerID corrente');
 for(const [id,m] of Object.entries(S.managerStates)){add('BUD-'+id,m.budget>=0&&m.budget<=500,`${id} budget ${m.budget}`);add('BAL-'+id,m.budget+m.spent===500,`${id}: budget ${m.budget} + spent ${m.spent} = 500`);add('SLOT-'+id,m.count<=25,`${id} slot ${m.count}/25`);add('FIN-'+id,m.budget>=m.slots,`${id} completabile a 1 cr/slot`);for(const r in CAPS)add(`ROLE-${id}-${r}`,m.roles[r]<=CAPS[r],`${id} ${r} ${m.roles[r]}/${CAPS[r]}`)}
 const totalBud=Object.values(S.managerStates).reduce((z,m)=>z+m.budget,0);
 add('LEAGUE01',S.spentLeague<=5000,`Speso lega ${S.spentLeague}/5000`);add('LEAGUE02',totalBud+S.spentLeague===5000,`Budget residui ${totalBud} + spent ${S.spentLeague} = 5000`);add('POOL01',S.soldIds.size===S.tx.length,`Sold IDs ${S.soldIds.size} = TX ${S.tx.length}`);add('POOL02',reg.length-S.soldIds.size===expected-S.tx.length,`Remaining pool ${reg.length-S.soldIds.size}/${expected}`);
 const lkg=window.FS_STATE?.lastKnownGood?.(),keys=window.FS_STATE?.keys||{},migration=keys.MIGRATION?(()=>{try{return JSON.parse(localStorage.getItem(keys.MIGRATION)||'null')}catch{return null}})():null;
 add('STATE01',!!lkg,'Last Known Good disponibile','WARN');add('STATE02',typeof window.FS_STATE?.commit==='function'&&typeof window.FS_STATE?.rollback==='function'&&typeof window.FS_STATE?.importBundle==='function','State Manager autoritativo + bundle import');add('STATE03',String(keys.STATE||'').startsWith('fantasegreto:'),'Storage namespace fantasegreto:*');add('STATE04',!migration||migration.status==='PASS',migration?`Migrazione legacy ${migration.status}`:'Nessuna migrazione legacy registrata','WARN');
 add('PWA01',!!document.querySelector('link[rel="manifest"]'),'Manifest collegato');return out
}
function render(){const root=document.getElementById('audit-content');if(!root)return;const a=run(),bad=a.filter(x=>!x.ok&&x.severity==='BLOCK'),warn=a.filter(x=>!x.ok&&x.severity!=='BLOCK');root.innerHTML=`<div class="audit-summary ${bad.length?'bad':'good'}"><b>${bad.length?'BLOCK':'PASS'}</b><span>${a.length-bad.length-warn.length}/${a.length} pass · ${warn.length} warn</span></div>${a.map(x=>`<div class="audit-row"><span>${x.id}<small>${x.msg}</small></span><b class="${x.ok?'pass':x.severity==='BLOCK'?'fail':'warn'}">${x.ok?'PASS':x.severity}</b></div>`).join('')}`}
window.FS_AUDIT={run,render};})();
