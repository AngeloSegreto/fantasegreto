'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),cp=require('node:child_process');
const root=path.resolve(__dirname,'../..');
const engine=path.join(root,'experimental/match-win-v3_2');
const {example}=require(path.join(engine,'example')),S=require(path.join(engine,'simulator')),
 O=require(path.join(engine,'optimizer')),{decisionIdentity}=require(path.join(engine,'decision-id'));
const {input,candidates}=example(),reverse=structuredClone(input);reverse.players.reverse();
const options={iterations:2000,seed:20261018};
const a=S.evaluate(input,candidates.slice(0,2),options),b=S.evaluate(reverse,candidates.slice(0,2),options);
const equal=JSON.stringify(a.results)===JSON.stringify(b.results);
const tie=l=>({lineup:l,win:.4,draw:.2,incomplete_probability:0,points:{mean:70}});
const ab=O.rankResults(candidates.slice(0,2).map(tie)),ba=O.rankResults(candidates.slice(0,2).reverse().map(tie));
const stable=ab[0].decision_id===ba[0].decision_id;
const report={schema:'FS_V331_INVARIANCE_REGRESSION_V1',
 based_on_commit:cp.execFileSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8'}).trim(),
 options,player_record_permutation:{pass:equal,normal_wins:a.results.map(r=>r.win),reversed_wins:b.results.map(r=>r.win)},
 exact_tie_candidate_permutation:{pass:stable,normal_choice:ab[0].decision_id,reversed_choice:ba[0].decision_id},
 identity_example:decisionIdentity(candidates[0]),
 scope:'Synthetic regression only; does not certify PCG64, calibration, parity or full V3.3.1.',
 tech_pass_v331:false,stat_validated:false,gold_lock:false};
fs.writeFileSync(path.join(__dirname,'regression.json'),JSON.stringify(report,null,2)+'\n');
const args=['--test',...['test.js','league-rules.test.js','league-integration.test.js','invariance.test.js'].map(f=>path.join(engine,f))];
const tests=cp.spawnSync('node',args,{cwd:root,encoding:'utf8'});
fs.writeFileSync(path.join(__dirname,'node-tests.log'),tests.stdout+tests.stderr);
console.log(JSON.stringify({player_order_fixed:equal,tie_order_fixed:stable,node_exit:tests.status,gold_lock:false},null,2));
if(!equal||!stable||tests.status!==0)process.exitCode=1;
