'use strict';
const C=require('./core');
function example() {
 const source={id:'synthetic',url:'synthetic://test-fixture-only',observed_at:'2026-01-01T09:00:00Z',reliability:1,half_life_hours:24,conflicts:[]};
 const players=[];
 for(const [prefix,team,counts] of [['h','TEST_HOME',{P:2,D:5,C:5,A:3}],['a','TEST_AWAY',{P:1,D:4,C:4,A:2}]]) {
  for(const [role,n] of Object.entries(counts))for(let k=0;k<n;k++)players.push({id:prefix+role+k,official_id:'SYNTHETIC_'+prefix+role+k,name:'TEST '+prefix+role+k,role,team,fixture_id:'test',unavailable:false,
   projection:{source_id:'synthetic',observed_at:source.observed_at,kind:'HEURISTIC',start:role==='P'?(n===2?(k===0?.7:.3):1):.85,sub:role==='P'?0:.1,
    vote_given_start:.99,vote_given_sub:.75,vote_mean:6+(role==='C'?.1:0),vote_sd:.65,
    goal_share:role==='A'?.15:role==='C'?.035:role==='D'?.01:0,assist_share:role==='A'?.07:role==='C'?.055:role==='D'?.025:0,
    yellow_probability:.12,red_probability:.015,save_rate:role==='P'?3:0,team_vote_loading:.3,
    conceded_vote_loading:['P','D'].includes(role)?-.15:0,disruption_sensitivity:.25}});
 }
 const homeRoster=players.filter(p=>p.id.startsWith('h')).map(p=>p.id),awayRoster=players.filter(p=>p.id.startsWith('a')).map(p=>p.id);
 function lineup(roster,form,keeper=0) {
  const ps=Object.fromEntries(players.map(p=>[p.id,p])),need={P:1,...Object.fromEntries(['D','C','A'].map((r,j)=>[r,Number(form.split('-')[j])]))};
  const starters=C.ROLES.flatMap(r=>roster.filter(id=>ps[id].role===r).slice(r==='P'?keeper:0,r==='P'?keeper+1:need[r]));
  return {starters,bench:roster.filter(id=>!starters.includes(id)),captain:starters[1],vice:starters[2]};
 }
 const input={kind:'SYNTHETIC',mode:'PRE_MATCH',round:1,as_of:'2026-01-01T10:00:00Z',deadline:'2026-01-01T11:00:00Z',sources:[source],
  fixtures:[{id:'test',home:'TEST_HOME',away:'TEST_AWAY',kickoff:'2026-01-01T12:00:00Z',home_goal_rate:1.6,away_goal_rate:1.1,disruption_probability:.03,source_id:'synthetic'}],players,
  rules:{verified:true,source_id:'synthetic',goal_lock:'NATIONAL_66_4_FIXED_V3_1',formations:C.FORMS,substitution_count:5,substitution_mode:'SAME_ROLE',module_change_allowed:false,bench_order:'DISPLAY_ORDER',keeper_model:'EXCLUSIVE_FULL_MATCH',
   bonus_malus:{goal:3,assist:1,yellow:-.5,red:-1,conceded:-1,save:0,clean_sheet:1},
   defence:{enabled:true,minimum_rated_defenders:4,top_defenders:3,include_keeper:true,bands:[{min:6,bonus:1},{min:6.5,bonus:3},{min:7,bonus:6}]},
   captain:{enabled:true,sv_policy:'VICE_THEN_ZERO',basis:'PURE_VOTE',bands:[{min:0,bonus:-1},{min:6,bonus:0},{min:7,bonus:1}]}}
 };
 input.home={name:'SYNTHETIC HOME',roster:homeRoster,lineup:lineup(homeRoster,'4-4-2')};input.away={name:'SYNTHETIC AWAY',roster:awayRoster,lineup:lineup(awayRoster,'4-4-2')};
 const candidates=C.FORMS.flatMap(form=>[0,1].map(k=>lineup(homeRoster,form,k)));
 return {input,candidates};
}
module.exports={example};
