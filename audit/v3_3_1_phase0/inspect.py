#!/usr/bin/env python3
"""Read-only inspection of the reviewed engine; writes only this audit directory."""
import concurrent.futures
import datetime
import hashlib
import json
import os
import platform
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
BASE = 'fa9562decb683a3d64ca248cb66ff20099ddcb54'
REVIEWED = '2122699104f8923eb65d9f4c7491d4bcf48306f2'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def command(cmd):
    start = time.monotonic()
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=60)
    return {'command': cmd, 'exit_code': p.returncode, 'elapsed_seconds': time.monotonic()-start,
            'stdout': p.stdout, 'stderr': p.stderr}

def main():
    ev = OUT/'evidence'
    ev.mkdir(exist_ok=True)
    jobs = {
        'candidate-tests': ['node', '--test', 'experimental/match-win-v3_2/test.js'],
        'legacy-simulator': ['node', 'premium-monte-carlo-v1.test.js'],
        'legacy-scoring': ['node', 'experimental/scoring-gate-v1.test.js'],
        'official-runtime': ['python3', 'tools/validate_official_runtime.py'],
        'official-parity': ['python3', 'tools/validate_13oct_offline.py'],
    }
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(command, cmd): name for name, cmd in jobs.items()}
        for future in concurrent.futures.as_completed(futures):
            name = futures[future]
            result = future.result()
            log = ev/(name+'.log')
            log.write_text(result.pop('stdout')+result.pop('stderr'), encoding='utf8')
            result.update(log=str(log.relative_to(ROOT)), sha256=sha(log.read_bytes()))
            results[name] = result
    protected = ['engine.js','app.js','index.html','sw.js','registry.json','version.json',
                 'premium-monte-carlo-v1.js','experimental/scoring-gate-v1.js','FS_PREMIUM_MATCH_EVIDENCE_V1.json']
    integrity = []
    for p in protected:
        old = subprocess.check_output(['git','show',BASE+':'+p], cwd=ROOT)
        current = (ROOT/p).read_bytes()
        integrity.append({'path':p,'base_sha256':sha(old),'current_sha256':sha(current),'identical':old==current})
    manifests = []
    for name in ['synthetic','real-readiness']:
        folder = ROOT/'experimental/match-win-v3_2/runs'/name
        m = json.loads((folder/'manifest.json').read_text())
        manifests.append({'run':name,'files_ok':all(sha((folder/f).read_bytes())==h for f,h in m['files'].items()),
                          'code_ok':all(sha((folder.parents[1]/f).read_bytes())==h for f,h in m['code_sha256'].items())})
    reg = json.loads((ROOT/'registry.json').read_text())
    ver = json.loads((ROOT/'version.json').read_text())
    result = {
        'schema':'FS_PHASE0_INSPECTION_V1', 'inspected_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'reviewed_remote_commit':REVIEWED, 'production_commit':BASE,
        'local_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'reviewed_tree':'949ca62d8a62fddb2999dd00844d6a6139dbfc34',
        'local_tree':subprocess.check_output(['git','rev-parse','HEAD^{tree}'],cwd=ROOT,text=True).strip(),
        'environment':{'python':platform.python_version(),'node':subprocess.check_output(['node','--version'],text=True).strip(),
                       'system':platform.platform(),'cpu_count':os.cpu_count(),'machine':platform.machine()},
        'runtime':{'version':ver['app'],'registry_count':reg['count'],'engine':ver['engine'],'gold':ver['gold']},
        'checks':results,'production_integrity':integrity,'frozen_run_manifests':manifests,
        'independent_auditor':False,'stat_validated':False,'gold':False,
        'scope':'Existing tests rerun; not certification of V3.3.1 or live forecast accuracy.'
    }
    result['inspection_checks_pass'] = all(r['exit_code']==0 for r in results.values()) and all(r['identical'] for r in integrity) and all(r['files_ok'] and r['code_ok'] for r in manifests) and result['reviewed_tree']==result['local_tree']
    (OUT/'inspection.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print(json.dumps({'inspection_checks_pass':result['inspection_checks_pass'],'test_groups':len(results),'production_unchanged':all(r['identical'] for r in integrity),'gold':False},indent=2))
    if not result['inspection_checks_pass']:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
