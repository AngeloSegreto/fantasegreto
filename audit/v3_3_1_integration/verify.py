"""Run bounded regressions; never converts green tests into a GOLD verdict."""
import concurrent.futures
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def main():
    ev = OUT / 'evidence'
    ev.mkdir(exist_ok=True)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    jobs = {
        'node-integration': (['node', '--test', 'experimental/match-win-v3_2/test.js',
            'experimental/match-win-v3_2/league-rules.test.js',
            'experimental/match-win-v3_2/league-integration.test.js'], ROOT),
        'python-baseline': ([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], ROOT / 'experimental/fs_v331_phase1_import/phase1_baseline'),
        'gold-evidence-guard': ([sys.executable, '-m', 'unittest', 'discover', '-s', 'tools', '-p', 'test_match_win_gold_audit.py', '-v'], ROOT),
        'legacy-simulator': (['node', 'premium-monte-carlo-v1.test.js'], ROOT),
        'legacy-scoring': (['node', 'experimental/scoring-gate-v1.test.js'], ROOT),
        'official-runtime': ([sys.executable, 'tools/validate_official_runtime.py'], ROOT),
        'official-parity': ([sys.executable, 'tools/validate_13oct_offline.py'], ROOT),
    }

    def run(item):
        name, (cmd, cwd) = item
        p = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=60)
        path = ev / (name + '.log')
        path.write_text(p.stdout + p.stderr)
        return name, {'command': cmd, 'exit_code': p.returncode,
                      'log': str(path.relative_to(ROOT)),
                      'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        checks = dict(pool.map(run, jobs.items()))
    protected = ['app.js', 'engine.js', 'index.html', 'sw.js', 'registry.json',
                 'version.json', 'premium-monte-carlo-v1.js',
                 'experimental/scoring-gate-v1.js', 'FS_PREMIUM_MATCH_EVIDENCE_V1.json']
    integrity = {}
    for name in protected:
        production = subprocess.check_output(['git', 'show', 'fa9562decb683a3d64ca248cb66ff20099ddcb54:' + name], cwd=ROOT)
        integrity[name] = production == (ROOT / name).read_bytes()
    result = {'schema': 'FS_ACQUIRED_RULES_INTEGRATION_AUDIT_V1',
              'based_on_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'checked_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'checks': checks, 'production_integrity': integrity,
              'all_test_groups_pass': all(c['exit_code'] == 0 for c in checks.values()),
              'tech_pass_v331': False, 'stat_validated': False, 'gold_lock': False}
    (OUT / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'test_groups': len(checks), 'all_pass': result['all_test_groups_pass'],
                      'production_unchanged': all(integrity.values()), 'gold_lock': False}))
    return 0 if result['all_test_groups_pass'] and all(integrity.values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
