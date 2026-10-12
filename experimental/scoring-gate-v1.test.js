'use strict';
const a=require('node:assert/strict'),s=require('./scoring-gate-v1');let n=0;
function test(name,fn){fn();n++;console.log('PASS',name)}
for(const [p,g] of [[65.9,0],[66,1],[69.9,1],[70,2],[73.9,2],[74,3],[77.9,3],[78,4],[94,8]])test('goals '+p,()=>a.equal(s.goals(p),g));
const def=v=>[{id:'p',role:'P',pureVote:v},...Array.from({length:4},(_,i)=>({id:'d'+i,role:'D',pureVote:v}))];
for(const [v,b] of [[6.24,0],[6.25,.5],[6.5,1],[6.75,1.5],[7,2]])test('defense '+v,()=>a.equal(s.defenseModifier(def(v)),b));
test('top three defenders',()=>{const xi=def(6.5);xi[4].pureVote=3;a.equal(s.defenseModifier(xi),1)});
test('fewer than four defenders',()=>a.equal(s.defenseModifier(def(7).slice(0,4)),0));
for(const [v,b] of [[4.5,-1.5],[5,-1],[5.5,0],[6.5,0],[7,1],[7.5,1.5]])test('captain '+v,()=>a.equal(s.captainFactor([{id:'c',pureVote:v}],'c','v'),b));
test('vice on captain SV',()=>a.equal(s.captainFactor([{id:'c',pureVote:null},{id:'v',pureVote:7.5}],'c','v'),1.5));
test('bench role order',()=>{const r=s.substitute([{id:'c',role:'C',pureVote:null}],[{id:'d',role:'D',pureVote:7},{id:'c1',role:'C',pureVote:6},{id:'c2',role:'C',pureVote:8}]);a.equal(r.xi[0].id,'c1')});
test('skip SV substitute',()=>{const r=s.substitute([{id:'c',role:'C',pureVote:null}],[{id:'c1',role:'C',pureVote:null},{id:'c2',role:'C',pureVote:7}]);a.equal(r.xi[0].id,'c2')});
test('five replacements maximum',()=>{const x=Array.from({length:6},(_,i)=>({id:'s'+i,role:'C',pureVote:null})),b=Array.from({length:6},(_,i)=>({id:'b'+i,role:'C',pureVote:6}));const r=s.substitute(x,b);a.equal(r.changes,5);a.equal(r.unfilled,1)});
test('block unverified bonus/malus',()=>a.throws(()=>s.score([],{}),/BLOCKED_BONUS_MALUS_UNVERIFIED/));
test('score complete',()=>{const xi=[...def(7),...Array.from({length:6},(_,i)=>({id:'c'+i,role:'C',pureVote:6}))].map(x=>({...x,fantavote:x.pureVote}));const r=s.score(xi,{bonusMalusVerified:true,captainId:'p'});a.equal(r.base,71);a.equal(r.modifier,2);a.equal(r.captain,1);a.equal(r.goals,3)});
console.log('TOTAL',n,'PASS');
