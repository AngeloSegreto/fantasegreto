(()=>{'use strict';
const SRC='FS_RC7_1_STATE_V1',FLAG='fantasegreto:rc7:migration:rc71-to-v2';
const nk=s=>String(s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
function run(){
 if(localStorage.getItem(FLAG))return {status:'SKIP_ALREADY_DONE'};
 const raw=localStorage.getItem(SRC);if(!raw)return {status:'SKIP_NO_SOURCE'};
 let old;try{old=JSON.parse(raw)}catch(e){return {status:'FAIL_PARSE',error:e.message}}
 const reg=window.FS_APP?.registry?.()||[];if(!reg.length)return {status:'FAIL_NO_REGISTRY'};
 const byKey=new Map(reg.map(p=>[nk(p.name)+'|'+nk(p.team)+'|'+p.role,p]));
 const tx=[];const unresolved=[];
 for(const t of old.tx||[]){
   const p=byKey.get(nk(t.name)+'|'+nk(t.team)+'|'+t.role);
   if(!p){unresolved.push({name:t.name,team:t.team,role:t.role});continue}
   tx.push({id:p.id,name:p.name,team:p.team,role:p.role,price:Number(t.price),owner:t.owner||'ME',result:t.result||((t.owner||'ME')==='ME'?'WON':'LOST'),managerName:t.owner==='ME'?'IO':(old.managerNames?.[t.owner]||t.owner),ts:t.ts||new Date().toISOString(),engine:'RC7.1_MIGRATED_TO_FS_STATE_V2'});
 }
 if(unresolved.length)return {status:'BLOCK_UNRESOLVED',unresolved};
 try{
   window.FS_STATE.begin('RC71_MIGRATION');
   window.FS_STATE.setTransactions(tx);
   for(const [id,name] of Object.entries(old.managerNames||{}))if(/^R[1-9]$/.test(id))window.FS_STATE.setManagerName(id,name);
   const snap=window.FS_STATE.commit('RC71_MIGRATION');
   localStorage.setItem(FLAG,JSON.stringify({status:'PASS',at:new Date().toISOString(),transactions:tx.length,state_hash:snap?.state_hash||null}));
   return {status:'PASS',transactions:tx.length,state_hash:snap?.state_hash||null};
 }catch(e){try{window.FS_STATE.rollback()}catch(_e){}return {status:'FAIL_IMPORT',error:e.message}}
}
window.FS_RC7_MIGRATION={run,source:SRC,flag:FLAG};
})();