'use strict';
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'../..');
const {example}=require(path.join(root,'experimental/match-win-v3_2/example'));
const C=require(path.join(root,'experimental/match-win-v3_2/core'));
const {input,candidates}=example();
input.as_of='2026-10-18T21:10:00Z';input.deadline='2026-10-19T10:00:00Z';
input.fixtures[0].kickoff='2026-10-19T12:00:00Z';input.fixtures[0].disruption_probability=0;
input.sources[0].observed_at='2026-10-18T21:05:00Z';
input.rules.league_config=JSON.parse(fs.readFileSync(path.join(root,'league_config.yaml'),'utf8'));
input.rules.vote_model='EXPLICIT_DISCRETE_PMF';
for(const p of input.players){
 const x=p.projection;if(p.role!=='P')x.start=1;
 x.sub=0;x.vote_given_start=1;x.vote_given_sub=1;x.disruption_sensitivity=0;
 x.team_vote_loading=0;x.conceded_vote_loading=0;x.observed_at=input.sources[0].observed_at;
 x.vote_pmf=[['5',.1],['5.5',.15],['6',.3],['6.5',.25],['7',.15],['7.5',.05]].map(([vote,probability])=>({vote,probability}));
}
const players=Object.fromEntries(input.players.map(p=>[p.id,p]));
const panel=['4-4-2','3-5-2'].map(form=>candidates.find(l=>C.formation(l.starters,players)===form));
fs.writeFileSync(path.join(__dirname,'synthetic-pmf-input.json'),JSON.stringify({input,candidates:panel},null,2)+'\n',{flag:'wx'});
console.log('Synthetic inputs only; PMFs invented for integration testing, not real forecasts.');
