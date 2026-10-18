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
function decimalText(value) {
 // Sums of decimal inputs retain a power-of-ten denominator.
 const negative=value.n<0n,n=negative?-value.n:value.n;
 let places=0,d=value.d;while(d>1n&&d%10n===0n){places++;d/=10n;}
 if(d!==1n)throw Error('Non-terminating decimal output');
 const digits=n.toString().padStart(places+1,'0');
 let text=places?digits.slice(0,-places)+'.'+digits.slice(-places):digits;
 if(places)text=text.replace(/0+$/,'').replace(/\.$/,'');
 return (negative&&n!==0n?'-':'')+text;
}
function exactGoals(total,config) {
 const r=config.rules.fantasy_goals,first=decimal(r.first_goal),width=decimal(r.band_width);
 if(width.n<=0n||first.n<0n||r.fixed!==true||r.unbounded!==true)throw Error('Unsupported goal configuration');
 const score=decimal(total);if(compare(score,first)<0)return 0;
 const diff={n:score.n*first.d-first.n*score.d,d:score.d*first.d};
 const count=1n+(diff.n*width.d)/(diff.d*width.n);
 if(count>BigInt(Number.MAX_SAFE_INTEGER))throw Error('Goal count outside exact integer domain');
 return Number(count);
}
function fantasyPoints(pure,events,weights) {
 let value=decimal(pure);
 for(const [name,count] of Object.entries(events)) {
  if(!Number.isSafeInteger(count)||count<0)throw Error('Invalid event count');
  const weight=decimal(String(weights[name]));
  value=add(value,{n:weight.n*BigInt(count),d:weight.d});
 }
 return decimalText(value);
}
function scoreResolved(lineup,xi,used,scenario,players,rules) {
 const config=rules.league_config;
 if(rules.substitution_count!==config.rules.substitutions.maximum||config.rules.substitutions.office_reserve_enabled!==false)
  throw Error('Substitution settings differ from acquired configuration');
 const valid=xi.filter(p=>p.voted);
 const effective=xi.map(p=>({role:players[p.id].role,pure_vote:p.voted?p.pure:null,
  kind:p.vote_kind||'NORMAL',office_reserve:!!p.office_reserve}));
 const modifier=defenseModifier(effective,config);
 const captainPlayer=valid.find(p=>p.id===lineup.captain),vicePlayer=valid.find(p=>p.id===lineup.vice);
 const chosenCaptain=captainPlayer||vicePlayer;
 if(config.rules.captain_factor.enabled&&chosenCaptain&&chosenCaptain.vote_kind&&chosenCaptain.vote_kind!=='NORMAL')
  throw Error('Special captain vote treatment not shown');
 const captain=captainFactor(captainPlayer?captainPlayer.pure:null,vicePlayer?vicePlayer.pure:null,config);
 const sum=ids=>ids.reduce((value,id)=>add(value,decimal(scenario[id].fp)),zero());
 const base=sum(valid.map(p=>p.id));
 const total=add(add(base,decimal(modifier)),decimal(captain));
 const unused=lineup.bench.filter(id=>!used.has(id)&&scenario[id].voted);
 const unusedBonus=unused.reduce((value,id)=>{
  const p=scenario[id],difference=add(decimal(p.fp),{...decimal(p.pure),n:-decimal(p.pure).n});
  return add(value,difference.n>0n?difference:zero());
 },zero());
 const exact={base:decimalText(base),modifier,captain,total:decimalText(total),
  recovered:decimalText(sum([...used])),bench_unused_points:decimalText(sum(unused)),
  unused_bonus:decimalText(unusedBonus)};
 return {...Object.fromEntries(Object.entries(exact).map(([key,value])=>[key,Number(value)])),
  exact,goals:exactGoals(exact.total,config),rules_version:config.version,
  status:'PROVISIONAL_OBSERVED_SCORE',gold:false};
}
module.exports={defenseModifier,captainFactor,exactGoals,scoreResolved,fantasyPoints};
