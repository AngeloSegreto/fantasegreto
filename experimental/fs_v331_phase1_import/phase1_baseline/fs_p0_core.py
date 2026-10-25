"""FS V3.3.1 Fase1 P0: precise goal rule & canonical identity; SHADOW only."""
from decimal import Decimal, ROUND_FLOOR
import hashlib, json
from pathlib import Path
import yaml
from jsonschema import validate as schema_validate
import numpy as np

MANDATORY_RULES = ('fantasy_goals', 'defense_modifier', 'captain_factor', 'substitution', 'classic_roles', 'allowed_formations')

def load_config(config_path: str, schema_path: str):
    p=Path(config_path)
    conf=yaml.safe_load(p.read_text(encoding='utf-8'))
    schema=json.loads(Path(schema_path).read_text(encoding='utf-8'))
    schema_validate(conf, schema)
    rules=conf['rules']
    for key in MANDATORY_RULES:
        if key not in rules:
            raise ValueError('missing rule: '+key)
    g=rules['fantasy_goals']
    if Decimal(g['band_width']) <= 0:
        raise ValueError('nonpositive goal band')
    if Decimal(g['first_goal']) < 0:
        raise ValueError('negative first goal')
    return conf

def verify_goal_evidence(conf, evidence_dir):
    g=conf['rules']['fantasy_goals']
    evidence=Path(evidence_dir)/Path(g['source_path']).name
    return evidence.is_file() and hashlib.sha256(evidence.read_bytes()).hexdigest()==g['source_sha256']

def fantasy_goals(score, conf):
    """Use *configuration* and base-10 exact Decimal, no float rounding/truncation."""
    if isinstance(score,float):
        raise TypeError('Binary floats prohibited for boundary comparison')
    score=Decimal(str(score))
    g=conf['rules']['fantasy_goals']
    first=Decimal(g['first_goal'])
    band=Decimal(g['band_width'])
    if score<first:
        return 0
    return 1+int(((score-first)/band).to_integral_value(rounding=ROUND_FLOOR))

def canonical_identity(starters, bench, captain_id, vice_id):
    """Starters unordered; bench exact. IDs must be unique in the entire decision."""
    if len(starters)!=11 or len(set(starters))!=11:
        raise ValueError('11 unique starters required')
    if len(set(bench))!=len(bench) or set(starters)&set(bench):
        raise ValueError('duplicate player across lineup/bench')
    if captain_id not in starters or vice_id not in starters or captain_id==vice_id:
        raise ValueError('captain & vice must be different starters')
    canon=lambda ids:json.dumps(list(ids),ensure_ascii=False,separators=(',',':'))
    encoded=('Titolari:'+canon(sorted(starters))+'|Panchina:'+canon(bench)+'|Capitano:'+str(captain_id)+'|Vice:'+str(vice_id)).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()

def pcg64_seed(master_seed,player_id,scenario_number):
    """Independent per-player per-scenario deterministic seed, avoids enumeration dependency."""
    value=json.dumps([str(master_seed),str(player_id),int(scenario_number)],separators=(',',':'),ensure_ascii=False).encode()
    return int.from_bytes(hashlib.sha256(value).digest()[:16],'big')

def sampled_uniform(master_seed,player_id,scenario_number):
    return float(np.random.Generator(np.random.PCG64(pcg64_seed(master_seed,player_id,scenario_number))).random())

def promotion_state(conf):
    """Fail closed; rule certification and prediction validation are separate."""
    uncertified=[k for k in MANDATORY_RULES if conf['rules'][k].get('status')!='CERTIFICATA']
    if conf['strategic_profile'].get('status')!='CERTIFICATA':
        uncertified.append('strategic_profile')
    if conf['standings_points'].get('status')!='CERTIFICATA':
        uncertified.append('standings_points')
    return {'status':'PROVVISORIO' if uncertified else 'RULES_VERIFIED_ONLY', 'not_certified':uncertified,'tech_pass':False,'stat_validated':False,'gold_lock':False}
