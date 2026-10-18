"""FS FantaSegreto V3.3.1 P0 candidate. Shadow-only, NOT TECH PASS."""
from decimal import Decimal, ROUND_FLOOR
import hashlib, json
import numpy as np
import yaml

REQUIRED=('fantasy_goals','defense_modifier','captain_factor','substitution','classic_roles','allowed_formations')

def load_config(path):
    with open(path,encoding='utf8') as f: c=yaml.safe_load(f)
    if c.get('version')!='FS_LEAGUE_CONFIG_V3_3_1_CANDIDATE':
        raise ValueError('Wrong contract')
    for key in REQUIRED:
        if key not in c['rules']: raise ValueError('Missing rule '+key)
    g=c['rules']['fantasy_goals']
    if g['status']!='CERTIFICATA' or Decimal(g['band_width'])<=0:
        raise ValueError('Goal threshold contract invalid')
    return c

def fantagol(score,config):
    if isinstance(score,float):
        raise TypeError('Use decimal numbers, not floats, for threshold comparisons')
    g=config['rules']['fantasy_goals']
    first=Decimal(g['first_goal'])
    step=Decimal(g['band_width'])
    t=Decimal(str(score))
    if t<first: return 0
    return 1+int(((t-first)/step).to_integral_value(rounding=ROUND_FLOOR))

def decision_hash(starters,bench,captain,vice):
    if len(starters)!=11 or len(set(starters))!=11: raise ValueError('Expected 11 unique starters')
    if len(set(bench))!=len(bench) or set(starters)&set(bench):
        raise ValueError('Duplicated player')
    if captain==vice or captain not in starters or vice not in starters:
        raise ValueError('Captain/vice invalid')
    payload={'Titolari':sorted(starters),'Panchina':list(bench),'Capitano':captain,'Vice':vice}
    return hashlib.sha256(json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

def uniform(master_seed,player_id,scenario):
    payload=json.dumps([str(master_seed),str(player_id),int(scenario)],separators=(',',':'),ensure_ascii=False)
    seed=int.from_bytes(hashlib.sha256(payload.encode()).digest()[:16],'big')
    return float(np.random.Generator(np.random.PCG64(seed)).random())

def promotion_state(config):
    missing=[k for k in REQUIRED if config['rules'][k].get('status')!='CERTIFICATA']
    return {'status':'PROVVISORIO' if missing else 'RULES_VERIFIED_ONLY',
            'uncertified':missing,'TECH_PASS':False,'STAT_VALIDATED':False,'GOLD_LOCK':False}
