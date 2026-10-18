'use strict';
const C=require('./core'),S=require('./simulator');
function* choose(xs,n,start=0,prefix=[]) {
 if(n===0){yield prefix;return;}
 for(let j=start;j<=xs.length-n;j++)yield* choose(xs,n-1,j+1,[...prefix,xs[j]]);
}
function* permutations(xs) {
 if(xs.length<2){yield xs;return;}
 for(let j=0;j<xs.length;j++)for(const rest of permutations(xs.filter((_,k)=>k!==j)))yield [xs[j],...rest];
}
function combinationCount(n,k){if(n<k)return 0;let v=1;for(let j=1;j<=k;j++)v=v*(n-j+1)/j;return Math.round(v);}
function factorial(n){let v=1;for(let j=2;j<=n;j++)v*=j;return v;}
function searchSize(input,{bench='FIXED',captains='FIXED'}={}) {
 const ps=Object.fromEntries(input.players.map(p=>[p.id,p])),roles=Object.fromEntries(C.ROLES.map(r=>[r,input.home.roster.filter(id=>ps[id].role===r)]));
 const n=input.home.roster.length;
 return input.rules.formations.reduce((s,f)=>{const [d,c,a]=f.split('-').map(Number);return s+roles.P.length*combinationCount(roles.D.length,d)*combinationCount(roles.C.length,c)*combinationCount(roles.A.length,a);},0)
  *(bench==='ALL'?factorial(n-11):1)*(input.rules.captain.enabled&&captains==='ALL'?110:1);
}
function enumerate(input,options={}) {
 const validation=C.validate(input);C.assert(!validation.errors.length,validation.errors.join('; '));
 const {bench='FIXED',captains='FIXED',max_candidates=1000}=options;
 C.assert(['FIXED','ALL'].includes(bench)&&['FIXED','ALL'].includes(captains),'invalid search mode');
 const size=searchSize(input,options);
 // Never silently prune to high means, and never label a partial search global.
 C.assert(size<=max_candidates&&size<=1000,'EXHAUSTIVE_SEARCH_BUDGET_EXCEEDED: '+size+' candidates; provide an explicit panel or increase compute in a separate runner');
 const ps=Object.fromEntries(input.players.map(p=>[p.id,p])),roles=Object.fromEntries(C.ROLES.map(r=>[r,input.home.roster.filter(id=>ps[id].role===r)])),out=[];
 for(const f of input.rules.formations) {
  const [d,c,a]=f.split('-').map(Number);
  for(const p of roles.P)for(const ds of choose(roles.D,d))for(const cs of choose(roles.C,c))for(const as of choose(roles.A,a)) {
   const starters=[p,...ds,...cs,...as],rest=input.home.roster.filter(id=>!starters.includes(id));
   const benches=bench==='ALL'?permutations(rest):[rest];
   for(const b of benches) {
    const pairs=input.rules.captain.enabled?(captains==='ALL'?starters.flatMap(c=>starters.filter(v=>v!==c).map(v=>[c,v])):[[input.home.lineup.captain,input.home.lineup.vice]]):[[null,null]];
    for(const [captain,vice] of pairs) {
     const l={starters,bench:b,captain,vice};
     if(!C.validateLineup(l,input.home.roster,ps,input.rules).length)out.push(l);
    }
   }
  }
 }
 return {candidates:out,scope:{lineups:'ALL_ALLOWED',bench,captains,estimated_candidates:size,actual_candidates:out.length,global_joint_optimum_searched:bench==='ALL'&&(!input.rules.captain.enabled||captains==='ALL')}};
}
function rankResults(results) {
 return results.map((r,index)=>({index,...r})).sort((a,b)=>b.win-a.win||b.draw-a.draw||a.incomplete_probability-b.incomplete_probability||b.points.mean-a.points.mean||a.index-b.index);
}
function optimize(input,candidates,options={}) {
 const report=S.evaluate(input,candidates,options);
 if(!report.results)return report;
 const rank=rankResults(report.results);
 const best=rank[0],alternate=rank.find(r=>r.formation!==best.formation)||rank[1];
 // Independent validation draw; never use it to rerank candidates.
 const holdout=S.evaluate(input,[best.lineup,...(alternate?[alternate.lineup]:[])],{iterations:options.iterations??100000,seed:((options.seed??20261018)^0x9e3779b9)>>>0});
 return {...report,objective:'MAX_WIN_THEN_DRAW_THEN_COMPLETENESS_THEN_POINTS',scope:options.scope||{lineups:'EXPLICIT_PANEL',global_joint_optimum_searched:false},
  recommended_index:best.index,ranking:rank.map(r=>({index:r.index,win:r.win,draw:r.draw,points:r.points.mean,formation:r.formation})),
  selection_warning:'Best among evaluated candidates under supplied model, not a certified National League prediction.',
  holdout:{seed:holdout.seed,simulation_count:holdout.simulation_count,results:holdout.results},
  alternative_index:alternate?.index??null,advantage:alternate?holdout.results[1].paired_to_first:null,
  model_comparison:{
   A_expected_points_index:report.results.reduce((b,r,j)=>r.points.mean>report.results[b].points.mean?j:b,0),
   B_availability_index:report.results.reduce((b,r,j)=>r.incomplete_probability<report.results[b].incomplete_probability?j:b,0),
   C_shared_scenarios:report.simulation_count,D_match_win_index:best.index,
   ensemble_weights:null,note:'A and B are diagnostics of the same supplied model, not independent calibrated predictors. Learned ensemble pending real out-of-sample history.'}};
}
module.exports={choose,permutations,searchSize,enumerate,optimize,rankResults};
