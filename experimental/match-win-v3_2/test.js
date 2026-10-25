'use strict';
const {test}=require('node:test'),A=require('node:assert/strict'),C=require('./core'),S=require('./simulator'),O=require('./optimizer'),D=require('./diagnostics'),{example}=require('./example');
const make=()=>structuredClone(example());
function states(i,pure=6,fp=pure){return Object.fromEntries(i.players.map(p=>[p.id,{voted:true,pure,fp}]));}
test('G8 strict goal boundaries across all 30 bands, no epsilon promotion',()=>{
 A.equal(C.goals(65.9999999999),0);A.equal(C.goals(65.999),0);
 for(let j=0;j<30;j++){const t=66+j*4;A.equal(C.goals(t-1e-10),j);A.equal(C.goals(t),j+1);A.equal(C.goals(t+1e-10),j+1);}for(const v of [NaN,Infinity,-Infinity])A.throws(()=>C.goals(v));
});
test('G0 G1 G2 G3 valid example and every formation',()=>{const {input,candidates}=make();A.deepEqual(C.validate(input).errors,[]);const ps=Object.fromEntries(input.players.map(p=>[p.id,p]));for(const l of candidates)A.deepEqual(C.validateLineup(l,input.home.roster,ps,input.rules),[]);A.equal(new Set(candidates.map(l=>C.formation(l.starters,ps))).size,7);});
test('G6 rejects missing, nonfinite, out-of-domain probabilities',()=>{for(const v of [null,undefined,NaN,-.1,1.1,Infinity]){const {input}=make();input.players[0].projection.start=v;A.ok(C.validate(input).errors.length);}});
test('G0 G12 rejects stale certification labels, future sources and fixture leakage',()=>{
 for(const edit of [i=>i.sources[0].observed_at='2027-01-01',i=>i.players[0].projection.observed_at='2027-01-01',i=>i.as_of='2027-01-01',i=>i.fixtures[0].kickoff='2025-01-01',i=>i.players[0].projection.kind='CERTIFIED',i=>i.rules.defence=null,i=>i.rules.captain=null]){const {input}=make();edit(input);A.ok(C.validate(input).errors.length);}
});
test('G2 G3 duplicate identity, missing fixture, illegal XI and ownership blocked',()=>{
 for(const edit of [i=>i.players[1].official_id=i.players[0].official_id,i=>i.players[0].fixture_id='missing',i=>i.home.lineup.starters[0]='foreign',i=>i.home.lineup.starters[1]=i.home.lineup.starters[0],i=>i.away.roster.push(i.home.roster[0])]){const {input}=make();edit(input);A.ok(C.validate(input).errors.length);}
});
test('G4 unavailable lock, mutually exclusive keepers, state simplex',()=>{
 const {input}=make();input.players[0].unavailable=true;A.ok(C.validate(input).errors.length);input.players[0].projection.start=0;A.deepEqual(C.validate(input).errors,[]);
 input.players[1].projection.start=1.1;A.ok(C.validate(input).errors.length);
 A.deepEqual(C.availability({start:.5,sub:.2,vote_given_start:.9,vote_given_sub:.5,kind:'HEURISTIC'}),{start:.5,sub:.2,vote:.55,sv:.44999999999999996,kind:'HEURISTIC'});
});
test('G5 shared match goals conserved, assists linked, keeper opposition and exclusivity',()=>{
 const {input}=make(),m=S.compile(input),rand=S.rng(7);
 for(let j=0;j<2000;j++) {
  const s=S.scenario(m,rand),match=s.matches.test,ps=s.players;
  A.equal(match.events.length,match.home+match.away);
  A.ok(input.players.filter(p=>p.role==='P'&&p.team==='TEST_HOME'&&ps[p.id].voted).length<=1);
  for(const p of input.players.filter(p=>p.role==='P'))if(ps[p.id].voted)A.equal(ps[p.id].conceded,p.team==='TEST_HOME'?match.away:match.home);
  for(const e of match.events){if(e.scorer&&e.assister)A.notEqual(e.scorer,e.assister);if(e.scorer)A.equal(m.players[e.scorer].team,e.team);}
  for(const team of ['TEST_HOME','TEST_AWAY'])A.ok(input.players.filter(p=>p.team===team).reduce((sum,p)=>sum+ps[p.id].goals,0)<=(team==='TEST_HOME'?match.home:match.away));
 }
});
test('G7 display bench order has priority across roles and maximum 5 substitutions',()=>{
 const {input}=make(),ps=S.compile(input).players,l=input.home.lineup,s=states(input);
 l.starters.slice(0,7).forEach(id=>s[id].voted=false);
 const r=C.score(l,s,ps,input.rules);A.equal(r.changes,3);A.equal(r.missing,4);
 const seven=structuredClone(l);seven.bench=[];
 seven.starters.slice(0,7).forEach((id,j)=>{const b='reserve'+j;ps[b]={...ps[id],id:b};s[b]={voted:true,pure:6,fp:6};seven.bench.push(b);});
 A.equal(C.score(seven,s,ps,input.rules).changes,5);A.equal(C.score(seven,s,ps,input.rules).missing,2);
 const {input:i}=make(),p=S.compile(i).players,x=states(i),q=i.home.lineup;i.rules.substitution_count=1;
 q.starters.filter(id=>p[id].role==='C'||p[id].role==='A').forEach(id=>x[id].voted=false);
 q.bench.sort((a,b)=>Number(p[b].role==='A')-Number(p[a].role==='A'));
 const out=C.score(q,x,p,i.rules);A.ok(out.xi.includes(q.bench.find(id=>p[id].role==='A')));A.equal(out.changes,1);
});
test('G9 modifier requires four rated defenders after substitutions and pure votes',()=>{
 const {input,candidates}=make(),ps=S.compile(input).players,s=states(input,6.5,15),r=input.rules;
 A.equal(C.score(candidates.find(l=>C.formation(l.starters,ps)==='3-5-2'),s,ps,r).modifier,0);
 const l=input.home.lineup;A.equal(C.score(l,s,ps,r).modifier,3);
 r.substitution_count=0;s[l.starters.find(id=>ps[id].role==='D')].voted=false;A.equal(C.score(l,s,ps,r).modifier,0);
});
test('G10 captain SV uses vice, replacements do not inherit marker',()=>{
 const {input}=make(),ps=S.compile(input).players,s=states(input,7),l=input.home.lineup;
 s[l.captain].voted=false;s[l.vice].pure=6;A.equal(C.score(l,s,ps,input.rules).captain,0);
 s[l.vice].voted=false;A.equal(C.score(l,s,ps,input.rules).captain,0);
});
test('seed replay identical and winner/draw/loss simplex',()=>{
 const {input,candidates}=make(),a=S.evaluate(input,candidates.slice(0,2),{iterations:300,seed:1}),b=S.evaluate(input,candidates.slice(0,2),{iterations:300,seed:1});A.deepEqual(a,b);
 a.results.forEach(r=>A.ok(Math.abs(r.win+r.draw+r.loss-1)<1e-12));A.equal(a.gold,false);A.equal(a.status,'SYNTHETIC_TEST_ONLY');
});
test('G13 sample count and seed validation; blocked input has zero runs',()=>{const {input,candidates}=make();for(const options of [{iterations:99},{seed:-1},{seed:2**32},{iterations:500001}])A.throws(()=>S.evaluate(input,candidates,options));input.rules.captain=null;A.equal(S.evaluate(input,candidates).simulation_count,0);});
test('optimizer values wins over means: constructed threshold counterexample',()=>{
 // Against 70 points, 69 always loses. A 74/60 mix averages 67 yet wins half.
 const opponent=C.goals(70),scores=[[69,69],[74,60]],results=scores.map(xs=>({win:xs.filter(x=>C.goals(x)>opponent).length/xs.length,draw:xs.filter(x=>C.goals(x)===opponent).length/xs.length,incomplete_probability:0,points:{mean:xs.reduce((a,b)=>a+b,0)/xs.length}}));
 A.equal(O.rankResults(results)[0].index,1);A.ok(results[1].points.mean<results[0].points.mean);
});
test('exhaustive enumerate small roster across forms, rejects huge joint search',()=>{
 const {input}=make();input.rules.captain.enabled=false;const panel=O.enumerate(input,{max_candidates:1000});A.ok(panel.candidates.length>14);A.equal(panel.scope.global_joint_optimum_searched,false);
 A.throws(()=>O.enumerate(input,{bench:'ALL',captains:'ALL'}),/BUDGET_EXCEEDED/);
 const roster=input.home.lineup.starters;input.home.roster=roster;input.home.lineup.bench=[];input.rules.formations=['4-4-2'];const all=O.enumerate(input,{bench:'ALL',captains:'ALL'});A.equal(all.candidates.length,1);A.equal(all.scope.global_joint_optimum_searched,true);
});
test('optimizer uses separate holdout seed and identifies explicit panel scope',()=>{const {input,candidates}=make(),r=O.optimize(input,candidates.slice(0,2),{iterations:100,seed:8});A.notEqual(r.seed,r.holdout.seed);A.equal(r.scope.global_joint_optimum_searched,false);A.equal(r.holdout.results.length,2);});
test('freshness confidence decays without inventing new probabilities',()=>{const {input}=make(),a=C.freshness(input.sources[0],input.as_of),b=C.freshness(input.sources[0],'2026-01-03T10:00:00Z');A.ok(b.confidence<a.confidence);A.equal(b.needs_refresh,true);});
test('Bayesian updates reject future labels',()=>{const o=[{voted:true,observed_at:'2026-01-01'}];A.equal(D.betaVotePosterior(1,1,o,'2026-01-02').mean,2/3);A.throws(()=>D.betaVotePosterior(1,1,o,'2025-01-01'));});
test('Brier, log loss and calibration tested against known values',()=>{
 const r=D.metrics([{probabilities:[1,0,0],outcome:0,expected_points:70,actual_points:72}]);A.equal(r.brier_multiclass,0);A.equal(r.log_loss,0);A.equal(r.mae_fantapoints,2);A.equal(r.win_calibration_error,0);A.equal(r.vote_brier,null);
 A.equal(D.metrics([{probabilities:[0,1,0],outcome:0,expected_points:70,actual_points:70}]).log_loss,Infinity);
});
test('rolling folds never expose held-out labels or unfinished rounds',()=>{
 const rounds=[1,2,3].map(j=>({round:j,lock_at:`2026-01-0${j}T10:00:00Z`,completed_at:`2026-01-0${j}T20:00:00Z`,features_as_of:`2026-01-0${j}T09:00:00Z`,features:{j},actual:{outcome:0,actual_points:70}}));
 const r=D.rollingBacktest(rounds,h=>{A.ok(h.length<3);return h.length;},(model,features)=>{A.equal(features.actual,undefined);A.equal(features.j,model+1);return {probabilities:[1,0,0],expected_points:70};});A.equal(r.rows.length,2);
 rounds[2].features_as_of='2027-01-01';A.throws(()=>D.rollingBacktest(rounds,()=>0,()=>0));
});
test('G16 G7 outcomes retained as observations only, oracle diagnoses supplied panel',()=>{
 const data=require('./g7-observed.json');A.equal(data.mode,'POST_MATCH_OBSERVED_ONLY');A.equal(data.results.Gaetano,10);
 const {input,candidates}=make(),s=states(input);const r=D.postmatchOracle(input,s,candidates);A.equal(r.predictable_regret,null);A.ok(r.regret_points>=0);
});
test('LIVE what-if never randomizes observed state; ongoing simulation blocked',()=>{
 const {input}=make(),s=states(input),before=structuredClone(s),id=input.home.lineup.starters[1];input.rules.defence.enabled=false;input.rules.captain.enabled=false;
 const r=D.liveWhatIf(input,s,[{id,fp_delta:3,pure_delta:0}]);A.deepEqual(s,before);A.equal(r.home.base,69);A.equal(r.away.base,66);A.equal(r.home.goals,r.away.goals);A.equal(r.win_probability,null);
 input.mode='LIVE';A.equal(S.evaluate(input,[input.home.lineup]).simulation_count,0);
});
test('candidate HTML script syntax, unique IDs, explicit synthetic entry and no paid endpoints',()=>{
 const fs=require('node:fs'),vm=require('node:vm'),html=fs.readFileSync(require('node:path').join(__dirname,'index.html'),'utf8');
 for(const m of html.matchAll(/<script>([\s\S]*?)<\/script>/g))new vm.Script(m[1]);
 const ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);A.equal(new Set(ids).size,ids.length);
 A.ok(html.includes('CANDIDATO V3.2'));A.ok(html.includes('Apri il test sintetico'));A.ok(!html.includes('https://'));
});
test('frozen runner refuses existing output directory without overwriting input',()=>{
 const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),{main}=require('./run');
 const temp=fs.mkdtempSync(path.join(os.tmpdir(),'fs-freeze-')),file=path.join(temp,'input.json');fs.writeFileSync(file,'original');
 try{A.throws(()=>main(['--synthetic',temp,'100','1']),/EEXIST/);A.equal(fs.readFileSync(file,'utf8'),'original');}finally{fs.rmSync(temp,{recursive:true});}
});
