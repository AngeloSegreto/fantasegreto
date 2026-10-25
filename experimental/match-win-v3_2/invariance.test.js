'use strict';
const test=require('node:test'),A=require('node:assert/strict');
const {example}=require('./example'),S=require('./simulator'),C=require('./core'),O=require('./optimizer');
const {decisionIdentity}=require('./decision-id');
const stats=r=>{const {lineup,paired_to_first,...rest}=r;return rest;};
test('seeded numeric outcomes no longer depend on player record order',()=>{
 const {input,candidates}=example(),reversed=structuredClone(input);reversed.players.reverse();
 const a=S.evaluate(input,candidates.slice(0,2),{iterations:2000,seed:20261018});
 const b=S.evaluate(reversed,candidates.slice(0,2),{iterations:2000,seed:20261018});
 A.deepEqual(a.results,b.results);A.deepEqual(a.keepers,b.keepers);
});
test('random event scenario is identical after record reversal without mutating caller',()=>{
 const {input}=example(),reversed=structuredClone(input);reversed.players.reverse();
 const before=structuredClone(reversed);
 const a=S.scenario(S.compile(input),S.rng(99)),b=S.scenario(S.compile(reversed),S.rng(99));
 A.deepEqual(a,b);A.deepEqual(reversed,before);
});
test('candidate reversal preserves each full decision statistics',()=>{
 const {input,candidates}=example(),panel=candidates.slice(0,3);
 const a=S.evaluate(input,panel,{iterations:300,seed:7});
 const b=S.evaluate(input,panel.slice().reverse(),{iterations:300,seed:7});
 const map=r=>Object.fromEntries(r.results.map(v=>[decisionIdentity(v.lineup),stats(v)]));
 A.deepEqual(map(a),map(b));
});
test('starter permutation preserves full score and identity',()=>{
 const {input}=example(),lineup=input.home.lineup,reversed=structuredClone(lineup);reversed.starters.reverse();
 const players=S.compile(input).players,scenario=S.scenario(S.compile(input),S.rng(18)).players;
 A.deepEqual(C.score(lineup,scenario,players,input.rules),C.score(reversed,scenario,players,input.rules));
 A.equal(decisionIdentity(lineup),decisionIdentity(reversed));
});
test('operational bench order remains part of decision identity',()=>{
 const {input}=example(),a=input.home.lineup,b=structuredClone(a);b.bench.reverse();
 A.notEqual(decisionIdentity(a),decisionIdentity(b));
});
test('captain and vice are part of decision identity',()=>{
 const {input}=example(),a=input.home.lineup,b=structuredClone(a);[b.captain,b.vice]=[b.vice,b.captain];
 A.notEqual(decisionIdentity(a),decisionIdentity(b));
});
test('exact tie is decided by full identity, not array index',()=>{
 const {candidates}=example();
 const result=lineup=>({lineup,win:.4,draw:.2,incomplete_probability:0,points:{mean:70}});
 const a=result(candidates[0]),b=result(candidates[1]);
 const ab=O.rankResults([a,b])[0],ba=O.rankResults([b,a])[0];
 A.equal(ab.decision_id,ba.decision_id);
 A.equal(ab.decision_id,[decisionIdentity(a.lineup),decisionIdentity(b.lineup)].sort()[0]);
});
test('fixture traversal is canonical',()=>{
 const {input}=example();
 input.fixtures.push({...input.fixtures[0],id:'z',home:'UNMODELED_HOME',away:'UNMODELED_AWAY'});
 const reverse=structuredClone(input);reverse.fixtures.reverse();
 A.deepEqual(S.scenario(S.compile(input),S.rng(4)),S.scenario(S.compile(reverse),S.rng(4)));
});
test('duplicate IDs cannot produce an ambiguous identity',()=>{
 const {input}=example(),lineup=structuredClone(input.home.lineup);lineup.bench.push(lineup.starters[0]);
 A.throws(()=>decisionIdentity(lineup),/Unique/);
});
test('JSON encoding prevents delimiter ambiguity in captain/vice IDs',()=>{
 const {input}=example(),a=structuredClone(input.home.lineup),b=structuredClone(a);
 a.captain='x|Vice:y';a.vice='z';b.captain='x';b.vice='y|Vice:z';
 A.notEqual(decisionIdentity(a),decisionIdentity(b));
});
