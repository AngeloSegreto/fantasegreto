'use strict';
const test=require('node:test'),A=require('node:assert/strict');
const {PCG64,scenarioStreams}=require('./pcg64'),S=require('./simulator'),{example}=require('./example');
const reference=require('../../audit/v3_3_1_pcg64/numpy-vectors.json');
test('PCG64 raw uint64 and uniform outputs match independent NumPy explicit-state references',()=>{
 A.equal(reference.cases.length,100);
 for(const c of reference.cases){
  const raw=new PCG64(BigInt(c.state),BigInt(c.increment)),uniform=new PCG64(BigInt(c.state),BigInt(c.increment));
  A.deepEqual(c.raw.map(()=>raw.raw().toString()),c.raw);
  A.deepEqual(c.uniform.map(()=>uniform.random()),c.uniform);
 }
});
test('PCG64 rejects invalid or even-increment states',()=>{
 for(const [s,i] of [[-1n,1n],[1n,2n],[1n<<128n,1n],[1n,1n<<128n],[1,3n]])A.throws(()=>new PCG64(s,i));
});
test('same master seed/entity/scenario reproduces stream',()=>{
 const a=scenarioStreams(42,12)('PLAYER','p'),b=scenarioStreams(42,12)('PLAYER','p');
 A.deepEqual(Array.from({length:20},a),Array.from({length:20},b));
});
test('entity traversal order does not change individual streams',()=>{
 const a=scenarioStreams(42,12),b=scenarioStreams(42,12);
 const x=a('PLAYER','a')(),y=a('PLAYER','b')();
 A.equal(b('PLAYER','b')(),y);A.equal(b('PLAYER','a')(),x);
});
test('unrelated stream consumption cannot shift player stream',()=>{
 const a=scenarioStreams(42,12),b=scenarioStreams(42,12);
 for(let i=0;i<100;i++)a('PLAYER','unused')();
 A.equal(a('PLAYER','p')(),b('PLAYER','p')());
});
test('scenario number, master seed and domain are part of stream identity',()=>{
 const values=[scenarioStreams(42,12)('PLAYER','p')(),scenarioStreams(42,13)('PLAYER','p')(),
  scenarioStreams(43,12)('PLAYER','p')(),scenarioStreams(42,12)('MATCH','p')()];
 A.equal(new Set(values).size,4);
});
test('invalid scenario and seed are rejected',()=>{
 for(const [seed,n] of [[-1,0],[1,-1],[1,.1],[NaN,1]])A.throws(()=>scenarioStreams(seed,n));
});
test('uniform draws are finite within half-open domain',()=>{
 const draw=scenarioStreams(1,1)('PLAYER','p');
 for(let i=0;i<10000;i++){const x=draw();A.ok(Number.isFinite(x)&&x>=0&&x<1);}
});
test('adding an unavailable zero-share player does not shift existing player outcomes',()=>{
 const {input}=example(),extended=structuredClone(input),p=structuredClone(input.players.find(p=>p.role==='D'));
 p.id='new-nonparticipant';p.official_id='SYNTHETIC_NEW';p.projection.start=0;p.projection.sub=0;
 p.projection.goal_share=0;p.projection.assist_share=0;extended.players.push(p);
 const a=S.scenario(S.compile(input),null,scenarioStreams(4,9));
 const b=S.scenario(S.compile(extended),null,scenarioStreams(4,9));
 A.deepEqual(a.matches,b.matches);for(const id of Object.keys(a.players))A.deepEqual(a.players[id],b.players[id]);
});
test('evaluate exposes the actual PCG64 entity/scenario engine',()=>{
 const {input,candidates}=example(),r=S.evaluate(input,candidates.slice(0,1),{iterations:100,seed:5});
 A.equal(r.random_engine,'PCG64_XSL_RR_128_64_ENTITY_SCENARIO_V1');A.equal(r.gold,false);
});
