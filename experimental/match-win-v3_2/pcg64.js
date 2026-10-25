'use strict';
const crypto=require('node:crypto');
const MASK64=(1n<<64n)-1n,MASK128=(1n<<128n)-1n;
const MULTIPLIER=47026247687942121848144207491837523525n;
class PCG64 {
 constructor(state,increment) {
  if(typeof state!=='bigint'||typeof increment!=='bigint'||state<0n||state>MASK128||increment<0n||increment>MASK128||!(increment&1n))throw Error('PCG64 requires uint128 state and odd increment');
  this.state=state;this.increment=increment;
 }
 raw() {
  this.state=(this.state*MULTIPLIER+this.increment)&MASK128;
  const x=((this.state>>64n)^this.state)&MASK64,rot=this.state>>122n;
  return ((x>>rot)|(x<<((-rot)&63n)))&MASK64;
 }
 random(){return Number(this.raw()>>11n)/9007199254740992;}
}
function scenarioStreams(masterSeed,scenarioNumber) {
 if(!Number.isSafeInteger(masterSeed)||masterSeed<0||!Number.isSafeInteger(scenarioNumber)||scenarioNumber<0)throw Error('Nonnegative integer seed/scenario required');
 const cache=new Map();
 return (...entity)=>{
  const key=JSON.stringify(entity);if(cache.has(key))return cache.get(key);
  // Versioned, length-delimited JSON. This is explicit-state seeding, not NumPy SeedSequence.
  const digest=crypto.createHash('sha256').update(JSON.stringify(['FS_PCG64_ENTITY_SCENARIO_V1',masterSeed,scenarioNumber,...entity])).digest('hex');
  const generator=new PCG64(BigInt('0x'+digest.slice(0,32)),BigInt('0x'+digest.slice(32))|1n);
  const draw=()=>generator.random();cache.set(key,draw);return draw;
 };
}
module.exports={PCG64,scenarioStreams};
