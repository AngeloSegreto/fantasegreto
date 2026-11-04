"""FantaSegreto native event-consistent joint matchday scenario generator.

SHADOW ONLY. All scoring coefficients are explicit league-contract inputs.
No external calls, no invented injury news or source authentication.
The output is compatible with V3.3.1's prelock_scenario_compare.py schema.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from decimal import Decimal

VERSION = 'FS_NATIVE_JOINT_GENERATOR_V1_0_SHADOW'
VALID_AVAILABILITY = {'AVAILABLE', 'DOUBTFUL', 'OUT', 'UNKNOWN'}


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


def check(cond, reason):
    if not cond:
        raise ValueError(reason)


def dt(value):
    try:
        x = datetime.fromisoformat(value)
    except (ValueError, TypeError) as exc:
        raise ValueError('timestamp must be ISO8601: ' + str(value)) from exc
    check(x.tzinfo is not None and x.utcoffset() is not None, 'timestamp requires timezone')
    return x


def bounded(v, key, lo=0., hi=1.):
    check(isinstance(v, (float, int)) and not isinstance(v, bool)
          and math.isfinite(v) and lo <= v <= hi, f'invalid numeric {key}')
    return float(v)


def poisson(rng, lam):
    """Exact Knuth sampler; xG bounded so this remains cheap and transparent."""
    check(0 <= lam <= 500 and math.isfinite(lam), 'nonfinite or excessive intensity')
    if lam == 0:
        return 0
    p, count, threshold = 1.0, 0, math.exp(-lam)
    while p > threshold:
        p *= rng.random()
        count += 1
    return count - 1


def weighted(rng, pairs):
    """Return an ID or None. The untracked OTHER bucket is explicit."""
    total = sum(w for _, w in pairs)
    check(total > 0, 'non-positive all event weights')
    u = rng.random() * total
    for person, weight in pairs:
        u -= weight
        if u < 0:
            return person
    return pairs[-1][0]


def _rounded_vote(value):
    return max(3.0, min(9.0, math.floor(value * 2 + 0.5) / 2))


def _sample_player(rng, p, par):
    av = par['availability']
    active = av != 'OUT' and rng.random() < par['vote_probability']
    return {
        'status': 'VOTED' if active else ('DID_NOT_PLAY' if av == 'OUT' else 'SV'),
        'pure_vote': None, 'fantavote': None,
        'yellow': bool(active and rng.random() < par['yellow_probability']),
        'red': bool(active and rng.random() < par['red_probability']),
        'goals': 0, 'assists': 0,
        'team': p['team'], 'role': p['role'],
    }


def validate_inputs(roster, opponent, calendar, priors, n, seed, cutoff, generated, lock):
    check(isinstance(n, int) and not isinstance(n, bool) and 1 <= n <= 1000000,
          'scenario count must be integer 1..1e6')
    check(isinstance(seed, int) and not isinstance(seed, bool) and seed >= 0,
          'nonnegative integer seed required')
    check(isinstance(calendar.get('matchday'), int), 'matchday required')
    games = calendar.get('games')
    check(isinstance(games, list) and len(games) == 10, 'ten fixtures required')
    check(dt(cutoff) <= dt(generated) <= dt(lock), 'source_cutoff <= generated <= lock')
    check(dt(lock) <= min(dt(g['kickoff']) for g in games), 'lock after earliest kickoff')
    clubs = []
    keys = []
    for g in games:
        check(all(isinstance(g.get(k), str) and g[k] for k in ('home','away','kickoff')), 'invalid fixture')
        clubs.extend([g['home'],g['away']]); keys.append('|'.join([g['home'],g['away'],g['kickoff']]))
    check(len(clubs) == len(set(clubs)) == 20 and len(keys) == len(set(keys)), 'fixtures must cover twenty distinct teams')
    check(priors.get('schema') == 'FS_NATIVE_JOINT_PRIORS_V1', 'wrong prior schema')
    check(priors.get('evidence_kind') == 'SYNTHETIC_UNIT_TEST',
          'real-mode calibration/provenance not verified: fail closed')
    check(isinstance(priors.get('players'), dict) and isinstance(priors.get('fixtures'), dict), 'priors missing')
    check(set(priors['fixtures']) == set(keys), 'fixture prior coverage mismatch')
    players = [*roster.get('roster',[]), *opponent.get('roster',[])]
    check(len(players) > 20, 'both fantasy rosters required')
    check(len({p['id'] for p in players}) == len(players), 'duplicate official IDs')
    check(all(p['team'] in clubs and p['role'] in ('P','D','C','A') for p in players),
          'unmapped player or illegal role')
    check(set(priors['players']) == {p['id'] for p in players}, 'priors must cover exactly all roster players')
    valid = {}
    for p in players:
        k = p['id']; x = priors['players'][k]
        check(isinstance(x, dict), 'player prior must be object')
        av = x.get('availability', 'UNKNOWN')
        check(av in VALID_AVAILABILITY, 'invalid availability status: '+k)
        pr = {
            'availability':av,
            'vote_probability':bounded(x.get('vote_probability'), k+'.vote_probability'),
            'pure_vote_mean':bounded(x.get('pure_vote_mean'),k+'.pure_vote_mean',3,9),
            'pure_vote_sd':bounded(x.get('pure_vote_sd'),k+'.pure_vote_sd',0,3),
            'goal_weight':bounded(x.get('goal_weight'),k+'.goal_weight',0,25),
            'assist_weight':bounded(x.get('assist_weight'),k+'.assist_weight',0,25),
            'yellow_probability':bounded(x.get('yellow_probability'),k+'.yellow_probability'),
            'red_probability':bounded(x.get('red_probability'),k+'.red_probability'),
        }
        if av == 'OUT': check(pr['vote_probability'] == 0., 'OUT player must have zero chance of vote '+k)
        valid[k] = pr
    vf = {}
    for key, x in priors['fixtures'].items():
        check(isinstance(x, dict), 'fixture prior must be object')
        vf[key] = {
            'home_xg':bounded(x.get('home_xg'),key+'.home_xg',0,8),
            'away_xg':bounded(x.get('away_xg'),key+'.away_xg',0,8),
            'shared_tempo_sd':bounded(x.get('shared_tempo_sd'),key+'.tempo',0,.7),
            'tracked_goal_residual_weight':bounded(x.get('other_goal_weight'),key+'.other_goal_weight',.01,30),
            'tracked_assist_residual_weight':bounded(x.get('other_assist_weight'),key+'.other_assist_weight',.01,30),
            'assist_chance':bounded(x.get('assist_chance'),key+'.assist_chance'),
        }
    return sorted(players, key=lambda p:p['id']),valid,vf,sorted(games, key=lambda g:g['kickoff'])


def generate(roster,opponent,calendar,priors,*,n,seed,source_cutoff_at,generated_at,lock_at):
    """Build identical shared scenarios for any number of candidate formations."""
    players, pars, fixtures, games = validate_inputs(roster,opponent,calendar,priors,n,seed,
                                                    source_cutoff_at,generated_at,lock_at)
    rng = random.Random(seed)
    by_club = defaultdict(list)
    by_id = {p['id']:p for p in players}
    for p in players: by_club[p['team']].append(p['id'])
    all_scenarios=[]
    goal_censors=0
    for scenario_id in range(n):
        states={}; outcomes={}
        for p in players:
            outcomes[p['id']] = _sample_player(rng, p, pars[p['id']])
        for g in games:
            key='|'.join([g['home'],g['away'],g['kickoff']]); fx=fixtures[key]
            sd=fx['shared_tempo_sd']
            tempo=math.exp(rng.gauss(-.5*sd*sd,sd))
            # A common tempo makes the two teams' goals correlated, not independent.
            goal_home=poisson(rng, fx['home_xg']*tempo)
            goal_away=poisson(rng, fx['away_xg']*tempo)
            if goal_home>15 or goal_away>15:
                goal_censors += 1
            goal_home=min(15,goal_home);goal_away=min(15,goal_away)
            events=[]
            for club,num in ((g['home'],goal_home),(g['away'],goal_away)):
                eligible=[pid for pid in by_club[club] if outcomes[pid]['status']=='VOTED'
                          and by_id[pid]['role']!='P']
                for _ in range(num):
                    scorer=weighted(rng,[(pid,pars[pid]['goal_weight']) for pid in eligible
                                          if pars[pid]['goal_weight']>0]+
                                    [(None,fx['tracked_goal_residual_weight'])])
                    assister=None
                    if rng.random()<fx['assist_chance']:
                        assister=weighted(rng,[(pid,pars[pid]['assist_weight']) for pid in eligible
                                                if pid!=scorer and pars[pid]['assist_weight']>0]+
                                          [(None,fx['tracked_assist_residual_weight'])])
                    if scorer is not None:outcomes[scorer]['goals']+=1
                    if assister is not None:outcomes[assister]['assists']+=1
                    events.append({'team':club,'scorer_id':scorer,'assist_id':assister})
            states[key]={'home_goals':goal_home,'away_goals':goal_away,
                         'goal_events':events,'shared_tempo':round(tempo,8)}
            for club,against in ((g['home'],goal_away),(g['away'],goal_home)):
                for pid in by_club[club]:
                    if outcomes[pid]['status']!='VOTED':continue
                    par=pars[pid];p=by_id[pid]; obs=outcomes[pid]
                    # Votes are common random outcomes, with a modest event-level uplift.
                    uplift=.25*obs['goals']+.12*obs['assists']+(.2 if p['role']=='P' and against==0 else 0.)
                    base=_rounded_vote(rng.gauss(par['pure_vote_mean']+uplift,par['pure_vote_sd']))
                    ff=base+3*obs['goals']+obs['assists']-.5*int(obs['yellow'])-int(obs['red'])
                    if p['role']=='P':ff=ff-against+(1 if against==0 else 0)
                    obs['pure_vote']=f'{base:.1f}'.rstrip('0').rstrip('.')
                    obs['fantavote']=f'{ff:.1f}'.rstrip('0').rstrip('.')
                    obs['conceded']=against if p['role']=='P' else 0
        player_outcomes={}
        for pid in sorted(outcomes):
            p=by_id[pid]; g=next(g for g in games if p['team'] in (g['home'],g['away']))
            key='|'.join([g['home'],g['away'],g['kickoff']]); obs=outcomes[pid]
            # Third-party comparator requires that SV records omit rating keys.
            row={'status':obs['status'],'fixture_ref':key}
            if obs['status']=='VOTED':
                row.update({'pure_vote':obs['pure_vote'],'fantavote':obs['fantavote'],
                            'components':{'goals':obs['goals'],'assists':obs['assists'],
                                'yellow':int(obs['yellow']),'red':int(obs['red']),
                                'conceded':obs['conceded'],
                                'clean_sheet':int(p['role']=='P' and obs['conceded']==0)}})
            player_outcomes[pid]=row
        all_scenarios.append({'scenario_id':scenario_id,'player_outcomes':player_outcomes,
                              'fixture_states':states})
    return {'schema':'FS_NATIVE_JOINT_MATCHDAY_BUNDLE_V1','engine':VERSION,
            'matchday':calendar['matchday'],'sampling_design':'IID_JOINT_MATCHDAY_SCENARIOS',
            'evidence_kind':'SYNTHETIC_UNIT_TEST','GOLD_LOCK':False,'TECH_PASS':False,
            'STAT_VALIDATED':False,'G14_G15_eligible':False,
            'generated_at':generated_at,'source_cutoff_at':source_cutoff_at,
            'lock_at':lock_at,'n_scenarios':n,'seed':seed,
            'input_sha256':digest({'roster':roster,'opponent':opponent,'calendar':calendar,'priors':priors}),
            'projection_sha256':digest(priors),
            'output_limitations':['illustrative priors, not calibrated; no verified historical holdout',
                                  'tracked scorer/assister residual OTHER includes unowned players',
                                  'no penalty, own-goal, card-second-yellow or injury-event process',
                                  'no actual pre-lock source attestation or official adversary XI'],
            'joint_fixture_groups':calendar['games'],
            'goal_count_censored_scenarios':goal_censors,
            'scenarios':all_scenarios}


def audit(bundle,roster,opponent,calendar):
    """Independently verify event coherence and scoring decompositions."""
    players=roster['roster']+opponent['roster']
    by_id={p['id']:p for p in players}
    check(len(by_id)==len(players),'duplicate IDs audit')
    expected={'|'.join((g['home'],g['away'],g['kickoff'])):g for g in calendar['games']}
    check(len(bundle['scenarios'])==bundle['n_scenarios'],'scenario count mismatch')
    for row in bundle['scenarios']:
        check(set(row['fixture_states'])==set(expected),'missing fixture in scenario')
        check(set(row['player_outcomes'])==set(by_id),'missing fantasy player in scenario')
        scores=Counter(); assists=Counter()
        for key,state in row['fixture_states'].items():
            fx=expected[key];evs=state['goal_events']
            check(len(evs)==state['home_goals']+state['away_goals'],'goal event count mismatch')
            ct=Counter(e['team'] for e in evs)
            check(ct[fx['home']]==state['home_goals'] and ct[fx['away']]==state['away_goals'],
                  'fixture score/event mismatch')
            for e in evs:
                for tag,count in [('scorer_id',scores),('assist_id',assists)]:
                    pid=e[tag]
                    if pid is not None:
                        check(pid in by_id and by_id[pid]['team']==e['team'], 'cross-team or phantom goal event')
                        check(by_id[pid]['role']!='P','unsupported keeper goal process')
                        check(row['player_outcomes'][pid]['status']=='VOTED','non-voter scored goal')
                        count[pid]+=1
                check(e['scorer_id'] is None or e['scorer_id']!=e['assist_id'], 'self-assist forbidden')
        for pid,obs in row['player_outcomes'].items():
            p=by_id[pid]
            check(obs['fixture_ref'] in expected and p['team'] in
                  (expected[obs['fixture_ref']]['home'],expected[obs['fixture_ref']]['away']),
                  'wrong fixture referee')
            if obs['status']!='VOTED':
                check('pure_vote' not in obs and 'fantavote' not in obs,'SV with vote')
            else:
                check(0<=float(obs['pure_vote'])<=10,'pure vote out of range')
                check(float(obs['pure_vote'])*2==int(float(obs['pure_vote'])*2), 'pure vote tick mismatch')
                comp=obs.get('components',{})
                check(comp.get('goals')==scores[pid] and comp.get('assists')==assists[pid],
                      'fantavote goal/assist components inconsistent with shared event log')
                fixture=expected[obs['fixture_ref']]
                state=row['fixture_states'][obs['fixture_ref']]
                actual_conceded=(state['away_goals'] if fixture['home']==p['team'] else state['home_goals'])
                expected_conceded=actual_conceded if p['role']=='P' else 0
                check(comp.get('conceded')==expected_conceded,'keeper goals-conceded not tied to fixture score')
                check(comp.get('clean_sheet')==int(p['role']=='P' and actual_conceded==0),
                      'keeper clean-sheet bonus not tied to fixture score')
                check(comp.get('yellow') in (0,1) and comp.get('red') in (0,1), 'invalid card event component')
                estimated=(Decimal(obs['pure_vote'])+3*comp['goals']+comp['assists']
                           -Decimal('0.5')*comp['yellow']-comp['red']
                           -comp['conceded']+comp['clean_sheet'])
                check(estimated==Decimal(obs['fantavote']), 'fantavote arithmetic mismatch')
    return {'audit':'PASS','scenario_count':bundle['n_scenarios'],
            'event_to_fixture_coherence':True,'same_fixture_shared_across_fantasy_teams':True,
            'no_cross_club_goals_or_assists':True,'only_voted_players_can_receive_events':True,
            'prediction_calibration_validated':False,'GOLD_LOCK':False}


def main():
    ap=argparse.ArgumentParser(description=VERSION+'; SHADOW ONLY')
    for arg in ('roster','opponent','calendar','priors','output'):
        ap.add_argument('--'+arg,required=True)
    for arg in ('source-cutoff-at','generated-at','lock-at'):
        ap.add_argument('--'+arg,required=True)
    ap.add_argument('--n',type=int,default=1000)
    ap.add_argument('--seed',type=int,default=3301)
    args=ap.parse_args()
    get=lambda name:json.loads(Path(getattr(args,name)).read_text(encoding='utf-8'))
    r,o,c,p=map(get,('roster','opponent','calendar','priors'))
    res=generate(r,o,c,p,n=args.n,seed=args.seed,
                 source_cutoff_at=args.source_cutoff_at,generated_at=args.generated_at,
                 lock_at=args.lock_at)
    result=audit(res,r,o,c)
    target=Path(args.output);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(res,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':'SHADOW_GENERATED_NOT_CALIBRATED',
                      'output':str(target),'bytes':target.stat().st_size,
                      'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),**result},indent=2))

if __name__=='__main__':main()
