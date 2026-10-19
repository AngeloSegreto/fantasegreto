"""G14/G15 backtest safety and paired-statistics tests; only synthetic fixtures."""
import copy
import unittest
from temporal_backtest import evaluate

PRE = {"registered_at": "2026-10-18T18:00:00+02:00",
       "metric": "brier_multiclass_0_2", "alpha": 0.05, "practical_gain": 0.01,
       "bootstrap_reps": 400, "seed": 311, "min_events": 4, "min_matchdays": 2,
       "cto_ratified": False, "independent_auditor_pass": False, "snapshot_hashes_verified": False}


def fixture(day, idx):
    date = f"2026-10-{22+day:02d}"
    return {"fixture_id": "F" + str(day) + "-" + str(idx), "matchday": day,
            "lock_at": date + "T20:45:00+02:00", "predicted_at": date + "T20:00:00+02:00",
            "observed_at": f"2026-10-{23+day:02d}T12:00:00+02:00",
            "source_kind": "SYNTHETIC", "outcome": "V",
            "prelock_archive_sha256": "a" * 64, "official_result_sha256": "b" * 64,
            "training_through_matchday": day - 1,
            "models": {"candidate": {"V": 0.90, "N": 0.05, "S": 0.05},
                       "B0": {"V": 0.35, "N": 0.25, "S": 0.40},
                       "B1": {"V": 0.40, "N": 0.30, "S": 0.30}}}


class TemporalSafety(unittest.TestCase):
    def setUp(self):
        self.events = [fixture(d, i) for d in (1, 2) for i in (1, 2)]
    def test_missing_evidence(self):
        self.assertEqual(evaluate([], PRE)["status"], "BLOCKED_NO_REAL_OBSERVATIONS")
    def test_reconstructed_or_synthetic_fails(self):
        with self.assertRaises(ValueError):
            evaluate(self.events, PRE)
    def test_paired_scoring_but_never_gold(self):
        r = evaluate(self.events, PRE, synthetic_tests=True)
        self.assertTrue(r["candidate_statistically_promising"])
        self.assertFalse(r["gold_lock"])
        self.assertEqual(r["G14"], "DA_VERIFICARE")
        self.assertEqual(r["G15"], "DA_VERIFICARE")
    def test_incomplete_sample(self):
        p = {**PRE, "min_events": 8}
        self.assertEqual(evaluate(self.events, p, synthetic_tests=True)["status"],
                         "BLOCKED_INSUFFICIENT_SAMPLE")
    def test_training_future_leak(self):
        self.events[0]["training_through_matchday"] = 1
        with self.assertRaisesRegex(ValueError, "leakage"):
            evaluate(self.events, PRE, synthetic_tests=True)
    def test_prediction_after_lock(self):
        self.events[0]["predicted_at"] = "2026-10-23T21:00:00+02:00"
        with self.assertRaisesRegex(ValueError, "temporal"):
            evaluate(self.events, PRE, synthetic_tests=True)
    def test_duplicate_fixture(self):
        self.events.append(copy.deepcopy(self.events[0]))
        with self.assertRaisesRegex(ValueError, "duplicated"):
            evaluate(self.events, PRE, synthetic_tests=True)
    def test_probability_domain(self):
        self.events[0]["models"]["candidate"] = {"V": 0.9, "N": 0.9, "S": -0.8}
        with self.assertRaisesRegex(ValueError, "probability"):
            evaluate(self.events, PRE, synthetic_tests=True)
    def test_missing_source_hash(self):
        self.events[0]["official_result_sha256"] = ""
        with self.assertRaisesRegex(ValueError, "sha256"):
            evaluate(self.events, PRE, synthetic_tests=True)
    def test_pre_registration_after_predictions(self):
        p = {**PRE, "registered_at": "2026-11-01T12:00:00+01:00"}
        with self.assertRaisesRegex(ValueError, "temporal"):
            evaluate(self.events, p, synthetic_tests=True)
    def test_deterministic_bootstrap(self):
        x = evaluate(self.events, PRE, synthetic_tests=True)
        y = evaluate(self.events[::-1], PRE, synthetic_tests=True)
        self.assertEqual(x["paired"], y["paired"])

if __name__ == "__main__":
    unittest.main()
