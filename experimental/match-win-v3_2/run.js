#!/usr/bin/env node
'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),cp=require('node:child_process');
const C=require('./core'),O=require('./optimizer'),{example}=require('./example');
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const ROOT=path.resolve(__dirname,'../..');
function main(args) {
 const synthetic=args[0]==='--synthetic',output=path.resolve(args[1]||path.join(__dirname,'runs',synthetic?'synthetic':'input'));
 let input,candidates;
 if(synthetic)({input,candidates}=example());
 else {if(!args[0])throw Error('Usage: node run.js --synthetic|input.json NEW_OUTPUT_DIR [iterations] [seed]');const raw=JSON.parse(fs.readFileSync(args[0],'utf8'));input=raw.input||raw;candidates=raw.candidates||[input.home?.lineup];}
 const iterations=Number(args[2]||100000),seed=Number(args[3]||20261018),start=performance.now();
 // Output directories cannot overwrite a frozen forecast. Hashes are tamper-evidence,
 // not a claim that ordinary local files are a write-once storage service.
 fs.mkdirSync(path.dirname(output),{recursive:true});fs.mkdirSync(output);
 const codeFiles=fs.readdirSync(__dirname).filter(x=>x.endsWith('.js')).sort(),code=Object.fromEntries(codeFiles.map(f=>[f,hash(fs.readFileSync(path.join(__dirname,f)))]));
 const payload={input,candidates},inputJSON=JSON.stringify(payload,null,2)+'\n';
 fs.writeFileSync(path.join(output,'input.json'),inputJSON,{flag:'wx'});
 const report=O.optimize(input,candidates,{iterations,seed});
 report.context={round:input.round,opponent:input.away?.name??null,as_of:input.as_of,
  players:Object.fromEntries((input.players||[]).map(p=>{const f=(input.fixtures||[]).find(f=>f.id===p.fixture_id);return [p.id,{name:p.name??p.id,role:p.role,fixture:f?f.home+' – '+f.away:null}];}))};
 report.execution={input_sha256:hash(inputJSON),code_sha256:code,base_commit:cp.execFileSync('git',['rev-parse','HEAD'],{cwd:ROOT,encoding:'utf8'}).trim(),elapsed_ms:performance.now()-start,cost_incurred_eur:0};
 const reportJSON=JSON.stringify(report,null,2)+'\n';fs.writeFileSync(path.join(output,'report.json'),reportJSON,{flag:'wx'});
 fs.writeFileSync(path.join(output,'manifest.json'),JSON.stringify({schema:'FS_FROZEN_RUN_V1',files:{'input.json':hash(inputJSON),'report.json':hash(reportJSON)},code_sha256:code,gold:false},null,2)+'\n',{flag:'wx'});
 console.log(JSON.stringify({status:report.status,simulation_count:report.simulation_count,holdout_count:report.holdout?.simulation_count??0,candidates:report.results?.length??0,elapsed_ms:report.execution.elapsed_ms,gold:false,output},null,2));
}
if(require.main===module)main(process.argv.slice(2));module.exports={main,hash};
