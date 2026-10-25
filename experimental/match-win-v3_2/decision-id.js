'use strict';
const crypto=require('node:crypto');
const order=(a,b)=>a<b?-1:a>b?1:0;
function decisionIdentity(lineup) {
 if(!lineup||!Array.isArray(lineup.starters)||!Array.isArray(lineup.bench))throw Error('Complete decision required');
 if(lineup.starters.length!==11)throw Error('Eleven starters required');
 const starters=lineup.starters.slice().sort(order),bench=lineup.bench.slice();
 const ids=[...starters,...bench];
 if(ids.some(id=>typeof id!=='string')||new Set(ids).size!==ids.length)throw Error('Unique string player IDs required');
 const encoded='Titolari:'+JSON.stringify(starters)+'|Panchina:'+JSON.stringify(bench)+
  '|Capitano:'+JSON.stringify(lineup.captain??null)+'|Vice:'+JSON.stringify(lineup.vice??null);
 return crypto.createHash('sha256').update(encoded).digest('hex');
}
module.exports={order,decisionIdentity};
