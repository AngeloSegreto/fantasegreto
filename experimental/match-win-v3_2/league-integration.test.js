'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const C=require('./core'),S=require('./simulator'),{example}=require('./example'),{exactGoals}=require('./league-rules');
const config=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../../league_config.yaml'),'utf8'));
function fixture(vote='6',fp=vote) {
 const {input,candidates}=example();input.rules.league_config=structuredClone(config);
 input.as_of='2026-10-18T21:10:00Z';input.deadline='2026-10-19T10:00:00Z';input.fixtures[0].kickoff='2026-10-19T12:00:00Z';
 const players=Object.fromEntries(input.players.map(p=>[p.id,p]));
 const scenario=Object.fromEntries(input.players.map(p=>[p.id,{voted:true,pure:vote,fp}]));
 return {input,candidates,players,scenario,lineup:input.home.lineup};
}
test('core.score consumes acquired defense/captain settings instead of synthetic bands',()=>{
 const {input,players,scenario,lineup}=fixture('6.5');
 input.rules.defence.bands=[{min:0,bonus:99}];input.rules.captain.bands=[{min:0,bonus:99}];
 const r=C.score(lineup,scenario,players,input.rules);
 assert.equal(r.modifier,1);assert.equal(r.captain,0);
 assert.equal(r.exact.base,'71.5');assert.equal(r.exact.total,'72.5');assert.equal(r.goals,2);
 assert.equal(r.gold,false);
});
test('full lineup uses pure captain vote, never fantasy points',()=>{
 const {input,players,scenario,lineup}=fixture('6.5');
 scenario[lineup.captain]={voted:true,pure:'7',fp:'10'};
 const r=C.score(lineup,scenario,players,input.rules);
 assert.equal(r.captain,1);assert.equal(r.modifier,1);
 assert.equal(r.exact.total,'77');assert.equal(r.goals,3);
});
test('exact observed match result uses goals separately for both sides',()=>{
 const {input,players,scenario,lineup}=fixture();
 scenario[lineup.starters.find(id=>players[id].role==='A')].fp='10';
 const h=C.score(lineup,scenario,players,input.rules),a=C.score(input.away.lineup,scenario,players,input.rules);
 assert.equal(h.exact.total,'70');assert.equal(h.goals,2);
 assert.equal(a.exact.total,'66');assert.equal(a.goals,1);
});
test('bench substitution is resolved before official modifier and does not inherit captain',()=>{
 const {input,players,scenario,lineup}=fixture('6.5');
 const replacement=lineup.bench.find(id=>players[id].role===players[lineup.captain].role);
 scenario[lineup.captain].voted=false;scenario[lineup.vice].pure='7';scenario[lineup.vice].fp='7';
 scenario[replacement].pure='8';scenario[replacement].fp='8';
 const r=C.score(lineup,scenario,players,input.rules);
 assert.equal(r.changes,1);assert.ok(r.xi.includes(replacement));
 assert.equal(r.captain,1);assert.equal(r.exact.recovered,'8');
 assert.equal(r.modifier,2);
});
test('three defenders after substitution receive no modifier',()=>{
 const {input,candidates,players,scenario}=fixture('7');
 const lineup=candidates.find(l=>C.formation(l.starters,players)==='3-5-2');
 assert.equal(C.score(lineup,scenario,players,input.rules).modifier,0);
});
test('both captain and vice SV fail without returning partial score',()=>{
 const {input,players,scenario,lineup}=fixture();
 scenario[lineup.captain].voted=false;scenario[lineup.vice].voted=false;
 assert.throws(()=>C.score(lineup,scenario,players,input.rules),/Both captain/);
});
test('SV yellow option remains unresolved inside full scoring',()=>{
 const {input,players,scenario,lineup}=fixture();
 const id=lineup.starters.find(id=>players[id].role==='D');
 scenario[id].vote_kind='SV_YELLOW';assert.throws(()=>C.score(lineup,scenario,players,input.rules),/unknown/);
});
test('unselected vice special vote does not alter valid captain',()=>{
 const {input,players,scenario,lineup}=fixture();
 scenario[lineup.vice].vote_kind='POLITICAL_SIX';
 assert.equal(C.score(lineup,scenario,players,input.rules).captain,0);
});
test('decimal scores are required by official observed route',()=>{
 const {input,players,scenario,lineup}=fixture();scenario[lineup.starters[0]].fp=6;
 assert.throws(()=>C.score(lineup,scenario,players,input.rules),/decimal string/);
});
test('exact goal mapping respects arbitrarily close finite decimal boundaries',()=>{
 for(const [score,goals] of [['65.999999999999999999999',0],['66',1],['69.999999999999999999999',1],['70',2],['94',8],['98',9]])assert.equal(exactGoals(score,config),goals);
});
test('goal thresholds come from config',()=>{
 const c=structuredClone(config);c.rules.fantasy_goals.first_goal='60';c.rules.fantasy_goals.band_width='5';
 assert.equal(exactGoals('65',c),2);
 assert.equal(exactGoals('65',config),0);
});
test('unknown goal or substitution configuration does not silently fall back',()=>{
 const {input,players,scenario,lineup}=fixture();input.rules.substitution_count=4;
 assert.throws(()=>C.score(lineup,scenario,players,input.rules),/Substitution settings/);
 const c=structuredClone(config);c.rules.fantasy_goals.band_width='0';assert.throws(()=>exactGoals('70',c),/Unsupported/);
});
test('Monte Carlo with official config blocks continuous vote mismatch before any draws',()=>{
 const {input,candidates}=fixture();const r=S.evaluate(input,candidates,{iterations:100,seed:1});
 assert.equal(r.status,'BLOCKED_PENDING_VOTE_MODEL_AND_RULE_EXCEPTIONS');assert.equal(r.simulation_count,0);
 assert.equal(r.gold,false);assert.equal(r.results,undefined);
});
function discreteFixture() {
 const f=fixture();f.input.rules.vote_model='EXPLICIT_DISCRETE_PMF';
 f.input.fixtures[0].disruption_probability=0;
 for(const p of f.input.players) {
  const x=p.projection;if(p.role!=='P')x.start=1;
  x.sub=0;x.vote_given_start=1;x.vote_given_sub=1;
  x.team_vote_loading=0;x.conceded_vote_loading=0;
  x.vote_pmf=[{vote:'6',probability:.5},{vote:'7',probability:.5}];
 }
 return f;
}
test('discrete Monte Carlo uses actual rules on shared scenarios with reproducible seed',()=>{
 const {input,candidates}=discreteFixture();
 const a=S.evaluate(input,candidates.slice(0,2),{iterations:100,seed:42});
 const b=S.evaluate(input,candidates.slice(0,2),{iterations:100,seed:42});
 assert.equal(a.status,'SYNTHETIC_TEST_ONLY');assert.equal(a.simulation_count,100);assert.deepEqual(a,b);
 for(const r of a.results){assert.ok(r.expected_defence_modifier>=0&&r.expected_defence_modifier<=2);assert.ok(Math.abs(r.win+r.draw+r.loss-1)<1e-12);}
 assert.equal(a.gold,false);
});
test('fixed discrete votes produce the acquired modifier inside every Monte Carlo scenario',()=>{
 const {input,candidates}=discreteFixture();
 for(const p of input.players)p.projection.vote_pmf=[{vote:'6.5',probability:1}];
 const r=S.evaluate(input,candidates.slice(0,1),{iterations:100,seed:2});
 assert.equal(r.results[0].expected_defence_modifier,0); // First candidate is 3-5-2.
 const four=candidates.find(l=>C.formation(l.starters,Object.fromEntries(input.players.map(p=>[p.id,p])))==='4-4-2');
 const full=S.evaluate(input,[four],{iterations:100,seed:2});
 assert.equal(full.results[0].expected_defence_modifier,1);assert.equal(full.results[0].expected_captain,0);
});
test('unknown SV scenario blocks all results instead of dropping unsuccessful samples',()=>{
 const {input,lineup}=discreteFixture();
 for(const id of [lineup.captain,lineup.vice])input.players.find(p=>p.id===id).projection.start=0;
 const r=S.evaluate(input,[lineup],{iterations:100,seed:1});
 assert.equal(r.status,'BLOCKED_UNRESOLVED_LEAGUE_SCENARIO');assert.equal(r.attempted_scenarios,1);
 assert.equal(r.discarded_partial_results,true);assert.equal(r.results,undefined);
});
test('invalid or missing PMF cannot fall back to normal votes',()=>{
 for(const pmf of [null,[null],[{vote:'6',probability:.8}],[{vote:'11',probability:1}]]){
  const {input,candidates}=discreteFixture();input.players[0].projection.vote_pmf=pmf;
  const r=S.evaluate(input,candidates.slice(0,1),{iterations:100,seed:1});
  assert.equal(r.simulation_count,0);assert.equal(r.results,undefined);
 }
});
test('rule snapshots acquired after forecast as_of are rejected',()=>{
 const {input,candidates}=discreteFixture();input.as_of='2026-01-01T10:00:00Z';
 const r=S.evaluate(input,candidates.slice(0,1),{iterations:100,seed:1});
 assert.equal(r.simulation_count,0);assert.ok(r.errors.some(e=>e.includes('received after')));
});
test('failed independent confirmation releases no recommendation',()=>{
 const {input,candidates}=discreteFixture(),O=require('./optimizer');
 const development=S.evaluate(input,candidates.slice(0,2),{iterations:100,seed:1});
 const original=S.evaluate;let calls=0;
 try {
  S.evaluate=()=>++calls===1?development:{status:'BLOCKED_UNRESOLVED_LEAGUE_SCENARIO',errors:['unknown SV'],simulation_count:0,attempted_scenarios:1,gold:false};
  const result=O.optimize(input,candidates.slice(0,2),{iterations:100,seed:1});
  assert.equal(result.status,'BLOCKED_INDEPENDENT_CONFIRMATION');assert.equal(result.recommended_index,null);
  assert.equal(result.ranking,undefined);assert.equal(result.results,undefined);
 }finally{S.evaluate=original;}
});
test('real input cannot use old synthetic scoring configuration',()=>{
 const {input,candidates}=example();input.kind='REAL';
 const result=S.evaluate(input,candidates.slice(0,1),{iterations:100,seed:1});
 assert.equal(result.simulation_count,0);assert.ok(result.errors.some(e=>e.includes('acquired league configuration')));
});
