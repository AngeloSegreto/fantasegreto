import copy
import hashlib
import tempfile
import unittest
from pathlib import Path
from audit_match_win_gold import evaluate, GATES, SCOPE


class EvidenceGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'proof').write_text('synthetic unit fixture; not real validation')
        self.proof = {'path': 'proof', 'sha256': hashlib.sha256((self.root / 'proof').read_bytes()).hexdigest()}
        self.tree = 'a' * 40
        self.dossier = {'gates': [dict(id=g, status='PASS', scope=SCOPE,
            reviewed_tree=self.tree, reviewer='synthetic-unit-reviewer',
            evidence=[self.proof], preregistered_protocol=self.proof,
            held_out_dataset=self.proof, measured_report=self.proof) for g in GATES]}

    def run_audit(self, dossier=None):
        return evaluate(self.root, dossier or self.dossier, self.tree)

    def test_complete_fixture_only_qualifies_for_review(self):
        result = self.run_audit()
        self.assertTrue(result['eligible_for_release_review'])
        self.assertFalse(result['gold_lock'])
        self.assertFalse(result['automatic_promotion'])

    def test_missing_gate_blocks(self):
        self.dossier['gates'].pop()
        self.assertFalse(self.run_audit()['eligible_for_release_review'])

    def test_pending_blocks(self):
        self.dossier['gates'][9]['status'] = 'PENDING'
        self.assertFalse(self.run_audit()['eligible_for_release_review'])

    def test_other_engine_cannot_close_gate(self):
        self.dossier['gates'][14]['scope'] = 'AUCTION_V4'
        self.assertFalse(self.run_audit()['eligible_for_release_review'])

    def test_other_tree_cannot_close_gate(self):
        self.dossier['gates'][0]['reviewed_tree'] = 'b' * 40
        self.assertFalse(self.run_audit()['eligible_for_release_review'])

    def test_tampering_blocks(self):
        (self.root / 'proof').write_text('changed')
        self.assertFalse(self.run_audit()['eligible_for_release_review'])

    def test_predictive_report_is_required(self):
        self.dossier['gates'][15].pop('measured_report')
        self.assertFalse(self.run_audit()['eligible_for_release_review'])

    def test_duplicate_cannot_hide_failure(self):
        self.dossier['gates'].append(copy.deepcopy(self.dossier['gates'][0]))
        self.assertFalse(self.run_audit()['eligible_for_release_review'])

    def test_path_escape_blocks(self):
        self.dossier['gates'][0]['evidence'] = [{'path': '../outside', 'sha256': '0' * 64}]
        self.assertFalse(self.run_audit()['eligible_for_release_review'])

    def test_no_reviewer_blocks(self):
        self.dossier['gates'][0].pop('reviewer')
        self.assertFalse(self.run_audit()['eligible_for_release_review'])


if __name__ == '__main__':
    unittest.main()
