(()=>{'use strict';
const CAPS={P:3,D:8,C:8,A:6};
function run(){
 const out=[],add=(id,ok,msg,severity='BLOCK')=>out.push({id,ok,msg,severity});
 const reg=window.FS_APP?.registry?.()||[],E=window.FS_AUCTION_ENGINE,S=E?.state?.(),ST=window.FS_STATE;
 add('RC7REG01',reg.length===531,'Registry 531/531');
 add('RC7REG02',new Set(reg.map(x=>x.id)).size===reg.length,'PlayerID unici');
 add('RC7REG03',reg.every(p=>['P','D','C','A'].includes(p.role)),'Ruoli validi');
 add('RC7DATA01',reg.every(p=>Number.isFinite(Number(p.score))),'FOS V2 numerico');
 add('RC7DATA02',reg.every(p=>Number.isFinite(Number(p.max))&&p.max>=1),'MAX base medical-adjusted numerico');
 add('RC7ENG01',!!E&&typeof E.exactMax==='function'&&typeof E.parityLayers==='function','Engine parity API presente');
 add('RC7ENG02',!!E&&typeof E.opponentPressure==='function'&&typeof E.pivots==='function','Opponent pressure + pivots presenti');
 add('RC7ENG03',!!E&&typeof E.modifierMarginal==='function'&&typeof E.cleanSheetMarginal==='function','Modifier + clean sheet presenti');
 add('RC7STATE01',!!ST&&typeof ST.exportBundle==='function'&&typeof ST.importBundle==='function','FS_STATE_V2 bundle API');
 if(!S){add('RC7STATE00',false,'Engine state non disponibile');return out}
 add('RC7TX01',new Set(S.tx.map(x=>x.id)).size===S.tx.length,'Ownership univoca');
 add('RC7TX02',S.tx.every(x=>reg.some(p=>p.id===x.id)),'TX risolvono registry corrente');
 add('RC7BUD01',Object.values(S.managerStates).every(m=>m.budget>=0&&m.budget<=500),'Budget manager validi');
 add('RC7FIN01',Object.values(S.managerStates).every(m=>m.budget>=m.slots),'Completamento a 1 cr finanziabile');
 for(const [id,m] of Object.entries(S.managerStates))for(const r in CAPS)add('RC7ROLE-'+id+'-'+r,m.roles[r]<=CAPS[r],id+' '+r+' '+m.roles[r]+'/'+CAPS[r]);
 const sample=reg.filter(p=>Number.isFinite(Number(p.max))&&Number.isFinite(Number(p.ideal))).slice(0,80);
 add('RC7MAX01',sample.every(p=>{const m=E.exactMax(p,S);return Number.isFinite(m)&&m>=0&&m<=Math.max(0,S.budget-Math.max(0,S.slots-1))}),'Exact MAX entro safe ceiling su sample 80');
 const sh=sample.slice(0,30).map(p=>E.parityLayers(p,S));
 add('RC7SH01',sh.every(x=>x.shadow_guarded>=x.mod_cs&&x.shadow_guarded-x.mod_cs<=x.shadow_delta_cap&&x.shadow_delta_cap<=8),'Shadow guard coerente sample 30');
 const mig=window.FS_RC7_MIGRATION?.run?.();
 add('RC7MIG01',!mig||['PASS','SKIP_NO_SOURCE','SKIP_ALREADY_DONE'].includes(mig.status),'Migrazione RC7.1→StateV2 '+(mig?.status||'N/A'),mig?.status==='BLOCK_UNRESOLVED'?'BLOCK':'WARN');
 return out;
}
function summary(){const a=run(),bad=a.filter(x=>!x.ok&&x.severity==='BLOCK'),warn=a.filter(x=>!x.ok&&x.severity!=='BLOCK');return{status:bad.length?'BLOCK':'PASS',checks:a.length,pass:a.filter(x=>x.ok).length,block:bad.length,warn:warn.length,results:a}}
window.FS_RC7_AUDIT={run,summary};
})();