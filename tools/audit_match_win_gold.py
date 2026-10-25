"""Fail-closed evidence audit. It never merges, deploys, or certifies a model."""
import argparse
import hashlib
import json
from pathlib import Path

SCOPE = 'FS_MATCH_WIN_V3_3_1'
GATES = tuple(f'G{i:02}' for i in range(23))
PREDICTIVE = {'G14', 'G15'}


def evidence_ok(root, item):
    if not isinstance(item, dict):
        return False
    path = item.get('path')
    digest = item.get('sha256')
    if not isinstance(path, str) or not isinstance(digest, str):
        return False
    target = (root / path).resolve()
    if not target.is_relative_to(root.resolve()) or not target.is_file():
        return False
    return hashlib.sha256(target.read_bytes()).hexdigest() == digest


def evaluate(root, dossier, reviewed_tree):
    """Check admissibility of reviewed evidence, not statistical truth itself.

    PASS attestations require an identified reviewer and exact tree/scope binding.
    Predictive gates additionally require protocol, held-out data and report.
    A complete dossier is eligible for a release review, never an auto-promotion.
    """
    root = Path(root)
    entries = dossier.get('gates', [])
    ids = [r.get('id') for r in entries if isinstance(r, dict)]
    duplicates = {g for g in ids if ids.count(g) > 1}
    records = {r['id']: r for r in entries if isinstance(r, dict) and 'id' in r}
    checks = []
    for gate in GATES:
        record = records.get(gate, {})
        reasons = []
        if gate in duplicates:
            reasons.append('DUPLICATE_GATE')
        if record.get('status') != 'PASS':
            reasons.append('REVIEWED_PASS_MISSING')
        if record.get('scope') != SCOPE:
            reasons.append('WRONG_OR_MISSING_ENGINE_SCOPE')
        if record.get('reviewed_tree') != reviewed_tree:
            reasons.append('WRONG_OR_MISSING_REVIEWED_TREE')
        if not record.get('reviewer'):
            reasons.append('REVIEWER_MISSING')
        evidence = record.get('evidence', [])
        if not evidence or not all(evidence_ok(root, item) for item in evidence):
            reasons.append('EVIDENCE_MISSING_OR_HASH_MISMATCH')
        if gate in PREDICTIVE:
            for name in ('preregistered_protocol', 'held_out_dataset', 'measured_report'):
                if not evidence_ok(root, record.get(name)):
                    reasons.append(name.upper() + '_MISSING_OR_HASH_MISMATCH')
        checks.append({'id': gate, 'admissible': not reasons,
                       'reasons': reasons, 'open_work': record.get('open_work')})
    eligible = all(c['admissible'] for c in checks)
    return {'schema': 'FS_MATCH_WIN_GOLD_EVIDENCE_AUDIT_V1',
            'scope': SCOPE, 'reviewed_tree': reviewed_tree,
            'status': 'ELIGIBLE_FOR_RELEASE_REVIEW' if eligible else 'GOLD_LOCK_BLOCKED',
            'eligible_for_release_review': eligible,
            'gold_lock': False, 'automatic_promotion': False,
            'note': 'Evidence admissibility audit; not a statistical certification or promotion.',
            'gates': checks}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--dossier', type=Path, required=True)
    parser.add_argument('--reviewed-tree', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    dossier = json.loads(args.dossier.read_text())
    result = evaluate(args.root, dossier, args.reviewed_tree)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(result['status'])
    return 0 if result['eligible_for_release_review'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
