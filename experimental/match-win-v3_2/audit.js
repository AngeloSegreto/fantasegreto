#!/usr/bin/env node
'use strict';
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),{hash}=require('./run');
const ROOT=path.resolve(__dirname,'../..'),BASE='fa9562decb683a3d64ca248cb66ff20099ddcb54';
function main(){
 const checks=[];
 for(const [name,cmd,args] of [
  ['candidate_tests','node',['--test','experimental/match-win-v3_2/test.js']],
  ['legacy_simulator','node',['premium-monte-carlo-v1.test.js']],
  ['legacy_scoring','node',['experimental/scoring-gate-v1.test.js']],
  ['official_runtime','python',['tools/validate_official_runtime.py']],
  ['official_parity','python',['tools/validate_13oct_offline.py']]]) {
  const p=cp.spawnSync(cmd,args,{cwd:ROOT,encoding:'utf8'});fs.writeFileSync(path.join(__dirname,name+'.log'),p.stdout+p.stderr);checks.push({name,pass:p.status===0,exit_code:p.status});
 }
 const protectedPaths=['engine.js','app.js','index.html','sw.js','registry.json','version.json','premium-monte-carlo-v1.js','experimental/scoring-gate-v1.js','FS_PREMIUM_MATCH_EVIDENCE_V1.json'];
 const integrity=protectedPaths.map(p=>{const original=cp.execFileSync('git',['show',BASE+':'+p],{cwd:ROOT});const current=fs.readFileSync(path.join(ROOT,p));return {path:p,base_sha256:hash(original),current_sha256:hash(current),identical:hash(original)===hash(current)};});
 const runs=['synthetic','real-readiness'].map(name=>{
  const dir=path.join(__dirname,'runs',name),manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json'))),report=JSON.parse(fs.readFileSync(path.join(dir,'report.json')));
  const files_ok=Object.entries(manifest.files).every(([f,h])=>hash(fs.readFileSync(path.join(dir,f)))===h);
  const code_ok=Object.entries(manifest.code_sha256).every(([f,h])=>hash(fs.readFileSync(path.join(__dirname,f)))===h);
  return {name,files_ok,code_ok,status:report.status,simulation_count:report.simulation_count,holdout_count:report.holdout?.simulation_count??0,convergence:report.results?.every(r=>r.convergence.pass)??null};
 });
 const ui=JSON.parse(fs.readFileSync(path.join(__dirname,'ui-audit.json'))),ok=checks.every(c=>c.pass)&&integrity.every(c=>c.identical)&&runs.every(r=>r.files_ok&&r.code_ok)&&(runs[0].convergence===true);
 const evidence={base_commit:BASE,technical_status:ok?'PASS_RC_SCOPE':'FAIL',gold:false,promoted:false,incremental_paid_compute_eur:0,checks,integrity,runs,ui,
  gates:[
   ['G0','PARTIAL','Provenance validation tested; live authoritative source ingestion pending'],
   ['G1','PARTIAL','Fixture identity/time checks tested; current calendar acquisition pending'],
   ['G2','PASS_TECHNICAL','539 official runtime identities verified; candidate input schema tested'],
   ['G3','PASS_TECHNICAL','All seven formations validated; exhaustive search bounded and explicitly scoped'],
   ['G4','PARTIAL','Availability simplex, unavailable lock, Beta update; current calibrated probabilities pending'],
   ['G5','PARTIAL','Shared goals, linked assist events and exclusive keepers tested; red-card game-state feedback and substitution minutes pending'],
   ['G6','PASS_TECHNICAL','Finite/domain checks and result simplex'],
   ['G7','PARTIAL','Five same-role changes and display-order priority tested; National League exceptional SV rules pending'],
   ['G8','PASS_TECHNICAL','Strict 66 + 4 fixed bands tested at boundaries'],
   ['G9','PARTIAL','Per-scenario pure-vote modifier implemented; official bands pending'],
   ['G10','PARTIAL','Configurable captain/vice implemented; official bands and exceptional SV handling pending'],
   ['G11','PARTIAL','Keeper event distributions implemented; real Meret/Gollini/Svilar comparison pending current sources'],
   ['G12','PARTIAL','Future sources rejected; immutable-by-run convention; LIVE scoring-only, residual event adapter pending'],
   ['G13','PASS_SYNTHETIC','100k shared selection draws + 100k independent holdout; half-sample consistency and MC errors reported'],
   ['G14','PENDING','Metrics implemented and tested; actual calibration history missing'],
   ['G15','PENDING','Rolling harness tested; real temporal backtest not run'],
   ['G16','PARTIAL','Legacy regression suites pass; G7 observations archived, complete official oracle pending'],
   ['G17','PENDING','Excel/PWA scoring parity not executed'],
   ['G18',ui.status==='PASS_CHROMIUM_AUTOMATED_ONLY'?'PARTIAL':'PENDING',ui.status==='PASS_CHROMIUM_AUTOMATED_ONLY'?'Chromium three widths tested; physical iPhone Safari pending':'Browser executable unavailable and download unsuccessful; UI script provided but browser acceptance not executed'],
   ['G19','PARTIAL','Protected production files identical, candidate manifests checked; release promotion blocked']
  ].map(([id,status,evidence])=>({id,status,evidence}))};
 fs.writeFileSync(path.join(__dirname,'release-audit.json'),JSON.stringify(evidence,null,2)+'\n');console.log(JSON.stringify({technical_status:evidence.technical_status,gold:false,tests:checks,runs},null,2));if(!ok)process.exitCode=1;
}
if(require.main===module)main();module.exports={main};
