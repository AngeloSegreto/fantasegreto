/* FS PREMIUM MONTE CARLO V1 - standalone, no external services.
   FAIL CLOSED: no probabilities or league rules are assumed. */
(function(root){
'use strict';
const requiredRules=['substitution_count','substitution_mode','bench_order','goal_thresholds','bonus_malus'];
function validate(contract,projections){
 const errors=[],i=contract?.inputs||{},r=i.league_rules||{};
 for(const side of ['home','away']){
  const xi=i[side+'_starting_xi'],bench=i[side+'_bench'];
  if(!Array.isArray(xi)||xi.length!==11)errors.push(side+': expected 11 starters');
  if(!Array.isArray(bench)||bench.length<1)errors.push(side+': bench missing');
  for(const p of [...(xi||[]),...(bench||[])])if(!p.official_id)errors.push(side+': missing official_id for '+p.name);
 }
 for(const k of requiredRules)if(r[k]===null||r[k]===undefined)errors.push('league_rules.'+k+' missing');
 if(!Array.isArray(r.goal_thresholds)||r.goal_thresholds.length<1||r.goal_thresholds.some((v,j)=>!Number.isFinite(v)||(j>0&&v<=r.goal_thresholds[j-1])))errors.push('invalid goal_thresholds');
 if(r.substitution_mode!=='SAME_ROLE'||r.module_change_allowed!==false)errors.push('same-role substitutions without module change must be confirmed');
 if(r.bench_order!=='DISPLAY_ORDER')errors.push('bench order not confirmed');
 if(r.substitution_count!==5)errors.push('National League requires exactly five substitutions');
 if(!projections||typeof projections!=='object')errors.push('projections missing');
 for(const side of ['home','away'])for(const p of [...(i[side+'_starting_xi']||[]),...(i[side+'_bench']||[])]){
  if(!p.official_id)continue;
  const x=projections?.[p.official_id];
  if(!x||!Number.isFinite(x.vote_probability)||x.vote_probability<0||x.vote_probability>1||!Number.isFinite(x.mean)||!Number.isFinite(x.sd)||x.sd<0)errors.push('projection missing/invalid for '+p.name);
 }
 return [...new Set(errors)];
}
function rng(seed){let a=seed>>>0;return ()=>{a=(a+0x6D2B79F5)|0;let t=Math.imul(a^(a>>>15),1|a);t^=t+Math.imul(t^(t>>>7),61|t);return ((t^(t>>>14))>>>0)/4294967296;};}
function normal(rand){return Math.sqrt(-2*Math.log(Math.max(1e-12,rand())))*Math.cos(2*Math.PI*rand());}
function samplePlayer(p,projections,rand){const x=projections[p.official_id];const voted=rand()<x.vote_probability;return {p,voted,score:voted?x.mean+x.sd*normal(rand):0};}
function evaluate(side,inputs,projections,rules,rand){
 const starters=inputs[side+'_starting_xi'].map(p=>samplePlayer(p,projections,rand));
 const bench=inputs[side+'_bench'].map(p=>samplePlayer(p,projections,rand));
 let changes=0;
 for(const slot of starters){
  if(slot.voted||changes>=rules.substitution_count)continue;
  const replacement=bench.find(b=>b.voted&&!b.used&&b.p.role===slot.p.role);
  // FLEXIBLE needs a league-specific legal-formation resolver, not a guess.
  if(replacement){slot.voted=true;slot.score=replacement.score;replacement.used=true;changes++;}
 }
 const missing=starters.filter(s=>!s.voted).length;
 const total=starters.reduce((sum,s)=>sum+s.score,0);
 return {total,missing,changes};
}
function simulate(contract,projections,options={}){
 const errors=validate(contract,projections);
 if(errors.length)return {status:'BLOCKED_PENDING_VERIFIED_INPUTS',errors,simulation_count:0};
 const rules=contract.inputs.league_rules;
 if(rules.substitution_mode!=='SAME_ROLE')return {status:'BLOCKED_FLEXIBLE_SUBSTITUTION_RESOLVER_PENDING',simulation_count:0};
 if(rules.defence_modifier!==false||rules.captain_factor!==false||rules.bonus_malus?.included_in_projection!==true)return {status:'BLOCKED_SCORING_RULES_UNIMPLEMENTED',simulation_count:0};
 const n=options.iterations??10000,seed=options.seed??20261009;
 if(!Number.isInteger(n)||n<100||n>1000000||!Number.isInteger(seed))throw Error('invalid simulation settings');
 const rand=rng(seed);let home=0,away=0,draw=0;
 const goals=x=>rules.goal_thresholds.reduce((count,threshold)=>count+(x>=threshold?1:0),0);
 for(let j=0;j<n;j++){
  const h=evaluate('home',contract.inputs,projections,rules,rand);
  const a=evaluate('away',contract.inputs,projections,rules,rand);
  const hg=goals(h.total),ag=goals(a.total);
  if(hg>ag)home++;else if(hg<ag)away++;else draw++;
 }
 return {status:'EXPERIMENTAL_UNCALIBRATED',simulation_count:n,seed,home_win_probability:home/n,draw_probability:draw/n,away_win_probability:away/n,gold:false};
}
const api={validate,simulate,version:'FS_PREMIUM_MONTE_CARLO_V1'};
if(typeof module!=='undefined'&&module.exports)module.exports=api;
else root.FS_PREMIUM_SIMULATOR=api;
})(typeof window!=='undefined'?window:globalThis);
