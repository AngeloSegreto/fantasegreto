'use strict';
const C=require('./core');
function betaVotePosterior(priorAlpha,priorBeta,observations,cutoff) {
 C.assert(Number.isFinite(priorAlpha)&&priorAlpha>0&&Number.isFinite(priorBeta)&&priorBeta>0,'invalid Beta prior');
 C.assert(Number.isFinite(Date.parse(cutoff)),'invalid cutoff');
 let a=priorAlpha,b=priorBeta;
 for(const o of observations){C.assert(typeof o.voted==='boolean'&&Number.isFinite(Date.parse(o.observed_at))&&Date.parse(o.observed_at)<=Date.parse(cutoff),'future/invalid availability observation');if(o.voted)a++;else b++;}
 return {alpha:a,beta:b,mean:a/(a+b),observations:observations.length,status:'POSTERIOR_UNCALIBRATED'};
}
function metrics(rows,bins=10) {
 C.assert(rows.length>0&&Number.isInteger(bins)&&bins>0,'invalid metric inputs');
 let brier=0,log=0,mae=0,voteBrier=0,bonusBrier=0;const cells=Array.from({length:bins},()=>({n:0,p:0,y:0}));
 let voteN=0,bonusN=0;
 for(const r of rows) {
  const p=r.probabilities;
  C.assert(Array.isArray(p)&&p.length===3&&p.every(C.prob)&&Math.abs(p.reduce((a,b)=>a+b,0)-1)<1e-10&&[0,1,2].includes(r.outcome),'invalid multiclass probabilities/outcome');
  C.assert(Number.isFinite(r.expected_points)&&Number.isFinite(r.actual_points),'invalid points');
  brier+=p.reduce((s,v,j)=>s+(v-Number(j===r.outcome))**2,0);log+=p[r.outcome]===0?Infinity:-Math.log(p[r.outcome]);mae+=Math.abs(r.expected_points-r.actual_points);
  const c=cells[Math.min(bins-1,Math.floor(p[0]*bins))];c.n++;c.p+=p[0];c.y+=Number(r.outcome===0);
  for(const [k,n] of [['votes','vote'],['bonuses','bonus']])for(const o of r[k]||[]) {
   C.assert(C.prob(o.p)&&typeof o.observed==='boolean','invalid reliability observation');
   if(n==='vote'){voteBrier+=(o.p-Number(o.observed))**2;voteN++;}else{bonusBrier+=(o.p-Number(o.observed))**2;bonusN++;}
  }
 }
 return {sample_size:rows.length,brier_multiclass:brier/rows.length,log_loss:log/rows.length,mae_fantapoints:mae/rows.length,
  win_calibration_error:cells.reduce((s,c)=>s+(c.n?c.n/rows.length*Math.abs(c.p/c.n-c.y/c.n):0),0),
  vote_brier:voteN?voteBrier/voteN:null,bonus_brier:bonusN?bonusBrier/bonusN:null,
  status:'DIAGNOSTIC_NOT_PROMOTION_EVIDENCE'};
}
// Train callback receives only earlier completed rounds; held-out labels are never passed to predict.
function rollingBacktest(rounds,train,predict,minHistory=1) {
 C.assert(rounds.length>minHistory&&Number.isInteger(minHistory)&&minHistory>=1,'insufficient history');
 for(let j=0;j<rounds.length;j++) {
  const r=rounds[j];C.assert(Number.isFinite(Date.parse(r.lock_at))&&Number.isFinite(Date.parse(r.completed_at))&&Date.parse(r.lock_at)<Date.parse(r.completed_at),'invalid round times');
  if(j)C.assert(Date.parse(rounds[j-1].lock_at)<Date.parse(r.lock_at),'round order');
  C.assert(Number.isFinite(Date.parse(r.features_as_of))&&Date.parse(r.features_as_of)<=Date.parse(r.lock_at),'future features');
 }
 const rows=[];
 for(let j=minHistory;j<rounds.length;j++) {
  const target=rounds[j],history=rounds.slice(0,j).filter(r=>Date.parse(r.completed_at)<=Date.parse(target.lock_at));
  if(history.length<minHistory)continue;
  const model=train(structuredClone(history)),forecast=predict(model,structuredClone(target.features));
  rows.push({...forecast,...target.actual,round:target.round});
 }
 C.assert(rows.length>0,'no eligible rolling folds');return {rows,metrics:metrics(rows)};
}
function postmatchOracle(input,observed,candidates) {
 const ps=Object.fromEntries(input.players.map(p=>[p.id,p]));
 C.assert(input.home.roster.every(id=>observed[id]&&typeof observed[id].voted==='boolean'&&(!observed[id].voted||(Number.isFinite(observed[id].pure)&&Number.isFinite(observed[id].fp)))),'official results incomplete');
 for(const l of [input.home.lineup,...candidates])C.assert(!C.validateLineup(l,input.home.roster,ps,input.rules).length,'invalid oracle candidate');
 const chosen=C.score(input.home.lineup,observed,ps,input.rules),rank=[input.home.lineup,...candidates].map(lineup=>({lineup,...C.score(lineup,observed,ps,input.rules)})).sort((a,b)=>b.total-a.total);
 C.assert(rank.length>0,'oracle candidates missing');
 return {mode:'POST_MATCH_ORACLE',scope:'SUPPLIED_CANDIDATES',chosen,oracle:rank[0],regret_points:Math.max(0,rank[0].total-chosen.total),
  predictable_regret:null,random_variability_regret:null,note:'Oracle gap alone does not establish a preventable forecasting error.'};
}
// LIVE scoring-only what-if: observed state remains fixed except explicit user interventions.
function liveWhatIf(input,observed,mutations) {
 C.assert(Array.isArray(mutations),'mutations required');
 const ps=Object.fromEntries(input.players.map(p=>[p.id,p])),state=structuredClone(observed);
 C.assert([...input.home.roster,...input.away.roster].every(id=>state[id]&&typeof state[id].voted==='boolean'&&(!state[id].voted||(Number.isFinite(state[id].pure)&&Number.isFinite(state[id].fp)))),'live state incomplete');
 for(const m of mutations) {
  C.assert(ps[m.id]&&Number.isFinite(m.fp_delta)&&Number.isFinite(m.pure_delta),'invalid what-if');
  C.assert(state[m.id].voted,'SV intervention requires a separately resolved official state');
  state[m.id].fp+=m.fp_delta;state[m.id].pure+=m.pure_delta;
 }
 const h=C.score(input.home.lineup,state,ps,input.rules),a=C.score(input.away.lineup,state,ps,input.rules);
 return {mode:'LIVE_WHAT_IF_SCORING_ONLY',home:h,away:a,points_needed_to_win:Math.max(0,66+4*a.goals-h.total),
  points_needed_to_draw:a.goals===0?(h.goals===0?0:null):h.goals>a.goals?null:Math.max(0,66+4*(a.goals-1)-h.total),
  win_probability:null,remaining_event_simulation:'NOT_IMPLEMENTED'};
}
module.exports={betaVotePosterior,metrics,rollingBacktest,postmatchOracle,liveWhatIf};
