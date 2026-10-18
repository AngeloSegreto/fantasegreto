'use strict';
const C=require('./core');
const {order}=require('./decision-id');
const {scenarioStreams}=require('./pcg64');
function rng(seed){return scenarioStreams(seed,0)('SINGLE_STREAM_COMPAT');}
function normal(rand){return Math.sqrt(-2*Math.log(Math.max(Number.MIN_VALUE,rand())))*Math.cos(2*Math.PI*rand());}
function poisson(rate,rand){if(rate===0)return 0;const limit=Math.exp(-rate);let p=1,k=0;do{k++;p*=rand();}while(p>limit);return k-1;}
function weighted(items,weight,rand){const u=rand();let sum=0;for(const x of items){sum+=weight(x);if(u<sum)return x;}return null;}
function compile(input){
 // Normalize non-operational record order before consuming any random draws.
 const orderedPlayers=input.players.slice().sort((a,b)=>order(a.id,b.id));
 const players=Object.fromEntries(orderedPlayers.map(p=>[p.id,p]));
 return {input,players,fixtures:input.fixtures.slice().sort((a,b)=>order(a.id,b.id)).map(f=>({...f,
  homePlayers:orderedPlayers.filter(p=>p.team===f.home),awayPlayers:orderedPlayers.filter(p=>p.team===f.away)}))};
}
function scenario(model,rand,streams=null){
 const out={},matches={},rules=model.input.rules,b=rules.bonus_malus;
 for(const f of model.fixtures) {
  const matchDraw=streams?streams('MATCH',f.id):rand;
  const hg=poisson(f.home_goal_rate,matchDraw),ag=poisson(f.away_goal_rate,matchDraw);
  matches[f.id]={home:hg,away:ag,events:[]};
  for(const [ps,gf,ga,team] of [[f.homePlayers,hg,ag,f.home],[f.awayPlayers,ag,hg,f.away]]) {
   const teamDraw=streams?streams('TEAM',f.id,team):rand;
   const shock=teamDraw()<f.disruption_probability,z=normal(teamDraw);
   const keeper=weighted(ps.filter(p=>p.role==='P'),p=>p.projection.start,teamDraw);
   for(const p of ps) {
    const draw=streams?streams('PLAYER',p.id):rand;
    const x=p.projection;let status='ABSENT';
    if(p.role==='P')status=keeper?.id===p.id?'START':'ABSENT';
    else {const u=draw();status=u<x.start?'START':u<x.start+x.sub?'SUB':'ABSENT';}
    const voted=status!=='ABSENT'&&draw()<(status==='START'?x.vote_given_start:x.vote_given_sub)&&!(shock&&draw()<x.disruption_sensitivity);
    const pure=voted?(rules.league_config?
     weighted(x.vote_pmf,v=>v.probability,draw).vote:
     Math.max(0,Math.min(10,x.vote_mean+x.vote_sd*normal(draw)+x.team_vote_loading*z+x.conceded_vote_loading*(ga-(p.team===f.home?f.away_goal_rate:f.home_goal_rate))))):null;
    const yellow=voted&&draw()<x.yellow_probability?1:0,red=voted&&draw()<x.red_probability?1:0;
    const saves=voted&&p.role==='P'?poisson(x.save_rate,draw):0;
    out[p.id]={status,voted,pure,fp:0,goals:0,assists:0,yellow,red,saves,conceded:p.role==='P'&&voted?ga:0,clean_sheet:p.role==='P'&&voted&&ga===0};
   }
   // Team goals are drawn once. Unmodelled scorers/assisters retain residual mass.
   // Availability does not renormalize known-player goal shares upwards.
   for(let k=0;k<gf;k++) {
    const scorer=weighted(ps,p=>out[p.id].voted?p.projection.goal_share:0,teamDraw);
    const assister=weighted(ps,p=>out[p.id].voted&&p.id!==scorer?.id?p.projection.assist_share:0,teamDraw);
    if(scorer)out[scorer.id].goals++;
    if(assister)out[assister.id].assists++;
    matches[f.id].events.push({team,scorer:scorer?.id||null,assister:assister?.id||null});
   }
  }
 }
 for(const p of model.input.players) {
  const x=out[p.id];if(x.voted)x.fp=rules.league_config?
   require('./league-rules').fantasyPoints(x.pure,{goal:x.goals,assist:x.assists,yellow:x.yellow,
    red:x.red,save:x.saves,conceded:x.conceded,clean_sheet:Number(x.clean_sheet)},b):
   x.pure+b.goal*x.goals+b.assist*x.assists+b.yellow*x.yellow+b.red*x.red+b.save*x.saves+b.conceded*x.conceded+b.clean_sheet*Number(x.clean_sheet);
 }
 return {players:out,matches};
}
function summary(values){
 const n=values.length,mean=values.reduce((a,b)=>a+b,0)/n,s=values.slice().sort((a,b)=>a-b);
 const q=p=>s[Math.floor((n-1)*p)];
 const tail=s.slice(0,Math.max(1,Math.ceil(n*.05)));
 return {mean,median:q(.5),p05:q(.05),p25:q(.25),p75:q(.75),p95:q(.95),worst_5pct_mean:tail.reduce((a,b)=>a+b,0)/tail.length,variance:values.reduce((a,v)=>a+(v-mean)**2,0)/n};
}
function evaluate(input,candidates,options={}) {
 const validation=C.validate(input);
 if(validation.errors.length)return {status:'BLOCKED_PENDING_VERIFIED_INPUTS',errors:validation.errors,gold:false,simulation_count:0};
 // Continuous synthetic votes cannot be silently rounded into the screenshot's
 // discrete captain table. No samples may be dropped to bypass an unknown rule.
 if(input.rules.league_config) {
  const errors=[];
  if(input.rules.vote_model!=='EXPLICIT_DISCRETE_PMF')errors.push('Explicit discrete vote PMF model required; continuous votes are never rounded');
  for(const p of input.players) {
   const x=p.projection,pmf=x.vote_pmf;
   if(!Array.isArray(pmf)||!pmf.length||pmf.some(v=>!v||typeof v.vote!=='string'||!/^\d+(\.\d+)?$/.test(v.vote)||!C.finite(Number(v.vote))||Number(v.vote)>10||!C.prob(v.probability))||
      Math.abs((pmf||[]).reduce((s,v)=>s+v.probability,0)-1)>1e-12)errors.push('Invalid discrete vote PMF '+p.id);
   if(x.team_vote_loading!==0||x.conceded_vote_loading!==0)errors.push('Continuous vote shock coefficients unsupported with explicit PMF '+p.id);
  }
  if(errors.length)return {status:'BLOCKED_PENDING_VOTE_MODEL_AND_RULE_EXCEPTIONS',errors,gold:false,simulation_count:0};
 }
 const n=options.iterations??100000,seed=options.seed??20261018;
 C.assert(Number.isInteger(n)&&n>=100&&n<=500000,'iterations must be 100..500000');
 C.assert(Number.isInteger(seed)&&seed>=0&&seed<=0xffffffff,'seed must be uint32');
 const model=compile(input);
 C.assert(Array.isArray(candidates)&&candidates.length>0&&candidates.length<=1000,'1..1000 candidates per evaluation');
 for(const l of candidates)C.assert(!C.validateLineup(l,input.home.roster,model.players,input.rules).length,'invalid candidate');
 const stats=candidates.map(()=>({win:0,draw:0,loss:0,points:[],opponent:[],goals:{},margins:{},missing:0,modifier:0,captain:0,recovered:0,bench:0,bonus:0,first:0,second:0,next:0}));
 const keeperStats=Object.fromEntries(input.home.roster.filter(id=>model.players[id].role==='P').map(id=>[id,{voted:0,clean:0,conceded:0,saves:0,pure:[],fp:[],ge6:0,ge65:0,ge7:0}]));
 const pairDiff=Array.from({length:candidates.length},()=>({sum:0,sum2:0}));
 for(let j=0;j<n;j++) {
  try {
  const s=scenario(model,null,scenarioStreams(seed,j)),a=C.score(input.away.lineup,s.players,model.players,input.rules),wins=[];
  for(const [id,k] of Object.entries(keeperStats)) {
   const p=s.players[id];k.fp.push(Number(p.fp));if(p.voted){k.voted++;k.clean+=Number(p.clean_sheet);k.conceded+=p.conceded;k.saves+=p.saves;k.pure.push(Number(p.pure));k.ge6+=Number(p.fp>=6);k.ge65+=Number(p.fp>=6.5);k.ge7+=Number(p.fp>=7);}
  }
  candidates.forEach((l,k)=>{
   const h=C.score(l,s.players,model.players,input.rules),t=stats[k],w=Number(h.goals>a.goals);wins.push(w);
   t.win+=w;t.draw+=Number(h.goals===a.goals);t.loss+=Number(h.goals<a.goals);t.points.push(h.total);t.opponent.push(a.total);
   t.goals[h.goals]=(t.goals[h.goals]||0)+1;const d=h.goals-a.goals;t.margins[d]=(t.margins[d]||0)+1;
   t.missing+=Number(h.missing>0);t.modifier+=h.modifier;t.captain+=h.captain;t.recovered+=h.recovered;t.bench+=h.bench_unused_points;t.bonus+=h.unused_bonus;
   if(j<Math.floor(n/2))t.first+=w;else t.second+=w;
  });
  wins.forEach((w,k)=>{const d=w-wins[0];pairDiff[k].sum+=d;pairDiff[k].sum2+=d*d;});
  } catch(error) {
   if(!input.rules.league_config)throw error;
   return {status:'BLOCKED_UNRESOLVED_LEAGUE_SCENARIO',errors:[error.message],
    attempted_scenarios:j+1,discarded_partial_results:true,gold:false,simulation_count:0};
  }
 }
 const dist=o=>Object.fromEntries(Object.entries(o).map(([k,v])=>[k,v/n]));
 const results=stats.map((t,k)=>{
  const p=t.win/n,se=Math.sqrt(p*(1-p)/n),diff=pairDiff[k].sum/n;
  const diffSE=Math.sqrt(Math.max(0,(pairDiff[k].sum2/n-diff*diff)/(n-1)));
  const half=Math.floor(n/2),p1=t.first/half,p2=t.second/(n-half),halfSE=Math.sqrt(p1*(1-p1)/half+p2*(1-p2)/(n-half));
  const mean=t.points.reduce((a,b)=>a+b,0)/n,nextThreshold=mean<66?66:66+4*(Math.floor((mean-66)/4)+1);
  return {lineup:candidates[k],formation:C.formation(candidates[k].starters,model.players),win:p,draw:t.draw/n,loss:t.loss/n,
   mc_95_interval:[Math.max(0,p-1.96*se),Math.min(1,p+1.96*se)],mc_standard_error:se,
   paired_to_first:{win_difference:diff,mc_standard_error:diffSE,indistinguishable_mc:Math.abs(diff)<=1.96*diffSE},
   points:summary(t.points),opponent_points:summary(t.opponent),fantagoals:dist(t.goals),goal_margins:dist(t.margins),
   expected_fantagoals:Object.entries(t.goals).reduce((s,[g,v])=>s+Number(g)*v,0)/n,
   next_threshold:nextThreshold,probability_next_threshold:t.points.filter(p=>p>=nextThreshold).length/n,
   incomplete_probability:t.missing/n,expected_defence_modifier:t.modifier/n,expected_captain:t.captain/n,
   expected_recovered_points:t.recovered/n,expected_unused_bench_points:t.bench/n,expected_unused_bench_bonus:t.bonus/n,
   convergence:{first_half_win:p1,second_half_win:p2,delta:Math.abs(p1-p2),tolerance:3*halfSE+1/n,pass:Math.abs(p1-p2)<=3*halfSE+1/n}};
 });
 const keepers=Object.fromEntries(Object.entries(keeperStats).map(([id,k])=>[id,{vote_probability:k.voted/n,clean_sheet_probability:k.clean/n,
  expected_conceded:k.conceded/n,expected_saves:k.saves/n,pure_conditional_on_vote:k.pure.length?summary(k.pure):null,
  fantasy_points:k.fp.length?summary(k.fp):null,probability_ge6:k.ge6/n,probability_ge65:k.ge65/n,probability_ge7:k.ge7/n}]));
 return {version:C.VERSION,random_engine:'PCG64_XSL_RR_128_64_ENTITY_SCENARIO_V1',
  status:input.kind==='SYNTHETIC'?'SYNTHETIC_TEST_ONLY':'EXPERIMENTAL_UNCALIBRATED',gold:false,simulation_count:n,seed,
  confidence:'UNCALIBRATED',warnings:validation.warnings,results,keepers,
  availability:Object.fromEntries(input.players.map(p=>[p.id,C.availability(p.projection)])),
  source_health:Object.fromEntries(input.sources.map(s=>[s.id,C.freshness(s,input.as_of)])),
  uncertainty_note:'Monte Carlo error conditional on input model; excludes parameter uncertainty and forecast miscalibration.'};
}
module.exports={rng,normal,poisson,compile,scenario,summary,evaluate};
