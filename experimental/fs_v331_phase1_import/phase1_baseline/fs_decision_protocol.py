"""FS V3.3.1 P0: confronto appaiato e log pre-lock. Shadow-only, non predittivo."""
from __future__ import annotations
import hashlib
import json
import math
import os
from datetime import datetime
from pathlib import Path
from statistics import NormalDist, mean, stdev

OUTCOMES = {'V', 'N', 'S'}
PROFILES = ('PUNTI_ATTESI', 'MAX_VITTORIA')


def _value(outcome: str, profile: str) -> float:
    if profile not in PROFILES or outcome not in OUTCOMES:
        raise ValueError('invalid profile/outcome')
    return (3.0 if outcome == 'V' else 1.0 if outcome == 'N' else 0.0) if profile == 'PUNTI_ATTESI' else (1.0 if outcome == 'V' else 0.0)


def _stats(outcomes):
    n = len(outcomes)
    return {'P(V)': outcomes.count('V') / n, 'P(N)': outcomes.count('N') / n,
            'P(S)': outcomes.count('S') / n, 'PUNTI_ATTESI': (3 * outcomes.count('V') + outcomes.count('N')) / n,
            'MAX_VITTORIA': outcomes.count('V') / n}


def compare_paired(outcomes_a, outcomes_b, profile: str, delta: float, alpha: float = 0.05,
                   identity_a: str = '', identity_b: str = '', previous: str | None = None,
                   previous_revalidated: bool = False):
    """Same scenarios paired; confidence interval only reflects Monte Carlo noise."""
    if profile not in PROFILES or not (0 < alpha < 1) or not (0 <= delta < math.inf):
        raise ValueError('invalid registered comparison parameters')
    if len(outcomes_a) != len(outcomes_b) or len(outcomes_a) < 2:
        raise ValueError('paired equal scenarios n>=2 required')
    if not set(outcomes_a).issubset(OUTCOMES) or not set(outcomes_b).issubset(OUTCOMES):
        raise ValueError('invalid scenario outcome')
    if not identity_a or not identity_b or identity_a == identity_b:
        raise ValueError('distinct complete decision hashes required')
    diff = [_value(a, profile) - _value(b, profile) for a, b in zip(outcomes_a, outcomes_b)]
    center = mean(diff)
    half = NormalDist().inv_cdf(1 - alpha / 2) * stdev(diff) / math.sqrt(len(diff))
    low, high = center - half, center + half
    sa, sb = _stats(outcomes_a), _stats(outcomes_b)
    if low > delta:
        verdict, winner = 'A SUPERIORE', 'A'
    elif high < -delta:
        verdict, winner = 'B SUPERIORE', 'B'
    elif low >= -delta and high <= delta:
        verdict = 'EQUIVALENTI ENTRO δ'
        secondary = 'MAX_VITTORIA' if profile == 'PUNTI_ATTESI' else 'PUNTI_ATTESI'
        if sa[secondary] != sb[secondary]:
            winner = 'A' if sa[secondary] > sb[secondary] else 'B'
        elif sa['P(S)'] != sb['P(S)']:
            winner = 'A' if sa['P(S)'] < sb['P(S)'] else 'B'
        elif previous_revalidated and previous in (identity_a, identity_b):
            winner = 'A' if previous == identity_a else 'B'
        else:
            winner = 'A' if identity_a < identity_b else 'B'
    else:
        verdict = 'INCONCLUDENTE'
        if sa[profile] == sb[profile]:
            winner = 'A' if identity_a < identity_b else 'B'
        else:
            winner = 'A' if sa[profile] > sb[profile] else 'B'
    return {'verdetto':verdict, 'decisione_operativa':winner,'n_scenari':len(diff),
            'intervallo_confidenza_95' if alpha == .05 else 'intervallo_confidenza': [low, high],
            'differenza_appaiata':center, 'delta_pre_registrato':delta,
            'profilo':profile,'A':sa,'B':sb,'stat_validated':False,'gold_lock':False}


def _ts(dt: str):
    value = datetime.fromisoformat(dt)
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError('timezone required')
    return value


def _canonical(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def verify_decision_ledger(path: str | Path):
    prev = '0' * 64
    count = 0
    file = Path(path)
    if not file.exists():
        return {'valid': True, 'count': 0, 'head': prev}
    for line in file.read_text(encoding='utf-8').splitlines():
        try:
            item=json.loads(line)
            head=item.pop('record_sha256')
            if item.get('previous_sha256') != prev or hashlib.sha256(_canonical(item)).hexdigest() != head:
                return {'valid':False,'count':count,'reason':'hash_chain_mismatch'}
            prev=head; count+=1
        except (json.JSONDecodeError, ValueError, KeyError):
            return {'valid':False,'count':count,'reason':'malformed_record'}
    return {'valid':True,'count':count,'head':prev}


def append_decision_record(path: str | Path, *, kind: str, observed_at: str, lock_at: str,
                           decision_sha256: str, input_sha256: str, config_sha256: str,
                           actual_decision_sha256: str | None = None):
    """Append-only proof record; a new version must never rewrite prior lines."""
    if kind not in ('RECOMMENDATION','OVERRIDE'):
        raise ValueError('invalid event kind')
    if not all(len(h)==64 and all(c in '0123456789abcdef' for c in h) for h in [decision_sha256,input_sha256,config_sha256]):
        raise ValueError('invalid hashes')
    if _ts(observed_at) > _ts(lock_at):
        raise ValueError('post-lock record rejected')
    if kind == 'OVERRIDE' and (actual_decision_sha256 is None or len(actual_decision_sha256)!=64):
        raise ValueError('override actual decision required')
    p = Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    prior = verify_decision_ledger(p)
    if not prior['valid']:
        raise ValueError('ledger corrupted')
    record={'kind':kind,'observed_at':observed_at,'lock_at':lock_at,
            'recommended_decision_sha256':decision_sha256,'actual_decision_sha256':actual_decision_sha256,
            'input_sha256':input_sha256,'config_sha256':config_sha256,'previous_sha256':prior['head']}
    record['record_sha256']=hashlib.sha256(_canonical(record)).hexdigest()
    # Only create/append; no truncation. Single process writer for MVP; concurrency lock remains G22 open.
    with os.fdopen(os.open(p,os.O_WRONLY|os.O_CREAT|os.O_APPEND,0o600),'a',encoding='utf-8') as f:
        f.write(_canonical(record).decode('utf-8')+'\n');f.flush();os.fsync(f.fileno())
    return record['record_sha256']
