'use strict';
// Diagnostic probes: a failure of a target requirement is a finding, not a green gate.
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'../..');
const C=require(root+'/experimental/match-win-v3_2/core');
const S=require(root+'/experimental/match-win-v3_2/simulator');
const O=require(root+'/experimental/match-win-v3_2/optimizer');
const {example}=require(root+'/experimental/match-win-v3_2/example');
const {input,candidates}=example();
const selected=[candidates[0],candidates[2]];
const normal=S.evaluate(input,selected,{iterations:2000,seed:20261018});
const reversed=structuredClone(input);reversed.players.reverse();
const permuted=S.evaluate(reversed,selected,{iterations:2000,seed:20261018});
const first=normal.results.map(r=>({win:r.win,mean:r.points.mean}));
const second=permuted.results.map(r=>({win:r.win,mean:r.points.mean}));
const tied=[{id:'A',win:.5,draw:.2,incomplete_probability:0,points:{mean:70}},{id:'B',win:.5,draw:.2,incomplete_probability:0,points:{mean:70}}];
const a=O.rankResults(tied)[0].id,b=O.rankResults(tied.slice().reverse())[0].id;
const noRules=structuredClone(input);noRules.rules.captain=null;
const blocked=S.evaluate(noRules,selected,{iterations:100,seed:1});
const thresholds=[65.9,66,69.4,70,94,98,102].map(p=>({points:p,goals:C.goals(p)}));
const result={
 reviewed_commit:'2122699104f8923eb65d9f4c7491d4bcf48306f2',
 player_permutation:{target_pass:JSON.stringify(first)===JSON.stringify(second),original:first,reversed:second,scope:'Exact seeded outcome invariance; not a test of distributional bias.'},
 candidate_tie_order:{target_pass:a===b,original_winner:a,reversed_winner:b},
 missing_rule:{fail_closed_pass:blocked.simulation_count===0,status:blocked.status,gold:blocked.gold},
 thresholds,goal_implementation:{configurable:false,decimal_exact:false,binary_number:true},
 prng:{pcg64:false,state_bits:32,source:'experimental/match-win-v3_2/simulator.js:rng'},
 source:'Read-only executable probes against the inspected candidate.'
};
fs.writeFileSync(path.join(__dirname,'probes.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));
