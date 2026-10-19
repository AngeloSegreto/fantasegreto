"""SHADOW G7 official replay: synthetic tests must never certify historic outcomes."""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from g7_golden_replay import replay
from p0_core import load_config

ROOT=Path(__file__).resolve().parent
PARTIAL=json.loads((ROOT/"data"/"g7_live_partial_20261019.json").read_text(encoding="utf8"))
CFG=load_config(ROOT/"league_config.yaml")

def synthetic_final(path):
    updates={"home":{},"away":{}}
    for side in ("home","away"):
        for p in PARTIAL[side]["starters"] + PARTIAL[side]["bench"]:
            if p["status"]=="VOTED":
                updates[side][p["id"]]={"pure_vote":"6.5"}
            elif p["status"]=="PENDING_MATCH":
                updates[side][p["id"]]={"status":"DID_NOT_PLAY"}
    # Invented ONLY for synthetic software test: NOT observed scores!
    updates["home"]["4896"]={"status":"VOTED","pure_vote":"7.5","fantavote":"10.5"}
    updates["away"]["unknown-ac-simeone"]={"status":"VOTED","pure_vote":"6","fantavote":"6"}
    raw=path.read_bytes()
    return {"schema":"FS_V331_G7_OFFICIAL_RESULT_INPUT_V1",
            "matchday":7,
            "receipt":{"original_path":str(path),"sha256":sha256(raw).hexdigest(),
                       "observed_at":"2026-10-20T00:15:00+02:00",
                       "evidence_kind":"SYNTHETIC_UNIT_TEST"},
            "player_updates":updates,
            # Calculated independently by hand:
            # home 50 + Cambiaso 6 + Maldini 10.5 + mod 1 + captain 1.5 = 69
            # away 60.5 + Perrone 6 + Simeone 6 + mod 0 + captain 0 = 72.5
            "platform":{"home_total":"69","away_total":"72.5",
                        "home_goals":1,"away_goals":2}}

class G7OfficialReplayTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"test_screen.png"
        self.path.write_bytes(b"SYNTHETIC_FANTACALCIO_SCOREBOARD_TEST_NOT_REAL")
        self.fixture=synthetic_final(self.path)

    def test_live_partial_never_misrepresented_as_final(self):
        r=replay(PARTIAL,None,CFG)
        self.assertEqual(r["status"],"BLOCKED_OFFICIAL_FINAL_NOT_PROVIDED")
        self.assertFalse(r["gold_lock"])
        self.assertIn("MALDINI_FINAL_VOTE",r["missing"])

    def test_complete_synthetic_score_uses_all_rules(self):
        r=replay(PARTIAL,self.fixture,CFG)
        self.assertEqual(r["status"],"SOFTWARE_TEST_ONLY")
        self.assertEqual(r["replay"]["home"]["total"],"69.0")
        self.assertEqual(r["replay"]["away"]["total"],"72.5")
        self.assertEqual(r["replay"]["home"]["fantagoals"],1)
        self.assertEqual(r["replay"]["away"]["fantagoals"],2)
        self.assertEqual(r["replay"]["home"]["defense_modifier"],"1")
        self.assertEqual(r["replay"]["home"]["captain_factor"],"1.5")
        self.assertEqual(r["replay"]["away"]["defense_modifier"],"0")
        self.assertEqual(r["replay"]["away"]["captain_factor"],"0")
        self.assertFalse(r["gold_lock"])
        self.assertEqual(r["golden_gate_G16"],"DA_VERIFICARE")

    def test_synthetic_never_claims_official_parity(self):
        r=replay(PARTIAL,self.fixture,CFG)
        self.assertFalse(r["independent_source_transcription_verified"])
        self.assertFalse(r["prematch_holdout_eligible"])
        self.assertEqual(r["evidence_kind"],"SYNTHETIC_UNIT_TEST")

    def test_tampered_photo_rejected(self):
        self.path.write_bytes(b"CHANGED")
        r=replay(PARTIAL,self.fixture,CFG)
        self.assertIn("FINAL_RECEIPT_HASH_MISMATCH",r["missing"])

    def test_missing_receipt_rejected(self):
        x=deepcopy(self.fixture);x.pop("receipt")
        self.assertIn("MISSING_FINAL_SCREENSHOT_RECEIPT",replay(PARTIAL,x,CFG)["missing"])

    def test_unresolved_Maldini_rejected(self):
        x=deepcopy(self.fixture);x["player_updates"]["home"].pop("4896")
        r=replay(PARTIAL,x,CFG)
        self.assertIn("home:PENDING_MATCH:Maldini",r["missing"])

    def test_unresolved_Simeone_rejected(self):
        x=deepcopy(self.fixture);x["player_updates"]["away"].pop("unknown-ac-simeone")
        r=replay(PARTIAL,x,CFG)
        self.assertIn("away:PENDING_MATCH:Simeone",r["missing"])

    def test_missing_pure_vote_rejected(self):
        x=deepcopy(self.fixture);x["player_updates"]["home"]["5520"].pop("pure_vote")
        r=replay(PARTIAL,x,CFG)
        self.assertIn("home:MISSING_PURE_VOTE:Cambiaso",r["missing"])

    def test_wrong_platform_total_produces_discrepancy(self):
        x=deepcopy(self.fixture);x["platform"]["home_total"]="69.5"
        r=replay(PARTIAL,x,CFG)
        self.assertEqual(r["status"],"SOFTWARE_TEST_ONLY")
        self.assertEqual(r["discrepancies"]["home"]["delta"],"-0.5")

    def test_missing_platform_final_blocks(self):
        x=deepcopy(self.fixture);x["platform"].pop("away_total")
        self.assertIn("MISSING_PLATFORM_AWAY_TOTAL",replay(PARTIAL,x,CFG)["missing"])

    def test_invalid_goal_number_rejected(self):
        x=deepcopy(self.fixture);x["platform"]["home_goals"]=False
        with self.assertRaises(ValueError):replay(PARTIAL,x,CFG)

    def test_invalid_league_rules_not_bypassed(self):
        x=deepcopy(CFG);x["rules"]["defense_modifier"]["status"]="PROVVISORIA"
        from league_scoring_v331 import UncertifiedScoringCase
        with self.assertRaises(UncertifiedScoringCase):replay(PARTIAL,self.fixture,x)

    def test_invented_outsider_rejected(self):
        x=deepcopy(self.fixture);x["player_updates"]["home"]["madeup"]={"status":"VOTED","fantavote":"30","pure_vote":"8"}
        with self.assertRaisesRegex(ValueError,"not in original roster"):replay(PARTIAL,x,CFG)

    def test_fixture_cannot_change_formation(self):
        x=deepcopy(PARTIAL);x["home"]["module"]="3-5-2"
        with self.assertRaisesRegex(ValueError,"match its module"):replay(x,self.fixture,CFG)

    def test_original_voted_player_revised_requires_review(self):
        x=deepcopy(self.fixture);x["player_updates"]["home"]["572"]={"status":"DID_NOT_PLAY"}
        r=replay(PARTIAL,x,CFG)
        self.assertIn("PRIOR_VOTE_REVISIONS_REQUIRE_SEPARATE_APP_ATTESTATION",r["missing"])

    def test_untrusted_future_data_doesnt_pass(self):
        x=deepcopy(self.fixture);x["receipt"]["observed_at"]="2026-10-20T00:15:00"
        with self.assertRaisesRegex(ValueError,"UTC offset"):replay(PARTIAL,x,CFG)

if __name__=="__main__":
    unittest.main()
