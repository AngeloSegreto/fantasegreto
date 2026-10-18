'use strict';
// Exact arithmetic for observed votes. Never guesses unshown SV or captain rules.
function decimal(x) {
 if(typeof x!=='string'||!/^[-+]?\d+(\.\d+)?$/.test(x))throw Error('decimal string required');
 const negative=x.startsWith('-'),s=x.replace(/^[-+]/,''),[a,b='']=s.split('.');
 return {n:BigInt(a+b)*(negative?-1n:1n),d:10n**BigInt(b.length)};
}
const compare=(a,b)=>a.n*b.d<b.n*a.d?-1:a.n*b.d>b.n*a.d?1:0;
const add=(a,b)=>({n:a.n*b.d+b.n*a.d,d:a.d*b.d});
const zero=()=>decimal('0');
function validateVote(p,rule) {
 if(p.office_reserve)return null;
 if(p.kind==='SV_YELLOW') {
  if(rule.sv_yellow_validation_enabled===null)throw Error('SV yellow validation option unknown');
  return rule.sv_yellow_validation_enabled?decimal(rule.sv_yellow_vote_if_validated):null;
 }
 if(p.kind==='POLITICAL_SIX')return decimal(rule.political_six_vote);
 return p.pure_vote===null?null:decimal(p.pure_vote);
}
function defenseModifier(effectivePlayers,config) {
 const r=config.rules.defense_modifier;
 if(!r.enabled)return '0';
 const defenders=effectivePlayers.filter(p=>p.role==='D');
 // The effective post-substitution formation controls eligibility.
 if(defenders.length<r.minimum_effective_defenders)return '0';
 const votes=defenders.map(p=>validateVote(p,r)).filter(v=>v!==null).sort((a,b)=>-compare(a,b));
 if(votes.length<r.minimum_effective_defenders)return '0';
 const keeper=effectivePlayers.find(p=>p.role==='P');
 const keeperVote=keeper?validateVote(keeper,r):null;
 if(r.include_keeper&&!keeperVote)throw Error('Keeper without eligible vote: rule not shown');
 const selected=r.include_keeper?[keeperVote,...votes.slice(0,r.top_defenders)]:votes.slice(0,4);
 const sum=selected.reduce(add,zero()),average={n:sum.n,d:sum.d*BigInt(selected.length)};
 let bonus='0';for(const b of r.bands)if(b.minimum===null||compare(average,decimal(b.minimum))>=0)bonus=b.bonus;
 return bonus;
}
function captainFactor(captainVote,viceVote,config) {
 const r=config.rules.captain_factor;if(!r.enabled)return '0';
 const v=captainVote===null?viceVote:captainVote;
 if(v===null)throw Error('Both captain and vice without vote: rule not shown');
 const value=decimal(v);
 if(compare(value,decimal(r.at_or_below.vote))<=0)return r.at_or_below.bonus;
 if(compare(value,decimal(r.at_or_above.vote))>=0)return r.at_or_above.bonus;
 for(const [vote,bonus] of Object.entries(r.exact_votes))if(compare(value,decimal(vote))===0)return bonus;
 throw Error('Unlisted captain vote: do not interpolate or round');
}
module.exports={defenseModifier,captainFactor};
