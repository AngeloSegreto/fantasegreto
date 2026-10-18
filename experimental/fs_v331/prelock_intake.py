"""FS V3.3.1 P0 pre-lock intake. Does NOT predict matches or promote GOLD."""
from __future__ import annotations
import argparse
import json
from datetime import datetime, timezone
from decimal import Decimal
from shadow_evidence import freeze_prelock, verify_archive, parse_time
from p0_core import decision_hash as canonical_decision_hash

LABELS = ('V', 'N', 'S')
ROLES = {'P', 'D', 'C', 'A'}

def _require(cond, message):
    if not cond:
        raise ValueError(message)

def _j(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def verify_fixture_calendar(calendar):
    """Calendar contract check, not proof of source provenance/G01 certification."""
    _require(calendar.get('league') == 'SERIE_A_2026_27', 'wrong competition')
    md = calendar.get('matchday')
    _require(isinstance(md, int) and md > 0, 'matchday missing')
    games = calendar.get('games')
    _require(isinstance(games, list) and len(games) == 10, 'exactly 10 Serie A fixtures expected')
    _require(calendar.get('source_url', '').startswith('https://'), 'source URL missing')
    clubs, kickoff = set(), []
    for g in games:
        for key in ('home', 'away'):
            team = g.get(key)
            _require(isinstance(team, str) and len(team.strip()) > 1, 'invalid team')
            _require(team not in clubs, 'duplicate team across fixtures')
            clubs.add(team)
        kickoff.append(parse_time(g['kickoff']))
    _require(len(clubs) == 20, '20 distinct Serie A teams required')
    return min(kickoff)

def verify_full_roster(input_data):
    roster = input_data.get('roster')
    _require(isinstance(roster, list) and len(roster) == 25, '25 registered players required')
    byid = {}
    for p in roster:
        _require(isinstance(p, dict) and isinstance(p.get('id'), str) and p.get('role') in ROLES,
                 'invalid roster player identity/role')
        _require(p['id'] not in byid, 'duplicate roster identity')
        byid[p['id']] = p['role']
    for role, expected in (('P', 3), ('D', 8), ('C', 8), ('A', 6)):
        _require(sum(1 for r in byid.values() if r == role) == expected,
                 'wrong player count for role ' + role)
    xi = input_data.get('starting_xi')
    bench = input_data.get('bench')
    _require(isinstance(xi, list) and len(xi) == 11, 'exactly 11 starters required')
    _require(isinstance(bench, list) and bench, 'ordered bench required')
    _require(len(set(xi)) == 11 and len(set(bench)) == len(bench) and not set(xi) & set(bench),
             'duplicate starter/reserve')
    _require(set(xi + bench) <= byid.keys(), 'unknown player in lineup')
    _require(sum(byid[p] == 'P' for p in xi) == 1, 'exactly one goalkeeper starter')
    _require(input_data.get('captain') in xi and input_data.get('vice') in xi and
             input_data['captain'] != input_data['vice'], 'captain/vice invalid')
    modules = input_data.get('module')
    count = tuple(sum(byid[p] == x for p in xi) for x in ('D', 'C', 'A'))
    _require(modules == '-'.join(map(str, count)), 'formation violates roles')
    return set(byid)

def validate_probabilities(predictions):
    _require(set(predictions) == {'candidate', 'B0', 'B1'}, 'candidate/B0/B1 required')
    for model, dist in predictions.items():
        _require(isinstance(dist, dict) and set(dist) == set(LABELS), 'invalid outcome keys: ' + model)
        vals = []
        for key in LABELS:
            _require(not isinstance(dist[key], bool), 'invalid bool probability')
            try:
                v = Decimal(str(dist[key]))
            except (ArithmeticError, ValueError, TypeError) as e:
                raise ValueError('invalid probability') from e
            _require(v.is_finite() and Decimal(0) <= v <= Decimal(1), 'out-of-domain probability')
            vals.append(v)
        _require(abs(sum(vals) - Decimal(1)) <= Decimal('0.000000001'), 'probabilities do not sum to 1')

def prepare_intake(*, calendar, inputs, config, decision, sources, now=None):
    earliest = verify_fixture_calendar(calendar)
    _require(inputs.get('matchday') == calendar['matchday'], 'calendar input matchday mismatch')
    _require(config.get('league_id') == 'NATIONAL_LEAGUE_2026_27', 'wrong league config')
    _require(decision.get('prediction_status') == 'SHADOW_PRELOCK', 'missing REAL shadow decision')
    _require(decision.get('engine_version') and decision.get('engine_commit_sha'), 'engine version/commit required')
    _require(decision.get('decision_hash') == canonical_decision_hash(
        inputs['starting_xi'], inputs['bench'], inputs['captain'], inputs['vice']),
        'decision identity hash mismatch')
    _require(decision.get('snapshot_source') == 'REAL_ENGINE_OUTPUT', 'no synthetic/reconstructed forecast')
    verify_full_roster(inputs)
    approved = config.get('rules', {}).get('allowed_formations', {}).get('values', [])
    _require(inputs['module'] in approved, 'module not in configured allowed formations')
    validate_probabilities(decision.get('model_probabilities', {}))
    lock = parse_time(inputs['lock_at'])
    t = now or datetime.now(timezone.utc)
    _require(t.tzinfo is not None and t.utcoffset() is not None, 'clock must be aware')
    _require(t < lock <= earliest, 'not in true pre-lock window')
    _require(parse_time(decision['generated_at']) <= t, 'decision future timestamp')
    _require(parse_time(decision['generated_at']) <= lock, 'decision generated post lock')
    _require(isinstance(sources, list) and len(sources) >= 2, 'at least two observed source snapshots')
    for s in sources:
        _require(s.get('kind') == 'OBSERVED', 'unverified source kind')
        _require(parse_time(s['observed_at']) <= t, 'future source observation')
    return t.isoformat()

def collect(*, calendar, inputs, config, decision, sources, target, engine_files, now=None):
    _require(bool(engine_files), 'engine artifact required for replay')
    real_run = prepare_intake(calendar=calendar, inputs=inputs, config=config,
                              decision=decision, sources=sources, now=now)
    bundle = {**inputs, 'calendar': calendar}
    r = freeze_prelock(target, lock_at=inputs['lock_at'], run_at=real_run, inputs=bundle,
                       config=config, decision=decision, source_snapshots=sources,
                       engine_artifacts=engine_files)
    readback = verify_archive(target)
    if readback['integrity'] != 'PASS':
        raise RuntimeError('archive did not verify, do not publish')
    return {'status': 'SHADOW_CAPTURED', 'gold_lock': False, 'capture': r, 'readback': readback}

def main():
    parser = argparse.ArgumentParser(description='V3.3.1 pre-lock evidence capture, never GOLD')
    for k in ('calendar', 'inputs', 'config', 'decision', 'sources', 'output'):
        parser.add_argument('--' + k, required=True)
    parser.add_argument('--engine-file', action='append', default=[])
    args = parser.parse_args()
    res = collect(calendar=_j(args.calendar), inputs=_j(args.inputs), config=_j(args.config),
                  decision=_j(args.decision), sources=_j(args.sources), target=args.output,
                  engine_files=args.engine_file)
    print(json.dumps(res, ensure_ascii=False, sort_keys=True))

if __name__ == '__main__':
    main()
