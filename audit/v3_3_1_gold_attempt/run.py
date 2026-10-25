"""Reproduce the bounded GOLD readiness check without changing production."""
import concurrent.futures
import csv
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools'))
from audit_match_win_gold import evaluate


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    (OUT / 'evidence').mkdir(exist_ok=True)
    reviewed = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    tree = subprocess.check_output(['git', 'rev-parse', 'HEAD^{tree}'], cwd=ROOT, text=True).strip()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    checks = {
        'release-evidence-guard': ([sys.executable, '-m', 'unittest', 'discover', '-s', 'tools', '-p', 'test_match_win_gold_audit.py', '-v'], ROOT),
        'python-baseline': ([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], ROOT / 'experimental/fs_v331_phase1_import/phase1_baseline'),
        'candidate-v32': (['node', '--test', 'experimental/match-win-v3_2/test.js'], ROOT),
        'legacy-simulator': (['node', 'premium-monte-carlo-v1.test.js'], ROOT),
        'legacy-scoring': (['node', 'experimental/scoring-gate-v1.test.js'], ROOT),
        'official-runtime': ([sys.executable, 'tools/validate_official_runtime.py'], ROOT),
        'official-parity': ([sys.executable, 'tools/validate_13oct_offline.py'], ROOT),
    }

    def run(item):
        name, (cmd, cwd) = item
        result = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=60)
        path = OUT / 'evidence' / (name + '.log')
        path.write_text(result.stdout + result.stderr)
        return name, {'command': cmd, 'cwd': str(cwd.relative_to(ROOT)),
                      'exit_code': result.returncode,
                      'log': str(path.relative_to(ROOT)), 'sha256': digest(path)}

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = dict(pool.map(run, checks.items()))
    protected = ['engine.js', 'app.js', 'index.html', 'sw.js', 'registry.json',
                 'version.json', 'premium-monte-carlo-v1.js',
                 'experimental/scoring-gate-v1.js', 'FS_PREMIUM_MATCH_EVIDENCE_V1.json']
    integrity = []
    for name in protected:
        old = subprocess.check_output(['git', 'show', 'fa9562decb683a3d64ca248cb66ff20099ddcb54:' + name], cwd=ROOT)
        integrity.append({'path': name, 'sha256': digest(ROOT / name),
                          'identical_to_production': old == (ROOT / name).read_bytes()})
    matrix = ROOT / 'audit/v3_3_1_phase0/MATRICE_CONFORMITA_V3_3_1.csv'
    with matrix.open(encoding='utf-8-sig') as handle:
        rows = list(csv.DictReader(handle))
    # The Phase 0 matrix contains local evidence, not full-scope PASS attestations.
    dossier = {'scope': 'FS_MATCH_WIN_V3_3_1', 'gates': [
        {'id': row['ID Requisito'], 'status': 'NOT_ATTESTED',
         'open_work': row['Criterio di Chiusura'], 'matrix_status': row['Stato']}
        for row in rows if row['ID Requisito'].startswith('G') and len(row['ID Requisito']) == 3]}
    (OUT / 'dossier.json').write_text(json.dumps(dossier, indent=2, ensure_ascii=False) + '\n')
    report = evaluate(ROOT, dossier, tree)
    report.update(reviewed_commit=reviewed, evaluated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  tests=results, protected_files=integrity, tech_pass=False, stat_validated=False,
                  all_rerun_test_groups_pass=all(r['exit_code'] == 0 for r in results.values()),
                  production_unchanged=all(r['identical_to_production'] for r in integrity))
    (OUT / 'GOLD_READINESS.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({k: report[k] for k in ['status', 'all_rerun_test_groups_pass', 'production_unchanged', 'tech_pass', 'stat_validated', 'gold_lock']}, indent=2))
    files = sorted([p for p in OUT.rglob('*') if p.is_file() and p.name != 'manifest.json' and '__pycache__' not in p.parts])
    manifest = {str(p.relative_to(ROOT)): digest(p) for p in files}
    manifest.update({name: digest(ROOT / name) for name in ['tools/audit_match_win_gold.py', 'tools/test_match_win_gold_audit.py']})
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return 0 if report['all_rerun_test_groups_pass'] and report['production_unchanged'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
