'use strict';
const VERSION = 'FS_MATCH_WIN_V3.2_RC1';
const FORMS = ['3-5-2','3-4-3','4-3-3','4-4-2','4-5-1','5-3-2','5-4-1'];
const ROLES = ['P','D','C','A'];
const finite = Number.isFinite;
const prob = x => finite(x) && x >= 0 && x <= 1;
const assert = (x,m) => { if (!x) throw Error(m); };
// Deliberately no epsilon: 65.9999999999 must remain zero goals.
function goals(points) { assert(finite(points),'nonfinite points'); return points < 66 ? 0 : 1 + Math.floor((points - 66) / 4); }
function formation(ids,players) {
 const p=ids.map(id=>players[id]);
 if(p.some(x=>!x)||new Set(ids).size!==11||p.filter(x=>x.role==='P').length!==1)return null;
 return ['D','C','A'].map(r=>p.filter(x=>x.role===r).length).join('-');
}
function validateLineup(lineup,roster,players,rules) {
 const errors=[];
 if(!lineup||!Array.isArray(lineup.starters)||!Array.isArray(lineup.bench))return ['missing lineup'];
 const all=[...lineup.starters,...lineup.bench];
 if(new Set(all).size!==all.length||all.some(id=>!roster.includes(id)||!players[id]))errors.push('duplicate/foreign lineup ID');
 if(!rules.formations.includes(formation(lineup.starters,players)))errors.push('illegal formation');
 if(all.length!==roster.length||roster.some(id=>!all.includes(id)))errors.push('every roster player must be starter or bench');
 if(rules.captain?.enabled&&(!lineup.starters.includes(lineup.captain)||!lineup.starters.includes(lineup.vice)||lineup.captain===lineup.vice))errors.push('invalid captain/vice');
 return errors;
}
function validate(input) {
 const errors=[],warnings=[],check=(c,m)=>{if(!c)errors.push(m);};
 if(!input||typeof input!=='object')return {errors:['missing input'],warnings};
 const i=input,r=i.rules||{},players=Object.fromEntries((i.players||[]).map(p=>[p.id,p]));
 const asof=Date.parse(i.as_of),deadline=Date.parse(i.deadline);
 check(['SYNTHETIC','REAL'].includes(i.kind),'kind required');
 if(i.kind==='REAL')check(!!r.league_config,'real match requires acquired league configuration, not synthetic scoring bands');
 check(i.mode==='PRE_MATCH','simulation supports PRE_MATCH only; LIVE event adapter pending');
 check(finite(asof)&&finite(deadline)&&asof<=deadline,'invalid as_of/deadline or future leakage');
 check(Number.isInteger(i.round)&&i.round>0,'round required');
 const sources=new Map((i.sources||[]).map(s=>[s.id,s]));
 check(sources.size===(i.sources||[]).length&&sources.size>0,'unique sources required');
 for(const s of sources.values()) {
  check(typeof s.url==='string'&&/^(https?:\/\/|synthetic:\/\/)/.test(s.url),'source URL required');
  check(finite(Date.parse(s.observed_at))&&Date.parse(s.observed_at)<=asof,'source from future or invalid');
  check(prob(s.reliability)&&finite(s.half_life_hours)&&s.half_life_hours>0,'source confidence metadata required');
  check(Array.isArray(s.conflicts),'source conflict list required');
  if(s.conflicts?.length)warnings.push('SOURCE_CONFLICT:'+s.id);
  if(i.kind==='REAL')check(s.url?.startsWith('https://'),'real input requires HTTPS sources');
 }
 check(r.goal_lock==='NATIONAL_66_4_FIXED_V3_1','goal lock missing');
 check(Array.isArray(r.formations)&&r.formations.length>0&&r.formations.every(f=>FORMS.includes(f))&&new Set(r.formations).size===r.formations.length,'invalid formations');
 check(Number.isInteger(r.substitution_count)&&r.substitution_count>=0&&r.substitution_count<=5,'invalid substitution count');
 check(r.substitution_mode==='SAME_ROLE'&&r.module_change_allowed===false&&r.bench_order==='DISPLAY_ORDER','unsupported substitution rules');
 check(r.keeper_model==='EXCLUSIVE_FULL_MATCH','keeper minutes model must be explicitly acknowledged');
 check(r.verified===true&&sources.has(r.source_id),'scoring rules require explicit source');
 if(r.league_config) {
  const received=Object.values(r.league_config.sources||{});
  check(received.length>0,'acquired rule provenance required');
  for(const s of received)check(finite(Date.parse(s.received_at))&&Date.parse(s.received_at)<=asof,
   'acquired league rules received after as_of or missing timestamp');
 }
 for(const k of ['goal','assist','yellow','red','conceded','save','clean_sheet'])check(finite(r.bonus_malus?.[k]),'missing bonus/malus '+k);
 for(const key of ['defence','captain']) {
  const cfg=r[key];check(cfg&&typeof cfg.enabled==='boolean',key+' rule missing');
  if(cfg?.enabled) {
   check(Array.isArray(cfg.bands)&&cfg.bands.length>0,key+' bands missing');
   (cfg.bands||[]).forEach((b,j)=>check(finite(b.min)&&finite(b.bonus)&&(!j||b.min>cfg.bands[j-1].min),key+' invalid bands'));
  }
 }
 if(r.defence?.enabled)check(r.defence.minimum_rated_defenders===4&&r.defence.top_defenders===3&&r.defence.include_keeper===true,'unsupported defence eligibility');
 if(r.captain?.enabled)check(r.captain.sv_policy==='VICE_THEN_ZERO'&&r.captain.basis==='PURE_VOTE','unsupported captain exceptions');
 const fixtures=new Map((i.fixtures||[]).map(f=>[f.id,f])),teams=new Set();
 check(fixtures.size===(i.fixtures||[]).length&&fixtures.size>0,'duplicate/missing fixtures');
 for(const f of fixtures.values()) {
  check(f.home!==f.away&&!teams.has(f.home)&&!teams.has(f.away),'team appears twice in round');teams.add(f.home);teams.add(f.away);
  check(finite(Date.parse(f.kickoff))&&Date.parse(f.kickoff)>=deadline,'fixture already started at lock');
  check(sources.has(f.source_id),'fixture source missing');
  for(const k of ['home_goal_rate','away_goal_rate'])check(finite(f[k])&&f[k]>=0&&f[k]<=10,'invalid '+k);
  check(prob(f.disruption_probability),'shared disruption probability missing');
 }
 check(Object.keys(players).length===(i.players||[]).length&&Object.keys(players).length>0,'duplicate/missing players');
 check(new Set((i.players||[]).map(p=>String(p.official_id))).size===(i.players||[]).length,'duplicate official IDs');
 for(const p of Object.values(players)) {
  const x=p.projection||{},f=fixtures.get(p.fixture_id);
  check(typeof p.id==='string'&&p.id.length>0&&p.official_id!=null&&String(p.official_id).length>0,'player identity missing');
  check(ROLES.includes(p.role),'invalid role '+p.id);
  check(f&&[f.home,f.away].includes(p.team),'fixture/team mismatch '+p.id);
  check(sources.has(x.source_id)&&finite(Date.parse(x.observed_at))&&Date.parse(x.observed_at)<=asof,'projection source/time '+p.id);
  check(['HEURISTIC','CALIBRATED'].includes(x.kind),'projection kind '+p.id);
  // Calibrated labels need evidence, but are never sufficient for release promotion.
  if(x.kind==='CALIBRATED')check(typeof x.calibration_evidence==='string'&&x.calibration_evidence.length>0,'calibration evidence '+p.id);
  for(const k of ['start','sub','vote_given_start','vote_given_sub','goal_share','assist_share','yellow_probability','red_probability','disruption_sensitivity'])check(prob(x[k]),'probability '+k+' '+p.id);
  check(x.start+x.sub<=1,'start+sub > 1 '+p.id);
  check(finite(x.vote_mean)&&x.vote_mean>=0&&x.vote_mean<=10&&finite(x.vote_sd)&&x.vote_sd>=0&&x.vote_sd<=5,'invalid vote distribution '+p.id);
  check(finite(x.team_vote_loading)&&finite(x.conceded_vote_loading),'role context coefficients '+p.id);
  check(finite(x.save_rate)&&x.save_rate>=0&&x.save_rate<=30,'save rate '+p.id);
  check(typeof p.unavailable==='boolean','availability state missing '+p.id);
  if(p.unavailable)check(x.start===0&&x.sub===0,'unavailable with nonzero chance '+p.id);
  if(p.role==='P')check(x.sub===0&&x.goal_share===0&&x.assist_share===0,'unsupported keeper substitution/scoring '+p.id);
 }
 for(const team of teams) {
  const ps=Object.values(players).filter(p=>p.team===team);
  for(const k of ['goal_share','assist_share'])check(ps.reduce((s,p)=>s+(p.projection?.[k]||0),0)<=1+1e-12,team+' '+k+' sum > 1');
  check(ps.filter(p=>p.role==='P').reduce((s,p)=>s+(p.projection?.start||0),0)<=1+1e-12,team+' keeper start sum > 1');
 }
 const sides=[i.home,i.away];
 for(let j=0;j<2;j++) {
  const s=sides[j];check(s&&Array.isArray(s.roster)&&s.roster.length>=11,'missing roster '+j);
  if(!s?.roster)continue;
  check(new Set(s.roster).size===s.roster.length&&s.roster.every(id=>players[id]),'roster identity '+j);
  errors.push(...validateLineup(s.lineup,s.roster,players,{...r,formations:r.formations||[]}).map(e=>j+': '+e));
 }
 if(i.home?.roster&&i.away?.roster)check(!i.home.roster.some(id=>i.away.roster.includes(id)),'same player owned by both fantasy sides');
 return {errors:[...new Set(errors)],warnings:[...new Set(warnings)]};
}
function availability(x) {
 const vote=x.start*x.vote_given_start+x.sub*x.vote_given_sub;
 return {start:x.start,sub:x.sub,vote,sv:1-vote,kind:x.kind};
}
function freshness(source,asof) {
 const age=Math.max(0,(Date.parse(asof)-Date.parse(source.observed_at))/3600000);
 return {age_hours:age,confidence:source.reliability*2**(-age/source.half_life_hours),needs_refresh:age>source.half_life_hours};
}
function band(value,bands) { let bonus=0; for(const b of bands)if(value>=b.min)bonus=b.bonus;return bonus; }
function score(lineup,scenario,players,rules) {
 const xi=lineup.starters.map(id=>({id,...scenario[id]})),used=new Set();let changes=0,recovered=0;
 for(const id of lineup.bench) {
  if(!scenario[id].voted||changes>=rules.substitution_count)continue;
  const j=xi.findIndex(p=>!p.voted&&players[p.id].role===players[id].role);
  if(j>=0){used.add(id);recovered+=Number(scenario[id].fp);xi[j]={id,...scenario[id]};changes++;}
 }
 if(rules.league_config) {
  const result=require('./league-rules').scoreResolved(lineup,xi,used,scenario,players,rules);
  return {...result,missing:11-xi.filter(p=>p.voted).length,changes,xi:xi.map(p=>p.id)};
 }
 const valid=xi.filter(p=>p.voted),def=valid.filter(p=>players[p.id].role==='D'),keeper=valid.find(p=>players[p.id].role==='P');
 let modifier=0,captain=0;
 if(rules.defence.enabled&&def.length>=rules.defence.minimum_rated_defenders&&keeper) {
  const avg=(keeper.pure+def.map(p=>p.pure).sort((a,b)=>b-a).slice(0,3).reduce((a,b)=>a+b,0))/4;
  modifier=band(avg,rules.defence.bands);
 }
 if(rules.captain.enabled) {
  // A replacement does not inherit a captain marker.
  const p=valid.find(p=>p.id===lineup.captain)||valid.find(p=>p.id===lineup.vice);
  if(p)captain=band(p.pure,rules.captain.bands);
 }
 const base=valid.reduce((s,p)=>s+p.fp,0),total=base+modifier+captain;
 return {total,goals:goals(total),base,modifier,captain,missing:11-valid.length,changes,recovered,
  bench_unused_points:lineup.bench.filter(id=>!used.has(id)&&scenario[id].voted).reduce((s,id)=>s+scenario[id].fp,0),
  unused_bonus:lineup.bench.filter(id=>!used.has(id)&&scenario[id].voted).reduce((s,id)=>s+Math.max(0,scenario[id].fp-scenario[id].pure),0),xi:xi.map(p=>p.id)};
}
module.exports={VERSION,FORMS,ROLES,finite,prob,assert,goals,formation,validateLineup,validate,availability,freshness,score};
