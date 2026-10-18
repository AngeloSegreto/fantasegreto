"""P0 shadow custody tests. Synthetic fixtures validate software, not model accuracy."""
import tempfile
import unittest
from pathlib import Path
from shadow_evidence import freeze_prelock, verify_archive, promotion_gate, GATES, REQUIRED_RULES

BEFORE = "2026-10-23T20:40:00+02:00"
LOCK = "2026-10-23T20:45:00+02:00"

class CustodyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.file = self.root / "source.txt"
        self.file.write_text("SYNTHETIC SOURCE FOR TESTS", encoding="utf-8")
        self.sources = [{"id": "a", "uri": "https://example.org/source", "observed_at": BEFORE,
                         "path": str(self.file), "kind": "OBSERVED"}]
        self.payload = dict(lock_at=LOCK, run_at=BEFORE, inputs={"fixture": "test"},
                            config={"rules": {}}, decision={"prediction_status": "SHADOW", "module": "4-4-2"},
                            source_snapshots=self.sources)

    def test_roundtrip_hashes_but_not_replay(self):
        r = freeze_prelock(self.root / "frozen", **self.payload)
        self.assertEqual(r["status"], "SHADOW_FROZEN")
        v = verify_archive(self.root / "frozen")
        self.assertEqual(v["integrity"], "PASS")
        self.assertFalse(v["replay_executed"])

    def test_no_overwrite(self):
        freeze_prelock(self.root / "frozen", **self.payload)
        with self.assertRaises(FileExistsError):
            freeze_prelock(self.root / "frozen", **self.payload)

    def test_no_postlock_run(self):
        self.payload["run_at"] = "2026-10-23T20:46:00+02:00"
        with self.assertRaises(ValueError):
            freeze_prelock(self.root / "frozen", **self.payload)

    def test_no_postlock_source(self):
        self.sources[0]["observed_at"] = "2026-10-23T20:46:00+02:00"
        with self.assertRaises(ValueError):
            freeze_prelock(self.root / "frozen", **self.payload)

    def test_no_reconstruction(self):
        self.sources[0]["kind"] = "RECONSTRUCTED"
        with self.assertRaises(ValueError):
            freeze_prelock(self.root / "frozen", **self.payload)

    def test_source_hash_mismatch(self):
        self.sources[0]["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            freeze_prelock(self.root / "frozen", **self.payload)

    def test_source_provenance_required(self):
        self.sources.clear()
        with self.assertRaises(ValueError):
            freeze_prelock(self.root / "frozen", **self.payload)

    def test_timezone_required(self):
        self.payload["lock_at"] = "2026-10-23T20:45:00"
        with self.assertRaises(ValueError):
            freeze_prelock(self.root / "frozen", **self.payload)

    def test_tamper_detection(self):
        freeze_prelock(self.root / "frozen", **self.payload)
        (self.root / "frozen" / "decision.json").write_text("{}")
        self.assertEqual(verify_archive(self.root / "frozen")["integrity"], "FAIL")

    def test_incomplete_freeze_rejected(self):
        freeze_prelock(self.root / "frozen", **self.payload)
        (self.root / "frozen" / "FINALIZED.sha256").unlink()
        self.assertEqual(verify_archive(self.root / "frozen")["integrity"], "FAIL")

    def test_deterministic_manifest(self):
        a = freeze_prelock(self.root / "a", **self.payload)
        b = freeze_prelock(self.root / "b", **self.payload)
        self.assertEqual(a["manifest_sha256"], b["manifest_sha256"])

    def test_no_gold_with_missing_evidence(self):
        verdict = promotion_gate({}, {"rules": {}}, {})
        self.assertEqual(verdict["status"], "SHADOW_BLOCKED")
        self.assertFalse(verdict["gold_lock"])
        self.assertIn("GATES_OPEN", verdict["blockers"])

    def test_eligibility_not_automatic_gold(self):
        gates = {g: {"status": "VERIFICATO", "evidence_sha256": "a" * 64} for g in GATES}
        config = {"rules": {k: {"status": "CERTIFICATA"} for k in REQUIRED_RULES}}
        b = dict(preregistered=True, rolling_origin=True, out_of_sample=True, observed_official=True,
                 baseline_comparison_pass=True, independent_auditor_pass=True, has_reconstructed=False,
                 n_real_events=50, preregistered_min_events=30, evidence_sha256="b" * 64)
        v = promotion_gate(gates, config, b)
        self.assertEqual(v["status"], "GOLD_ELIGIBLE_FOR_CTO_REVIEW")
        self.assertFalse(v["gold_lock"])
        b["observed_official"] = False
        self.assertIn("STAT_NOT_VALIDATED", promotion_gate(gates, config, b)["blockers"])

if __name__ == "__main__":
    unittest.main()
